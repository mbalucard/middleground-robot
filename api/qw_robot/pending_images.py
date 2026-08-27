"""
纯图挂起队列（Redis Hash）
    - append_pending_image: 追加一张，最多 5 张，TTL 10 分钟
    - list_pending_images: 只读当前挂起列表
    - take_pending_images: 原子取出并清空当前挂起
"""

from __future__ import annotations

import json
import time
import uuid
from typing import Any

import redis.asyncio as redis
from redis.exceptions import ResponseError

from api.qw_robot.media_handler import ImagePayload

MAX_PENDING_IMAGES = 5
PENDING_TTL_SECONDS = 600

_APPEND_LUA = """
local n = redis.call('HLEN', KEYS[1])
if n >= tonumber(ARGV[4]) then
  return -1
end
redis.call('HSET', KEYS[1], ARGV[1], ARGV[2])
redis.call('EXPIRE', KEYS[1], tonumber(ARGV[3]))
return n + 1
"""

_TAKE_LUA = """
local raw = redis.call('HGETALL', KEYS[1])
redis.call('DEL', KEYS[1])
return raw
"""


class PendingFullError(Exception):
    """挂起队列已满。"""

    def __init__(self, count: int = MAX_PENDING_IMAGES):
        self.count = count
        super().__init__(
            f"最多同时挂起 {MAX_PENDING_IMAGES} 张图片，请先提问或等待过期"
        )
        self.user_message = str(self)


def _key(userid: str, thread_id: str) -> str:
    return f"pending_images:{userid}:{thread_id}"


def _is_wrongtype(exc: BaseException) -> bool:
    return "WRONGTYPE" in str(exc)


def _parse_payload(raw: Any) -> ImagePayload | None:
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    if not isinstance(raw, str):
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    if not data.get("media_type") or not data.get("data"):
        return None
    return {
        "media_type": str(data["media_type"]),
        "data": str(data["data"]),
    }


def _mapping_from_raw(raw: Any) -> dict[str, Any]:
    if not raw:
        return {}
    if isinstance(raw, dict):
        return {str(k): v for k, v in raw.items()}
    mapping: dict[str, Any] = {}
    seq = list(raw)
    for i in range(0, len(seq) - 1, 2):
        mapping[str(seq[i])] = seq[i + 1]
    return mapping


def _payloads_from_mapping(mapping: dict[str, Any]) -> list[ImagePayload]:
    out: list[ImagePayload] = []
    for _field, raw in sorted(mapping.items(), key=lambda kv: str(kv[0])):
        payload = _parse_payload(raw)
        if payload:
            out.append(payload)
    return out


async def _eval_script(
    redis_client: redis.Redis,
    script: str,
    key: str,
    *args: Any,
    retry_on_wrongtype: bool = False,
) -> Any:
    try:
        return await redis_client.eval(script, 1, key, *args)
    except ResponseError as e:
        if not _is_wrongtype(e):
            raise
        await redis_client.delete(key)
        if retry_on_wrongtype:
            return await redis_client.eval(script, 1, key, *args)
        return None


async def list_pending_images(
    redis_client: redis.Redis,
    userid: str,
    thread_id: str,
) -> list[ImagePayload]:
    """
    只读当前挂起图片列表，不删除。
    Args:
        redis_client: Redis连接
        userid(str): 用户ID
        thread_id(str): 会话ID
    Returns:
        按写入时间排序的挂起图片列表
    """
    key = _key(userid, thread_id)
    try:
        mapping = await redis_client.hgetall(key)
    except ResponseError as e:
        if _is_wrongtype(e):
            await redis_client.delete(key)
            return []
        raise
    return _payloads_from_mapping(_mapping_from_raw(mapping))


async def take_pending_images(
    redis_client: redis.Redis,
    userid: str,
    thread_id: str,
) -> list[ImagePayload]:
    """
    原子取出当前挂起图片并删除该 Hash。
    Args:
        redis_client: Redis连接
        userid(str): 用户ID
        thread_id(str): 会话ID
    Returns:
        按写入时间排序的挂起图片列表
    """
    key = _key(userid, thread_id)
    raw = await _eval_script(redis_client, _TAKE_LUA, key)
    return _payloads_from_mapping(_mapping_from_raw(raw))


async def append_pending_image(
    redis_client: redis.Redis,
    userid: str,
    thread_id: str,
    payload: ImagePayload | dict[str, Any],
) -> int:
    """
    追加一张挂起图并刷新 TTL。
    Args:
        redis_client: Redis连接
        userid(str): 用户ID
        thread_id(str): 会话ID
        payload: 图片 payload（media_type + data）
    Returns:
        当前挂起张数
    Raises:
        PendingFullError: 已满 5 张
    """
    key = _key(userid, thread_id)
    field = f"{time.time_ns()}:{uuid.uuid4()}"
    value = json.dumps(
        {
            "media_type": str(payload["media_type"]),
            "data": str(payload["data"]),
        },
        ensure_ascii=False,
    )
    n = await _eval_script(
        redis_client,
        _APPEND_LUA,
        key,
        field,
        value,
        PENDING_TTL_SECONDS,
        MAX_PENDING_IMAGES,
        retry_on_wrongtype=True,
    )
    count = int(n)
    if count < 0:
        raise PendingFullError(MAX_PENDING_IMAGES)
    return count
