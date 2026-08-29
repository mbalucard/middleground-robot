"""
FastAPI 主函数
"""
from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn

from robot.agents.main_agent import build_agent
from robot.tools.memory_device import postgres_resources
from utils.redis_link import RedisManager

from src.routes.agent_interactive import router as agent_interactive_router
from src.routes.session_management import router as session_management_router
from utils.logger_manager import LoggerManager

logger = LoggerManager.get_logger(name='fastapi_main')


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 生命周期管理
    """
    redis_manager = None
    try:
        redis_manager = RedisManager()
        redis_client = await redis_manager.get_client()
        app.state.redis_client = redis_client
        logger.info("FastAPI Redis 初始化完成")

        async with postgres_resources() as pg:
            app.state.store = pg.store
            app.state.checkpointer = pg.checkpointer

            agent = await build_agent(checkpointer=app.state.checkpointer, store=app.state.store)
            app.state.agent = agent

            logger.info("FastAPI Agent 初始化完成")
            logger.info("服务完成初始化，并启动服务")
            yield
    except Exception as e:
        logger.error(f"FastAPI 生命周期管理错误: {e}")
        raise RuntimeError(f"服务初始化失败: {str(e)}") from e
    finally:
        if redis_manager is not None:
            await redis_manager.close()
        logger.info("关闭服务并完成资源清理")


app = FastAPI(
    title="Robot API",
    description="基于DeepAgents的机器人API",
    lifespan=lifespan,
    version="0.1.0",
)

app.include_router(agent_interactive_router)
app.include_router(session_management_router)


@app.get("/")
def read_root():
    return {"message": "我是Dawn机器人根目录!"}


if __name__ == "__main__":
    uvicorn.run(
        "src.fastapi_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug"
    )
