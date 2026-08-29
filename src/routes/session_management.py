"""
Session管理路由
"""
from fastapi import APIRouter, HTTPException, Request
from utils.logger_manager import LoggerManager

logger = LoggerManager.get_logger(name='session_management')

router = APIRouter(prefix='/session', tags=['Session'])

@router.get("/")
async def session_management():
    """
    Session管理路由,测试用
    """
    return {"message": "这里是Session管理路由"}