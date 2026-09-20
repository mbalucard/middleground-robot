"""
通过 HTTP API 流式运行智能体，并转为企微展示文案
    - agent_astream: 流式产出文本片段（回答/思考/工具提示/中断）
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Optional

from api.qw_api_robot.api_client import (
    ApiClientError,
    VisionProvider,
    stream_run_agent,
)
from utils.logger_manager import LoggerManager

logger = LoggerManager.get_logger(name="qw_api_stream_agent")

INTERRUPT_REPLY = "当前操作已中断，中断逻辑还未完成。"


def _format_agent_chunk(data: dict[str, Any] | None) -> list[str]:
    """
    将 API agent 消息转为企微展示片段
    Args:
        data(dict): agent_message_to_dict 结果
    Returns:
        文本片段列表
    """
    if not data:
        return []
    out: list[str] = []
    content = data.get("content")
    tool_calls = data.get("tool_calls") or []

    if isinstance(content, str) and content:
        if content.startswith("thinking:"):
            out.append(f"思考中：{content[len('thinking:'):].strip()}")
        else:
            out.append(f"回答：{content}")
    elif isinstance(content, list):
        texts = [
            b.get("text")
            for b in content
            if isinstance(b, dict) and b.get("type") == "text" and b.get("text")
        ]
        thinkings = [
            b.get("thinking")
            for b in content
            if isinstance(b, dict) and b.get("type") == "thinking" and b.get("thinking")
        ]
        if texts:
            for t in texts:
                out.append(f"回答：{t}")
        elif thinkings:
            for t in thinkings:
                out.append(f"思考中：{t}")

    if (not content) and tool_calls:
        for tool_call in tool_calls:
            if not isinstance(tool_call, dict):
                continue
            name = tool_call.get("name")
            args = tool_call.get("args")
            out.append(f"使用工具：{name} - 参数：{args}")
    return out


async def agent_astream(
        *,
        question: str,
        thread_id: str,
        user_id: str,
        model_name: str = "deepseek",
        images: Optional[list[dict[str, Any]]] = None,
        provider: Optional[VisionProvider] = None,) -> AsyncIterator[str]:
    """
    流式运行智能体（HTTP API），产出企微展示文案
    Args:
        question(str): 用户问题（有图时不可为空）
        thread_id(str): API 会话线程ID
        user_id(str): 用户ID
        model_name(str): 模型标签, default="deepseek"
        images(list): API 图片列表 [{data, media_type?}], default=None
        provider: 有图时必填, default=None
    Returns:
        异步迭代文本片段
    """
    image_list = list(images or [])
    try:
        async for event in stream_run_agent(
            user_id=user_id,
            query=question,
            thread_id=thread_id,
            model_label=model_name,
            images=image_list,
            provider=provider,
        ):
            if not event.get("success", True):
                yield str(event.get("message") or "请求失败，请稍后重试")
                return

            data_type = event.get("data_type")
            if data_type == "end":
                return
            if data_type == "error":
                yield str(event.get("message") or "请求失败，请稍后重试")
                return
            if data_type == "interrupt":
                yield INTERRUPT_REPLY
                return
            if data_type == "tool":
                continue
            if data_type == "agent":
                for fragment in _format_agent_chunk(event.get("data")):
                    yield fragment
                continue
            if data_type == "unknown":
                logger.warning(f"未知流式数据类型: {event}")
                continue
    except ApiClientError as e:
        yield e.user_message
