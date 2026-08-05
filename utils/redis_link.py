"""
Redis连接管理
"""
import redis.asyncio as redis

from configs.service_config import  ConfigRedis
from utils.logger_manager import LoggerManager

logger = LoggerManager.get_logger(name=__name__)


class RedisManager:
    """
    定义Redis会话管理器
    """

    def __init__(self):
        self.redis_client = redis.Redis(host=ConfigRedis.HOST, port=ConfigRedis.PORT, db=ConfigRedis.DB, password=ConfigRedis.PASSWORD, decode_responses=True)
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