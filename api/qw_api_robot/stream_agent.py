"""
通过 HTTP API 流式运行智能体，并转为企微展示文案
    - agent_astream: 流式产出结构化事件（text / interrupt / file）
    - format_agent_chunk: 将 API agent 消息转为展示片段
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, AsyncIterator, Optional

from api.qw_api_robot.api_client import (
    ApiClientError,
    VisionProvider,
    stream_run_agent,
)
from api.qw_api_robot.interrupt_card import parse_tools_from_interrupt
from utils.logger_manager import LoggerManager

logger = LoggerManager.get_logger(name="stream_agent")

EXPORT_TOOL_NAME = "export_erp_data_to_excel"


def _parse_tool_content(content: Any) -> dict[str, Any] | None:
    """
    将 ToolMessage content 解析为 dict
    Args:
        content: 工具返回内容（dict 或 JSON 字符串）
    Returns:
        dict 或 None
    """
    if isinstance(content, dict):
        return content
    if isinstance(content, str) and content.strip():
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, dict):
            return parsed
    return None


def _file_event_from_tool_data(data: dict[str, Any] | None) -> dict[str, Any] | None:
    """
    从导出工具成功结果构造 file 事件
    Args:
        data(dict): ToolMessage 字典
    Returns:
        kind=file 事件，或 None
    """
    if not data or not isinstance(data, dict):
        return None
    if data.get("name") != EXPORT_TOOL_NAME:
        return None
    payload = _parse_tool_content(data.get("content"))
    if not payload:
        return None
    if payload.get("status") != "success":
        return None
    file_path = str(payload.get("file_path") or "").strip()
    if not file_path:
        return None
    file_name = Path(file_path).name
    return {
        "kind": "file",
        "file_path": file_path,
        "file_name": file_name,
    }


def format_agent_chunk(data: dict[str, Any] | None) -> list[str]:
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


# 兼容旧名
_format_agent_chunk = format_agent_chunk


def _interrupt_event_from_api(event: dict[str, Any]) -> dict[str, Any]:
    """
    将 API interrupt NDJSON 转为上层事件
    Args:
        event(dict): API 流式事件
    Returns:
        kind=interrupt 的结构化事件
    """
    agent_args = event.get("agent_args") or {}
    data = event.get("data") if isinstance(event.get("data"), dict) else {}
    tools = parse_tools_from_interrupt(data)
    message_id = str(agent_args.get("message_id") or "")
    return {
        "kind": "interrupt",
        "message_id": message_id,
        "tools": tools,
        "agent_args": agent_args,
        "data": data,
    }


async def agent_astream(
        *,
        question: str,
        thread_id: str,
        user_id: str,
        model_name: str = "deepseek",
        images: Optional[list[dict[str, Any]]] = None,
        provider: Optional[VisionProvider] = None,) -> AsyncIterator[dict[str, Any]]:
    """
    流式运行智能体（HTTP API），产出结构化事件
    Args:
        question(str): 用户问题（有图时不可为空）
        thread_id(str): API 会话线程ID
        user_id(str): 用户ID
        model_name(str): 模型标签, default="deepseek"
        images(list): API 图片列表 [{data, media_type?}], default=None
        provider: 有图时必填, default=None
    Returns:
        异步迭代 {"kind":"text",...} / {"kind":"interrupt",...} / {"kind":"file",...}
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
                yield {
                    "kind": "text",
                    "text": str(event.get("message") or "请求失败，请稍后重试"),
                }
                return

            data_type = event.get("data_type")
            if data_type == "end":
                return
            if data_type == "error":
                yield {
                    "kind": "text",
                    "text": str(event.get("message") or "请求失败，请稍后重试"),
                }
                return
            if data_type == "interrupt":
                yield _interrupt_event_from_api(event)
                return
            if data_type == "tool":
                file_event = _file_event_from_tool_data(event.get("data"))
                if file_event:
                    yield file_event
                continue
            if data_type == "agent":
                for fragment in format_agent_chunk(event.get("data")):
                    yield {"kind": "text", "text": fragment}
                continue
            if data_type == "unknown":
                logger.warning(f"未知流式数据类型: {event}")
                continue
    except ApiClientError as e:
        yield {"kind": "text", "text": e.user_message}
