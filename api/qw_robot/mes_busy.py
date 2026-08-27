"""
单聊消息忙锁（Redis String）
    - try_acquire_busy: 尝试占锁，成功返回 token
    - release_busy: 校验 token 后释放锁
"""

from __future__ import annotations

import redis.asyncio as redis

from api.qw_robot.general_tools import new_req_id

BUSY_TTL_SECONDS = 300
BUSY_REPLY = "🕐 任务进行中，请等待完成后再尝试......"

_RELEASE_LUA = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
  return redis.call('DEL', KEYS[1])
end
return 0
"""


def _key(userid: str, thread_id: str) -> str:
    return f"mes_busy:{userid}:{thread_id}"


async def try_acquire_busy(
    redis_client: redis.Redis,
    userid: str,
    thread_id: str,
) -> str | None:
    """
    尝试占用消息忙锁
    Args:
        redis_client: Redis连接
        userid(str): 用户ID
        thread_id(str): 会话ID
    Returns:
        成功时返回 token；已有占用时返回 None
    """
    token = new_req_id()
    key = _key(userid, thread_id)
    ok = await redis_client.set(
        key, token, nx=True, ex=BUSY_TTL_SECONDS
    )
    if ok:
        return token
    return None


async def release_busy(
    redis_client: redis.Redis,
    userid: str,
    thread_id: str,
    token: str,
) -> bool:
    """
    释放消息忙锁（仅持有者可删）
    Args:
        redis_client: Redis连接
        userid(str): 用户ID
        thread_id(str): 会话ID
        token(str): 抢锁时返回的 token
    Returns:
        是否成功删除
    """
    key = _key(userid, thread_id)
    deleted = await redis_client.eval(_RELEASE_LUA, 1, key, token)
    return int(deleted or 0) > 0
