"""
Agent交互路由
"""
from fastapi import APIRouter, HTTPException, Request
from utils.logger_manager import LoggerManager

logger = LoggerManager.get_logger(name='agent_interactive')

router = APIRouter(prefix='/agent', tags=['Agent'])

@router.get("/")
async def agent_interactive():
    """ Agent交互路由,测试用 """
    return {"message": "这里是Agent交互路由"}