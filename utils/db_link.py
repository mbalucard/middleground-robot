"""
数据库连接
"""
from configs.service_config import DatabaseConfig

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from contextlib import asynccontextmanager


class PostgresServer:
    def __init__(self):
        self.engine = create_async_engine(DatabaseConfig.DB_URI, echo=False)
        self.AsyncSessionLocal = async_sessionmaker(
            self.engine, expire_on_commit=False
        )

    @asynccontextmanager
    async def get_db_session(self):
        async with self.AsyncSessionLocal() as db:
            try:
                yield db
            except Exception:
                await db.rollback()
                raise

    async def close(self):
        """进程/应用退出时调用，释放连接池"""
        await self.engine.dispose()

    def get_engine(self):
        """获取数据库引擎"""
        return self.engine

    
