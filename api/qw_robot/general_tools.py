"""
通用工具
    - new_req_id: 生成唯一请求id
    - get_redis_id: 获取redis id
    - send_json: 发送json数据
    - send_and_wait_response / dispatch_ws_response: WS 响应按 req_id 分发
"""

import asyncio
import uuid
import json
from configs.service_config import ConfigRedis
from redis import Redis
from typing import Literal
from random import randint
from utils.redis_link import RedisManager

r_link = RedisManager()

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
    # 业务回调带 cmd，不应当作发送应答
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
    """发送 JSON 并等待同 req_id 的应答（由主循环 dispatch）。"""
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


async def get_redis_id(
        key: str,
        id_type: Literal['thread_id', 'u_id'] = 'u_id',
        ttl: int = ConfigRedis.TIMEOUT) -> str:
    """
    获取ID
    Args:
        key: 键
        id_type: id类型 default: u_id
            - thread_id: 会话ID
            - u_id: 通用ID
        ttl: 过期时间 单位: 秒
    Returns:
        str: ID
    """
    r_client = await r_link.get_client()
    out_time = ttl + randint(1, 30)
    if await r_client.exists(key):
        await r_client.expire(key, out_time)
        return await r_client.hget(key, id_type)
    else:
        if id_type == 'thread_id':
            value = {'key': key, id_type: f"t-{new_req_id()}"}
        else:
            value = {'key': key, id_type: f"u-{new_req_id()}"}
        await r_client.hset(key, mapping=value)
        await r_client.expire(key, out_time)
        return value[id_type]


async def send_json(ws, payload: dict) -> None:
    """
    发送json数据
    Args:
        ws:  websocket连接
        payload: 发送的数据，字典类型
    Returns:
        None
    """
    await ws.send(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    import asyncio
    print(asyncio.run(get_redis_id(key="test", id_type="thread_id")))
