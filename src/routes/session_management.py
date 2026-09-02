"""
Session管理路由
    - read_long_term_info: 读取用户所有长期记忆信息详情
    - delete_long_term_info: 删除用户指定长期记忆信息
    - write_long_term_info: 写入用户长期记忆信息
"""
from fastapi import APIRouter, HTTPException, Request
from utils.logger_manager import LoggerManager
from utils.api_utils.data_processing import format_long_term_info_key, agent_message_to_dict
from utils.api_utils.request_models import ReadLongTermInfoRequest, LongTermInfoDetailRequest, WriteLongTermInfoRequest
from utils.api_utils.memory_service import get_memory_service, get_short_term_memory_service


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


@router.post("/delete_session/thread")
async def delete_session_thread(
    thread_id: str,
    app_request: Request):
    """
    删除会话线程
    """
    state = app_request.app.state
    checkpointer = state.checkpointer
    await checkpointer.adelete_thread(thread_id)
    return {"success": True, "message": "成功删除会话"}


@router.post("/user_session/thread_details")
async def user_session_thread_details(
    user_id: str,
    thread_id: str,
    app_request: Request):
    """
    获取用户会话详情
    """
    state = app_request.app.state
    agent_args = {
        "user_id": user_id,
        "thread_id": thread_id,
    }
    memory_service = await get_short_term_memory_service(
        state=state,
        thread_id=thread_id,
        user_id=user_id
    )
    messages = await memory_service.get_context(context_type="messages")
    message_list = []
    for item in messages:
        data_dict = agent_message_to_dict(item)
        message_list.append(data_dict)
    res_message = "成功获取用户会话详情" if message_list else "未找到用户会话详情"
    session_response = {
        "success": True,
        "agent_args": agent_args,
        "total": len(message_list),
        "data": message_list,
        "data_type": "thread_details",
        "message": res_message,
    }
    logger.info(session_response)
    return session_response

@router.post("/user_session/thread_interrupt")
async def user_session_thread_interrupt(
    user_id: str,
    thread_id: str,
    app_request: Request):
    """
    获取会话中断信息
    """
    state = app_request.app.state
    memory_service = await get_short_term_memory_service(
        state=state,
        thread_id=thread_id,
        user_id=user_id
    )
    interrupt_info = await memory_service.get_interrupt_info()
    agent_args = {
        "user_id": user_id,
        "thread_id": thread_id,
    }
    res_message = "成功获取会话中断信息" if interrupt_info else "未找到会话中断信息"
    interrupt_response = {
        "success": True,
        "agent_args": agent_args,
        "data": interrupt_info,
        "data_type": "interrupt",
        "message": res_message,
    }
    return interrupt_response