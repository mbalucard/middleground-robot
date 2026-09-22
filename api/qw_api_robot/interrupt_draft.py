"""
企微 interrupt 审批草稿（挂在 qw_api_thread Hash）
    - get_draft / set_draft / clear_draft: 读写 interrupt_draft 字段
    - apply_button_decision: 补齐 decides 并判定 is_all_decides
    - is_draft_expired / mark_event_seen: 过期与短时幂等
"""

from __future__ import annotations

import json
import time
from typing import Any, Literal, Optional

from utils.logger_manager import LoggerManager
from utils.redis_link import RedisManager

logger = LoggerManager.get_logger(name="interrupt_draft")
r_link = RedisManager()

DRAFT_FIELD = "interrupt_draft"
DRAFT_EXPIRE_SECONDS = 600

ButtonKey = Literal[
    "irq_approve",
    "irq_reject",
    "irq_approve_all",
    "irq_reject_all",
]

Decision = Literal["approve", "reject"]


def _redis_key(userid: str) -> str:
    return f"qw_api_thread:{userid}"


def now_ts() -> int:
    """
    当前 Unix 秒级时间戳
    Returns:
        int
    """
    return int(time.time())


def is_draft_expired(draft: dict[str, Any] | None) -> bool:
    """
    草稿是否已逻辑过期
    Args:
        draft(dict): interrupt_draft, default=None
    Returns:
        bool
    """
    if not draft:
        return True
    expires_at = draft.get("expires_at")
    if expires_at is None:
        return True
    try:
        return now_ts() > int(expires_at)
    except (TypeError, ValueError):
        return True


def build_draft(
    *,
    message_id: str,
    tools: list[dict[str, Any]],
    task_id: str,
) -> dict[str, Any]:
    """
    构造新的审批草稿
    Args:
        message_id(str): API message_id
        tools(list): [{name, args?, description?}, ...]
        task_id(str): 首卡 task_id
    Returns:
        draft 字典
    """
    n = len(tools)
    return {
        "message_id": message_id,
        "tools": tools,
        "decides": [None] * n,
        "index": 0,
        "status": "pending",
        "current_task_id": task_id,
        "card_task_ids": [task_id],
        "expires_at": now_ts() + DRAFT_EXPIRE_SECONDS,
        "seen_events": [],
    }


async def get_draft(userid: str) -> Optional[dict[str, Any]]:
    """
    读取 interrupt_draft
    Args:
        userid(str): 企微 userid
    Returns:
        draft 或 None
    """
    r_client = await r_link.get_client()
    raw = await r_client.hget(_redis_key(userid), DRAFT_FIELD)
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        logger.warning(f"interrupt_draft JSON 无效 userid={userid}")
        return None
    if not isinstance(data, dict):
        return None
    return data


async def set_draft(userid: str, draft: dict[str, Any]) -> None:
    """
    写入 interrupt_draft（不改 thread_id）
    Args:
        userid(str): 企微 userid
        draft(dict): 草稿
    """
    r_client = await r_link.get_client()
    await r_client.hset(
        _redis_key(userid),
        DRAFT_FIELD,
        json.dumps(draft, ensure_ascii=False),
    )


async def clear_draft(userid: str) -> None:
    """
    仅删除 interrupt_draft 字段（禁止 DEL 整个 key）
    Args:
        userid(str): 企微 userid
    """
    r_client = await r_link.get_client()
    await r_client.hdel(_redis_key(userid), DRAFT_FIELD)


def mark_event_seen(draft: dict[str, Any], event_token: str) -> bool:
    """
    短时幂等：若已见过则返回 False，否则记入并返回 True
    Args:
        draft(dict): 草稿（原地修改）
        event_token(str): 如 task_id+event_key 或 msgid
    Returns:
        True 表示首次见到，应继续处理
    """
    seen = draft.get("seen_events")
    if not isinstance(seen, list):
        seen = []
        draft["seen_events"] = seen
    if event_token in seen:
        return False
    seen.append(event_token)
    # 控制长度，避免无限增长
    if len(seen) > 32:
        draft["seen_events"] = seen[-32:]
    return True


def apply_button_decision(
    draft: dict[str, Any],
    event_key: str,
) -> tuple[dict[str, Any], bool, bool]:
    """
    按按钮补齐 decides
    Args:
        draft(dict): 草稿（会复制后修改）
        event_key(str): irq_approve / irq_reject / irq_approve_all / irq_reject_all
    Returns:
        (新草稿, 是否已全部决策, is_all_decides)
    """
    out = json.loads(json.dumps(draft))  # 深拷贝
    tools = out.get("tools") or []
    decides: list[Any] = list(out.get("decides") or [None] * len(tools))
    if len(decides) < len(tools):
        decides.extend([None] * (len(tools) - len(decides)))
    index = int(out.get("index") or 0)
    n = len(tools)
    is_all_decides = False

    if event_key == "irq_approve_all":
        fill: Decision = "approve"
        if index == 0:
            decides = [fill] * n
            is_all_decides = True
        else:
            for i in range(index, n):
                decides[i] = fill
            is_all_decides = False
        out["decides"] = decides
        out["index"] = n
        out["status"] = "completed"
        return out, True, is_all_decides

    if event_key == "irq_reject_all":
        fill = "reject"
        if index == 0:
            decides = [fill] * n
            is_all_decides = True
        else:
            for i in range(index, n):
                decides[i] = fill
            is_all_decides = False
        out["decides"] = decides
        out["index"] = n
        out["status"] = "completed"
        return out, True, is_all_decides

    decision: Decision
    if event_key == "irq_approve":
        decision = "approve"
    elif event_key == "irq_reject":
        decision = "reject"
    else:
        raise ValueError(f"未知 event_key: {event_key}")

    if index < 0 or index >= n:
        out["decides"] = decides
        out["status"] = "completed"
        return out, True, False

    decides[index] = decision
    index += 1
    out["decides"] = decides
    out["index"] = index
    done = index >= n or all(d is not None for d in decides)
    if done:
        out["status"] = "completed"
        out["index"] = n
    return out, done, False


def fill_all_reject(draft: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """
    审批中发消息：剩余未决全部 reject
    Args:
        draft(dict): 草稿
    Returns:
        (新草稿, is_all_decides) — 若原本无一决策且一次填满则为 True
    """
    out = json.loads(json.dumps(draft))
    tools = out.get("tools") or []
    decides: list[Any] = list(out.get("decides") or [None] * len(tools))
    if len(decides) < len(tools):
        decides.extend([None] * (len(tools) - len(decides)))
    had_any = any(d is not None for d in decides)
    for i in range(len(decides)):
        if decides[i] is None:
            decides[i] = "reject"
    out["decides"] = decides
    out["index"] = len(tools)
    out["status"] = "cancelled"
    is_all = (not had_any) and len(tools) > 0
    return out, is_all


def decides_for_api(draft: dict[str, Any], is_all_decides: bool) -> list[str]:
    """
    组装提交给 interrupts_judge 的 decides
    Args:
        draft(dict): 草稿
        is_all_decides(bool): 是否全部一致决策
    Returns:
        decides 列表
    """
    decides = [d for d in (draft.get("decides") or []) if d in ("approve", "reject")]
    if is_all_decides:
        if not decides:
            return ["reject"]
        return [str(decides[0])]
    return [str(d) for d in decides]


def current_tool_name(draft: dict[str, Any]) -> str:
    """
    当前待审工具名
    Args:
        draft(dict): 草稿
    Returns:
        工具名
    """
    tools = draft.get("tools") or []
    index = int(draft.get("index") or 0)
    if 0 <= index < len(tools):
        name = (tools[index] or {}).get("name")
        if name:
            return str(name)
    return "工具"
