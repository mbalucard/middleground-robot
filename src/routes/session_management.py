"""
Session管理路由
    - read_long_term_info: 读取用户所有长期记忆信息详情
    - delete_long_term_info: 删除用户指定长期记忆信息
    - write_long_term_info: 写入用户长期记忆信息
    - delete_session_thread: 删除会话线程
    - create_session_thread: 创建会话线程
    - user_session_thread_details: 获取用户会话详情
    - user_session_thread_interrupt: 获取会话中断信息
"""
from fastapi import APIRouter, HTTPException, Request
from utils.logger_manager import LoggerManager
from utils.api_utils.data_processing import format_long_term_info_key, agent_message_to_dict
from utils.api_utils.request_models import LongTermInfoRequest, UserThreadRequest
from utils.api_utils.memory_service import get_memory_service, get_short_term_memory_service
from robot.tools.general_tool import new_thread_id
from utils.api_utils.db_execute import UserThreadExecute

logger = LoggerManager.get_logger(name='session_management')

router = APIRouter(prefix='/session', tags=['Session'])


@router.get("/")
async def session_management():
    """
    Session管理路由,测试用
    """
    return {"message": "这里是Session管理路由"}


@router.post("/long_term_info/read")
async def read_long_term_info(
        request: LongTermInfoRequest,
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


@router.post("/long_term_info/delete")
async def delete_long_term_info(
        request: LongTermInfoRequest,
        app_request: Request):
    """
    删除用户指定长期记忆信息
    """
    # 检查请求字段是否合法
    if not request.key:
        raise HTTPException(status_code=400, detail="删除长期记忆信息失败，key不能为空")
    user_id = request.user_id
    key = format_long_term_info_key(request.key)

    state = app_request.app.state
    memory_service = get_memory_service(state)
    delete_result = await memory_service.delete_long_term_info(user_id, key)
    return delete_result


@router.post("/long_term_info/write")
async def write_long_term_info(
        request: LongTermInfoRequest,
        app_request: Request):
    """
    写入用户长期记忆信息
    """
    # 检查请求字段是否合法
    if not request.key or not request.content:
        raise HTTPException(status_code=400, detail="写入长期记忆信息失败，key或content不能为空")
    user_id = request.user_id
    key = format_long_term_info_key(request.key)
    content = request.content

    state = app_request.app.state
    memory_service = get_memory_service(state)
    write_result = await memory_service.write_long_term_info(user_id, key, content)
    return write_result


@router.post("/session_thread/delete")
async def delete_session_thread(
        request: UserThreadRequest,
        app_request: Request):
    """
    删除会话线程
    """
    # 检查请求字段是否合法
    if not request.thread_id:
        raise HTTPException(status_code=400, detail="删除会话线程失败，thread_id不能为空")
    user_id = request.user_id
    thread_id = request.thread_id

    state = app_request.app.state
    user_thread_execute = UserThreadExecute(state.db_server)
    data = await user_thread_execute.update_user_thread(user_id=user_id, thread_id=thread_id, is_active=0, is_deleted=1)
    if data:
        checkpointer = state.checkpointer
        await checkpointer.adelete_thread(thread_id)
        return {"success": True, "message": "成功删除会话"}
    else:
        return {"success": False, "message": "删除会话线程失败"}


@router.post("/session_thread/create")
async def create_session_thread(
        request: UserThreadRequest,
        app_request: Request):
    """
    创建会话线程
    """
    user_id = request.user_id

    thread_id = new_thread_id()
    state = app_request.app.state
    user_thread_execute = UserThreadExecute(state.db_server)
    data = await user_thread_execute.create_user_thread(user_id=user_id, thread_id=thread_id)
    if data:
        response = {
            "success": True,
            "data": {"user_id": data.get("user_id"), "thread_id": data.get("thread_id")},
            "message": "成功创建会话线程",
        }
    else:
        response = {
            "success": False,
            "message": "创建会话线程失败",
        }
    return response


@router.post("/user_session_thread/details")
async def user_session_thread_details(
        request: UserThreadRequest,
        app_request: Request):
    """
    获取用户会话详情
    """
    # 检查请求字段是否合法
    if not request.thread_id:
        raise HTTPException(status_code=400, detail="获取用户会话详情失败，thread_id不能为空")
    user_id = request.user_id
    thread_id = request.thread_id

    state = app_request.app.state
    agent_args = {
        "user_id": user_id,
        "thread_id": thread_id,
    }
    # 获取短期记忆服务
    memory_service = await get_short_term_memory_service(
        state=state,
        thread_id=thread_id,
        user_id=user_id
    )
    # 获取短期记忆服务中的消息
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
    return session_response


@router.post("/user_session_thread/interrupt")
async def user_session_thread_interrupt(
        request: UserThreadRequest,
        app_request: Request):
    """
    获取会话中断信息
    """
    # 检查请求字段是否合法
    if not request.thread_id:
        raise HTTPException(status_code=400, detail="获取会话中断信息失败，thread_id不能为空")
    user_id = request.user_id
    thread_id = request.thread_id

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
