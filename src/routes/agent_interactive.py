"""
Agent交互路由
    - run_agent_invoke: 运行智能体请求
    - run_agent_stream: 流式运行智能体请求
"""
import json
from fastapi import APIRouter, HTTPException, Request, Header
from fastapi.responses import StreamingResponse
from utils.logger_manager import LoggerManager
from utils.api_utils.request_models import RunAgentRequest
from utils.api_utils.data_processing import agent_message_to_dict

from robot.agents.agent_invoke import run_agent, run_agent_astream
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
    model_name = request.model_label
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
    agent_args = {
        "user_id": user_id,
        "thread_id": thread_id,
        "model_label": model_name,
    }

    agent_response = {
        "success": True,
        "agent_args": agent_args,
        "total": len(messages),
        "data": messages,
        "data_type": "agent_message",
        "message": "成功获取智能体消息",
    }
    return agent_response


@router.post("/run_agent/stream")
async def run_agent_stream(
        request: RunAgentRequest,
        app_request: Request,
        authorization: Optional[str] = Header(None),):
    """
    流式运行智能体请求
    """
    # 从 Header 读取 API 密钥
    api_key = None
    if authorization and authorization.startswith("Bearer "):
        api_key = authorization
    # 从请求体读取信息
    user_id = request.user_id
    query = request.query
    thread_id = request.thread_id
    model_name = request.model_label
    # 获取应用状态
    state = app_request.app.state
    agent_args = {
        "user_id": user_id,
        "thread_id": thread_id,
        "model_label": model_name,
    }

    async def generate():
        order_num = 0
        async for chunk in run_agent_astream(
            agent=state.agent,
            query=query,
            thread_id=thread_id,
            user_id=user_id,
            model_name=model_name,
            api_key=api_key,
        ):
            order_num += 1
            if chunk.get("model"):
                data_type = "agent"
                message = "智能体消息"
                data = agent_message_to_dict(chunk['model']['messages'][-1])
            elif chunk.get("tools"):
                data_type = "tool"
                message = "工具消息"
                data = agent_message_to_dict(chunk['tools']['messages'][-1])
            elif chunk.get("__interrupt__"):
                data_type = "interrupt"
                message = "中断消息"
                data = agent_message_to_dict(chunk['__interrupt__'][0])
            else:
                data_type = "unknown"
                message = "未知消息"
                data = None
            agent_response = {
                "success": True,
                "agent_args": agent_args,
                "order": {"num": order_num, "is_end": False},
                "data": data,
                "data_type": data_type,
                "message": message,
            }
            yield json.dumps(agent_response, ensure_ascii=False, default=str) + "\n"

        end_response = {
            "success": True,
            "agent_args": agent_args,
            "order": {"num": order_num + 1, "is_end": True},
            "data": None,
            "data_type": "end",
            "message": "流式输出结束",
        }
        yield json.dumps(end_response, ensure_ascii=False, default=str) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")
