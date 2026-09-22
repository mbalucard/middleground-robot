"""
企微 interrupt 审批卡片结构
    - make_task_id: 生成卡片 task_id
    - build_review_card: 审批按钮卡
    - build_result_card: 点击后/取消后结果卡
    - parse_tools_from_interrupt: 从 API interrupt data 解析 tools
"""

from __future__ import annotations

import uuid
from typing import Any


def make_task_id(message_id: str, index: int) -> str:
    """
    生成卡片 task_id（字母数字与 _-@）
    Args:
        message_id(str): API message_id
        index(int): 工具序号
    Returns:
        task_id
    """
    mid = "".join(c if c.isalnum() or c in "_-@" else "_" for c in (message_id or "m"))
    mid = mid[:24] or "m"
    return f"irq_{mid}_{index}_{uuid.uuid4().hex[:8]}"


def parse_tools_from_interrupt(data: dict[str, Any] | None) -> list[dict[str, Any]]:
    """
    从 interrupt 事件 data 解析待审工具列表
    Args:
        data(dict): API data 字段（含 content.action_requests）
    Returns:
        [{name, args, description}, ...]
    """
    if not data:
        return []
    content = data.get("content")
    if isinstance(content, dict):
        action_requests = content.get("action_requests") or []
    else:
        action_requests = data.get("action_requests") or []
    tools: list[dict[str, Any]] = []
    for item in action_requests:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or "unknown_tool"
        tools.append(
            {
                "name": str(name),
                "args": item.get("args"),
                "description": item.get("description") or "",
            }
        )
    return tools


def build_review_card(
    *,
    tool_name: str,
    task_id: str,
    show_all_buttons: bool,
    index: int = 0,
    total: int = 1,
) -> dict[str, Any]:
    """
    构造按钮交互审批卡
    Args:
        tool_name(str): 工具名
        task_id(str): 卡片 task_id
        show_all_buttons(bool): 是否展示全部同意/拒绝
        index(int): 当前序号（0-based）, default=0
        total(int): 工具总数, default=1
    Returns:
        template_card
    """
    title = f"{tool_name}需要您审核"
    if total > 1:
        desc = f"第 {index + 1}/{total} 个工具"
    else:
        desc = "工具调用需人工确认后继续"

    buttons: list[dict[str, Any]] = [
        {"text": "同意", "style": 1, "key": "irq_approve"},
        {"text": "拒绝", "style": 2, "key": "irq_reject"},
    ]
    if show_all_buttons:
        buttons.extend(
            [
                {"text": "全部同意", "style": 1, "key": "irq_approve_all"},
                {"text": "全部拒绝", "style": 2, "key": "irq_reject_all"},
            ]
        )

    return {
        "card_type": "button_interaction",
        "source": {"desc": "工具审批", "desc_color": 0},
        "main_title": {"title": title, "desc": desc},
        "sub_title_text": "请选择同意或拒绝；超时请重新发起请求",
        "button_list": buttons,
        "task_id": task_id,
    }


def build_result_card(
    *,
    task_id: str,
    title: str,
    desc: str,
) -> dict[str, Any]:
    """
    构造审批结果/已取消卡片（按钮置灰）
    Args:
        task_id(str): 原 task_id（须与回调一致）
        title(str): 主标题
        desc(str): 说明
    Returns:
        template_card
    """
    return {
        "card_type": "button_interaction",
        "main_title": {"title": title, "desc": desc},
        "sub_title_text": desc,
        "button_list": [
            {"text": "同意", "style": 3, "key": "irq_approve"},
            {"text": "拒绝", "style": 3, "key": "irq_reject"},
        ],
        "task_id": task_id,
    }
