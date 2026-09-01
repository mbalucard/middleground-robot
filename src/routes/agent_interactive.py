"""
Agent交互路由
"""
from fastapi import APIRouter, HTTPException, Request,Header
from utils.logger_manager import LoggerManager
from utils.api_utils.request_models import RunAgentRequest

from robot.agents.agent_invoke import run_agent
from typing import Optional
logger = LoggerManager.get_logger(name='agent_interactive')

router = APIRouter(prefix='/agent', tags=['Agent'])


@router.get("/")
async def agent_interactive():
    """ Agent交互路由,测试用 """
    return {"message": "这里是Agent交互路由"}


@router.post("/run_agent/invoke")
async def run_agent_invoke(
    request: RunAgentRequest, 
    app_request: Request,
    authorization: Optional[str] = Header(None),
    ):
    """
    运行智能体请求
    """
    # 从 Header 读取 API 密钥
    api_key = None
    if authorization and authorization.startswith("Bearer "):
        api_key = authorization
    # 从请求体读取信息
    user_id = request.user_id
    query = request.query
    thread_id = request.thread_id
    model_name = request.model_name
    is_message_all = request.is_message_all
    # 获取应用状态
    state = app_request.app.state

    result = await run_agent(
        agent=state.agent,
        query=query,
        thread_id=thread_id,
        user_id=user_id,
        model_name=model_name,
        api_key=api_key)
    if is_message_all:
        messages = result.value["messages"]
    else:
        messages = [result.value["messages"][-1]]

    agent_response = {
        "success": True,
        "user_id": user_id,
        "thread_id": thread_id,
        "model_name": model_name,
        "total": len(messages),
        "data": messages,
        "data_type": "agent_message",
        "message": "成功获取智能体消息",
    }
    return agent_response
