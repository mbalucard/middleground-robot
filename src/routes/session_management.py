"""
Session管理路由
    - create_session_thread: 创建会话线程
    - delete_session_thread: 删除会话线程
"""
from fastapi import APIRouter, HTTPException, Request
from utils.logger_manager import LoggerManager
from utils.api_utils.request_models import UserThreadRequest
from robot.tools.general_tool import new_id
from utils.api_utils.db_execute import UserThreadExecute

logger = LoggerManager.get_logger(name='session_management')

router = APIRouter(prefix='/session', tags=['Session'])


@router.get("/")
async def session_management():
    """
    Session管理路由,测试用
    """
    return {"message": "这里是Session管理路由"}


@router.post("/session_thread/create")
async def create_session_thread(
        request: UserThreadRequest,
        app_request: Request):
    """
    创建会话线程
    """
    user_id = request.user_id

    thread_id = new_id(id_type="thread")
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
