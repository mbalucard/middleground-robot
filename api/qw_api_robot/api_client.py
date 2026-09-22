"""
HTTP 调用 FastAPI Agent / Session
    - create_session_thread: 创建会话线程
    - stream_run_agent: 流式运行智能体（NDJSON）
    - stream_interrupts_judge: 中断恢复流式（NDJSON）
"""

from __future__ import annotations

import json
from typing import Any, AsyncIterator, Literal, Optional

import httpx

from configs.api_config import APIConfig
from utils.logger_manager import LoggerManager

logger = LoggerManager.get_logger(name="api_client")

VisionProvider = Literal["openai", "anthropic"]

DEFAULT_TIMEOUT = httpx.Timeout(connect=10.0, read=300.0, write=60.0, pool=10.0)


class ApiClientError(Exception):
    """
    API 调用业务异常
    Args:
        user_message(str): 可直接展示给用户的错误文案
        cause(Exception): 原始异常, default=None
    """

    def __init__(self, user_message: str, *, cause: Exception | None = None):
        super().__init__(user_message)
        self.user_message = user_message
        self.cause = cause


def _base_url() -> str:
    return (APIConfig.url or "").rstrip("/")


async def create_session_thread(user_id: str) -> str:
    """
    创建会话线程
    Args:
        user_id(str): 用户ID
    Returns:
        str: 新创建的 thread_id
    """
    url = f"{_base_url()}/session/session_thread/create"
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, trust_env=False) as client:
            resp = await client.post(url, json={"user_id": user_id})
            resp.raise_for_status()
            body = resp.json()
    except httpx.HTTPError as e:
        logger.error(f"创建会话线程失败: {e}")
        raise ApiClientError("服务暂时不可用，请稍后重试", cause=e) from e
    except Exception as e:
        logger.exception(f"创建会话线程异常: {e}")
        raise ApiClientError("创建会话失败，请稍后重试", cause=e) from e

    if not body.get("success"):
        msg = body.get("message") or "创建会话失败"
        raise ApiClientError(str(msg))

    thread_id = (body.get("data") or {}).get("thread_id")
    if not thread_id:
        raise ApiClientError("创建会话失败：未返回 thread_id")
    return str(thread_id)


async def stream_run_agent(
        *,
        user_id: str,
        query: str,
        thread_id: str,
        model_label: str = "deepseek",
        images: Optional[list[dict[str, Any]]] = None,
        provider: Optional[VisionProvider] = None,) -> AsyncIterator[dict[str, Any]]:
    """
    流式运行智能体，逐行产出 NDJSON 事件
    Args:
        user_id(str): 用户ID
        query(str): 查询字符串
        thread_id(str): 会话线程ID
        model_label(str): 模型标签, default="deepseek"
        images(list): 图片列表 [{data, media_type?}], default=None
        provider: 有图时必填 openai/anthropic, default=None
    Returns:
        异步迭代 NDJSON 解析后的 dict
    """
    url = f"{_base_url()}/agent/run_agent/stream"
    payload: dict[str, Any] = {
        "user_id": user_id,
        "query": query,
        "thread_id": thread_id,
        "model_label": model_label,
        "images": images or [],
    }
    if provider is not None:
        payload["provider"] = provider

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, trust_env=False) as client:
            async with client.stream("POST", url, json=payload) as resp:
                if resp.status_code >= 400:
                    text = (await resp.aread()).decode("utf-8", errors="replace")
                    logger.error(
                        f"stream_run_agent HTTP {resp.status_code}: {text[:500]}"
                    )
                    raise ApiClientError("服务暂时不可用，请稍后重试")
                async for line in resp.aiter_lines():
                    if not line or not line.strip():
                        continue
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        logger.warning(f"跳过非法 NDJSON 行: {line[:200]}")
                        continue
    except ApiClientError:
        raise
    except httpx.HTTPError as e:
        logger.error(f"流式调用失败: {e}")
        raise ApiClientError("服务暂时不可用，请稍后重试", cause=e) from e
    except Exception as e:
        logger.exception(f"流式调用异常: {e}")
        raise ApiClientError("处理失败，请稍后重试", cause=e) from e


async def stream_interrupts_judge(
        *,
        user_id: str,
        thread_id: str,
        message_id: str,
        decides: list[str],
        is_all_decides: bool = False,) -> AsyncIterator[dict[str, Any]]:
    """
    中断恢复流式运行智能体，逐行产出 NDJSON 事件
    Args:
        user_id(str): 用户ID
        thread_id(str): 会话线程ID
        message_id(str): 消息ID
        decides(list): 决策列表 approve/reject
        is_all_decides(bool): 是否全部一致决策, default=False
    Returns:
        异步迭代 NDJSON 解析后的 dict
    """
    url = f"{_base_url()}/agent/run_agent/interrupts_judge/stream"
    payload: dict[str, Any] = {
        "user_id": user_id,
        "thread_id": thread_id,
        "message_id": message_id,
        "decides": decides,
        "is_all_decides": is_all_decides,
    }

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, trust_env=False) as client:
            async with client.stream("POST", url, json=payload) as resp:
                if resp.status_code >= 400:
                    text = (await resp.aread()).decode("utf-8", errors="replace")
                    logger.error(
                        f"stream_interrupts_judge HTTP {resp.status_code}: {text[:500]}"
                    )
                    raise ApiClientError("服务暂时不可用，请稍后重试")
                async for line in resp.aiter_lines():
                    if not line or not line.strip():
                        continue
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        logger.warning(f"跳过非法 NDJSON 行: {line[:200]}")
                        continue
    except ApiClientError:
        raise
    except httpx.HTTPError as e:
        logger.error(f"中断恢复流式调用失败: {e}")
        raise ApiClientError("服务暂时不可用，请稍后重试", cause=e) from e
    except Exception as e:
        logger.exception(f"中断恢复流式调用异常: {e}")
        raise ApiClientError("处理失败，请稍后重试", cause=e) from e
