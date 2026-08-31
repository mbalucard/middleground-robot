"""
Session管理路由
"""
from fastapi import APIRouter, HTTPException, Request
from utils.logger_manager import LoggerManager

from utils.api_utils.request_models import LongTermInfoRequest

from utils.api_utils.memory_service import get_memory_service

logger = LoggerManager.get_logger(name='session_management')

router = APIRouter(prefix='/session', tags=['Session'])

@router.get("/")
async def session_management():
    """
    Session管理路由,测试用
    """
    return {"message": "这里是Session管理路由"}


@router.post("/read_long_term/info")
async def get_long_term_info(request: LongTermInfoRequest, app_request: Request):
    """
    读取长期记忆信息
    """
    user_id = request.user_id
    state = app_request.app.state
    memory_service = get_memory_service(state)
    long_term_info = await memory_service.read_long_term_info(user_id)
    return long_term_info