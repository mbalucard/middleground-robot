"""
Session管理路由
"""
from fastapi import APIRouter, HTTPException, Request
from utils.logger_manager import LoggerManager
from utils.api_utils.data_processing import format_long_term_info_key
from utils.api_utils.request_models import ReadLongTermInfoRequest, LongTermInfoDetailRequest, WriteLongTermInfoRequest

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
async def read_long_term_info(
    request: ReadLongTermInfoRequest,
    app_request: Request):
    """
    读取用户所有长期记忆信息详情
    """
    user_id = request.user_id
    state = app_request.app.state
    memory_service = get_memory_service(state)
    memories = await memory_service.read_long_term_info(user_id)
    store_list = []
    for item in memories:
        store_dict = {}
        store_dict['user_id'] = user_id
        store_dict['key'] = item.key
        store_dict['content'] = item.value.get('content', '')
        store_dict['created_at'] = item.value.get('created_at', '')
        store_dict['modified_at'] = item.value.get('modified_at', '')
        store_dict['encoding'] = item.value.get('encoding', '')
        store_list.append(store_dict)
    memories_response = {
        "success": True,
        "user_id": user_id,
        "data": store_list,
        "data_type": "long_term_info",
        "total": len(store_list),
        "message": "成功获取用户长期记忆" if store_list else "未找到用户长期记忆",
    }
    return memories_response


@router.post("/delete_long_term/info")
async def delete_long_term_info(
    request: LongTermInfoDetailRequest,
    app_request: Request):
    """
    删除用户指定长期记忆信息
    """
    key = format_long_term_info_key(request.key)
    user_id = request.user_id
    state = app_request.app.state
    memory_service = get_memory_service(state)
    delete_result = await memory_service.delete_long_term_info(user_id, key)
    return delete_result
    

@router.post("/write_long_term/info")
async def write_long_term_info(
    request: WriteLongTermInfoRequest,
    app_request: Request):
    """
    写入用户长期记忆信息
    """
    user_id = request.user_id
    key = format_long_term_info_key(request.key)
    content = request.content
    state = app_request.app.state
    memory_service = get_memory_service(state)
    write_result = await memory_service.write_long_term_info(user_id, key, content)
    return write_result