"""
Redis连接管理
    - RedisManager: Redis会话管理器
"""
import redis.asyncio as redis

from configs.service_config import ConfigRedis
from utils.logger_manager import LoggerManager

logger = LoggerManager.get_logger(name=__name__)


class RedisManager:
    """Redis管理器"""

    def __init__(
        self,
        redis_db: int = ConfigRedis.DB,
        redis_host: str = ConfigRedis.HOST,
        redis_port: int = ConfigRedis.PORT,
        redis_password: str = ConfigRedis.PASSWORD,
    ):
        self.redis_client = redis.Redis(
            host=redis_host, port=redis_port, db=redis_db, password=redis_password, decode_responses=True)
        self.session_timeout = 60

    async def close(self):
        """
        关闭Redis连接
        """
        await self.redis_client.close()

    async def get_client(self):
        """
        获取Redis连接
        """
        return self.redis_client
