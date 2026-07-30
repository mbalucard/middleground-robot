"""
记忆器，用来存储模型长短期记忆
    - PostgresResources 用来存储 Postgres 连接池、检查点、存储
    - postgres_resources 用来创建 PostgresResources 实例
"""
from __future__ import annotations

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres import AsyncPostgresStore
from psycopg_pool import AsyncConnectionPool
from dataclasses import dataclass
from contextlib import asynccontextmanager
from typing import AsyncIterator

from configs.service_config import ConfigPostgres

@dataclass
class PostgresResources:
    """Postgres资源"""
    pool: AsyncConnectionPool  # Postgres连接池
    checkpointer: AsyncPostgresSaver  # Postgres检查点
    store: AsyncPostgresStore  # Postgres存储


@asynccontextmanager
async def postgres_resources() -> AsyncIterator[PostgresResources]:
    """进程级：进入时 open + setup，退出时 close。"""
    pool = AsyncConnectionPool(
        ConfigPostgres.DB_URI,
        min_size=ConfigPostgres.MIN_SIZE,
        max_size=ConfigPostgres.MAX_SIZE,
        kwargs={"autocommit": True, "prepare_threshold": 0},
        open=False,
    )
    await pool.open()
    try:
        checkpointer = AsyncPostgresSaver(pool)
        store = AsyncPostgresStore(pool)
        await checkpointer.setup()
        await store.setup()
        yield PostgresResources(pool=pool, checkpointer=checkpointer, store=store)
    finally:
        await pool.close()
