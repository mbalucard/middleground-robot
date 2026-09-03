"""
Redis会话管理工具
"""


from utils.redis_link import RedisManager
from utils.logger_manager import LoggerManager

logger = LoggerManager.get_logger(name=__name__)

class SessionRedis(RedisManager):
    """
    Redis会话管理工具
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def get_session(self, user_id: str, thread_id: str) -> dict:
        """
        获取会话信息
        Args:
            user_id: 用户ID
            thread_id: 会话ID
        Returns:
            dict: 会话信息
        """
        pass



if __name__ == "__main__":
    import asyncio
    async def main():
        session_redis = SessionRedis()
        r = await session_redis.get_client()
        await r.set("test", "test", ex=10)
        data = await r.get("test")
        print(f"data: {data}")
    asyncio.run(main())

