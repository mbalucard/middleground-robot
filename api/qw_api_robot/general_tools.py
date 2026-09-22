"""
通用工具
    - new_req_id: 生成唯一请求id
    - get_or_create_api_thread_id: Redis 缓存 API thread_id（TTL 600s）
    - send_json / send_and_wait_response / dispatch_ws_response: WS 收发
"""

import asyncio
import json
import uuid
from random import randint

from api.qw_api_robot.api_client import ApiClientError, create_session_thread
from utils.logger_manager import LoggerManager
from utils.redis_link import RedisManager

r_link = RedisManager()
logger = LoggerManager.get_logger(name="general_tools")

# 企微侧「当前会话」映射 TTL；过期后重新 create，等价于新开对话
API_THREAD_TTL_SECONDS = 600

# 长连接并发任务时，主循环统一收包，按 req_id 投递给等待方
_pending_responses: dict[str, asyncio.Future] = {}


def dispatch_ws_response(msg: dict) -> bool:
    """
    若消息是某次发送的应答，则投递给等待中的 Future。
    Returns:
        True 表示已消费，主循环无需再处理
    """
    headers = msg.get("headers") or {}
    req_id = headers.get("req_id")
    if not req_id or "errcode" not in msg:
        return False
    if msg.get("cmd"):
        return False
    fut = _pending_responses.get(req_id)
    if fut is None or fut.done():
        return False
    fut.set_result(msg)
    return True


async def send_and_wait_response(
    ws,
    payload: dict,
    *,
    timeout: float = 60.0,
) -> dict:
    """
    发送 JSON 并等待同 req_id 的应答（由主循环 dispatch）
    Args:
        ws: websocket连接
        payload(dict): 发送数据
        timeout(float): 超时秒数, default=60.0
    Returns:
        dict: 企微应答
    """
    req_id = (payload.get("headers") or {}).get("req_id")
    if not req_id:
        raise ValueError("payload.headers.req_id 必填")
    loop = asyncio.get_running_loop()
    fut: asyncio.Future = loop.create_future()
    _pending_responses[req_id] = fut
    try:
        await send_json(ws, payload)
        return await asyncio.wait_for(fut, timeout=timeout)
    finally:
        _pending_responses.pop(req_id, None)


def new_req_id() -> str:
    """
    生成唯一请求id，用于标识一次请求
    Returns:
        str: 唯一请求id
    """
    return str(uuid.uuid4())


def _api_thread_redis_key(userid: str) -> str:
    return f"qw_api_thread:{userid}"


async def get_or_create_api_thread_id(userid: str) -> str:
    """
    获取或创建 API 会话 thread_id（Redis 缓存，TTL 约 600s）
    Args:
        userid(str): 企微用户ID
    Returns:
        str: API thread_id
    """
    r_client = await r_link.get_client()
    key = _api_thread_redis_key(userid)
    out_time = API_THREAD_TTL_SECONDS + randint(1, 30)

    existing = await r_client.hget(key, "thread_id")
    if existing:
        await r_client.expire(key, out_time)
        return str(existing)

    try:
        thread_id = await create_session_thread(userid)
    except ApiClientError:
        raise
    except Exception as e:
        logger.exception(f"创建 API thread 失败: {e}")
        raise ApiClientError("创建会话失败，请稍后重试", cause=e) from e

    await r_client.hset(
        key,
        mapping={"user_id": userid, "thread_id": thread_id},
    )
    await r_client.expire(key, out_time)
    logger.info(f"新建 API thread: userid={userid} thread_id={thread_id}")
    return thread_id


async def send_json(ws, payload: dict) -> None:
    """
    发送json数据
    Args:
        ws: websocket连接
        payload(dict): 发送的数据
    Returns:
        None
    """
    await ws.send(json.dumps(payload, ensure_ascii=False))
