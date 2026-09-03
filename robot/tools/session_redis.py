"""
Redis会话管理工具
"""

import json
from utils.redis_link import RedisManager
from utils.logger_manager import LoggerManager

logger = LoggerManager.get_logger(name=__name__)


class SessionRedis(RedisManager):
    """
    Redis会话管理工具
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timeout = 300

    async def get_session(self, user_id: str, thread_id: str):
        """
        获取会话信息
        Args:
            user_id: 用户ID
            thread_id: 会话ID
        Returns:
            dict: 会话信息
        """
        key = f"session:{user_id}-{thread_id}"
        data = await self.redis_client.get(key)
        if data:
            return json.loads(data)
        else:
            return None

    async def set_session(self, user_id: str, thread_id: str, data: dict):
        """
        设置会话信息
        Args:
            user_id: 用户ID
            thread_id: 会话ID
            data: 会话信息
        Returns:
            bool: 是否设置成功
        """
        key = f"session:{user_id}-{thread_id}"
        await self.redis_client.set(key, value=json.dumps(data), ex=self.timeout)
        return True

    async def delete_session(self, user_id: str, thread_id: str):
        """
        删除会话信息
        Args:
            user_id: 用户ID
            thread_id: 会话ID
        Returns:
            bool: 是否删除成功
        """
        key = f"session:{user_id}-{thread_id}"
        await self.redis_client.delete(key)
        return True

if __name__ == "__main__":
    import asyncio

    async def main():
        session_redis = SessionRedis()
        data = await session_redis.get_session(user_id="user01", thread_id="user01-17")
        print(f"data: {data}")
    asyncio.run(main())
