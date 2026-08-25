"""
纯图挂起队列（Redis）
    - append_pending_image: 追加一张，最多 5 张，TTL 10 分钟
    - list_pending_images: 读取当前挂起列表
    - clear_pending_images: 清空
"""

from __future__ import annotations

import json
from typing import Any

import redis.asyncio as redis

from api.qw_robot.media_handler import ImagePayload

MAX_PENDING_IMAGES = 5
PENDING_TTL_SECONDS = 600


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


async def list_pending_images(
    redis_client: redis.Redis,
    userid: str,
    thread_id: str,
) -> list[ImagePayload]:
    """读取挂起图片列表；不存在或无效则返回空列表。"""
    raw = await redis_client.get(_key(userid, thread_id))
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    out: list[ImagePayload] = []
    for item in data:
        if (
            isinstance(item, dict)
            and item.get("media_type")
            and item.get("data")
        ):
            out.append(
                {
                    "media_type": str(item["media_type"]),
                    "data": str(item["data"]),
                }
            )
    return out


async def append_pending_image(
    redis_client: redis.Redis,
    userid: str,
    thread_id: str,
    payload: ImagePayload | dict[str, Any],
) -> int:
    """
    追加一张挂起图并刷新 TTL。
    Returns:
        当前挂起张数
    Raises:
        PendingFullError: 已满 5 张
    """
    items = await list_pending_images(redis_client, userid, thread_id)
    if len(items) >= MAX_PENDING_IMAGES:
        raise PendingFullError(len(items))
    items.append(
        {
            "media_type": str(payload["media_type"]),
            "data": str(payload["data"]),
        }
    )
    key = _key(userid, thread_id)
    await redis_client.set(
        key,
        json.dumps(items, ensure_ascii=False),
        ex=PENDING_TTL_SECONDS,
    )
    return len(items)


async def clear_pending_images(
    redis_client: redis.Redis,
    userid: str,
    thread_id: str,
) -> None:
    """清空挂起队列。"""
    await redis_client.delete(_key(userid, thread_id))
