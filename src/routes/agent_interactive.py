"""
Agent交互路由
    - run_agent_invoke: 运行智能体请求
    - run_agent_stream: 流式运行智能体请求
    - run_agent_interrupts_judge_stream: 中断恢复流式运行智能体请求
"""
import json
from fastapi import APIRouter, HTTPException, Request, Header
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from utils.logger_manager import LoggerManager
from utils.api_utils.request_models import RunAgentRequest, RunAgentInterruptsJudgeRequest
from utils.api_utils.data_processing import agent_message_to_dict, tool_call_to_dict
from utils.api_utils.db_execute import UserThreadExecute, UserThreadMessageExecute, MessageToolCallsExecute
from robot.tools.general_tool import new_id

from robot.agents.agent_invoke import run_agent, interrypts_judge, run_agent_astream, interrypts_judge_astream
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
        authorization: Optional[str] = Header(None),):
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
    message_id = new_id(id_type="message")
    model_label = request.model_label
    is_message_all = request.is_message_all
    # 获取应用状态
    state = app_request.app.state
    user_thread_execute = UserThreadExecute(state.db_server)
    message_execute = UserThreadMessageExecute(state.db_server)
    tool_calls_execute = MessageToolCallsExecute(state.db_server)
    agent_args = {
        "user_id": user_id,
        "thread_id": thread_id,
        "message_id": message_id,
        "model_label": model_label,
    }
    # 检查会话线程是否存在
    is_exist = await user_thread_execute.check_user_thread(
        user_id=user_id,
        thread_id=thread_id
    )
    if not is_exist.get("is_exist"):
        return {
            "success": False,
            "agent_args": agent_args,
            "total": 0,
            "data": [],
            "data_type": "error",
            "message": is_exist.get("message")
        }

    # 运行智能体请求
    result = await run_agent(
        agent=state.agent,
        query=query,
        thread_id=thread_id,
        message_id=message_id,
        user_id=user_id,
        model_name=model_label,
        api_key=api_key,
        session_redis=state.session_redis,
    )
    messages_value = result.value["messages"]
    # 获取本轮用户消息的起点
    start = 0
    for i in range(len(messages_value) - 1, -1, -1):
        if isinstance(messages_value[i], HumanMessage):
            start = i
            break
    current_turn = messages_value[start:]
    if is_message_all:
        messages = [agent_message_to_dict(item) for item in current_turn]
    else:
        messages = [agent_message_to_dict(current_turn[-1])]

    if result.interrupts:
        interrupt_info = agent_message_to_dict(result.interrupts[0])
        messages.append(interrupt_info)
        db_insert_info = await message_execute.create_message(
            user_id=user_id,
            thread_id=thread_id,
            message_id=message_id,
            message_type="api",
            query=query,
            model_label=model_label,
        )
    else:
        db_insert_info = await message_execute.create_message(
            user_id=user_id,
            thread_id=thread_id,
            message_id=message_id,
            message_type="api",
            query=query,
            model_label=model_label,
            answer=messages[-1].get("content"),
            model_name=messages[-1].get("response_metadata").get("model_name"),
            model_norm=messages[-1].get(
                "response_metadata").get("model_provider"),
        )

    # 工具调用存表
    tools_list, tool_calls_list = tool_call_to_dict(
        current_turn, user_id, thread_id, message_id)
    if tools_list:
        await tool_calls_execute.create_message_tool_calls_incremental(
            tool_calls=tools_list,
            user_id=user_id,
            thread_id=thread_id,
            message_id=message_id,
            )
    if tool_calls_list:
        await tool_calls_execute.update_message_tool_calls(tool_calls_list)

    agent_response = {
        "success": True,
        "agent_args": agent_args,
        "total": len(messages),
        "data": messages,
        "data_type": "agent_message",
        "message": "成功获取智能体消息",
    }
    return agent_response


@router.post("/run_agent/interrupts_judge/invoke")
async def run_agent_interrupts_judge_invoke(
    request: RunAgentInterruptsJudgeRequest,
    app_request: Request,
):
    """
    中断恢复运行智能体请求
    """
    user_id = request.user_id
    thread_id = request.thread_id
    message_id = request.message_id
    decides = request.decides
    is_all_decides = request.is_all_decides
    is_message_all = request.is_message_all
    # 获取应用状态
    state = app_request.app.state
    user_thread_execute = UserThreadExecute(state.db_server)
    tool_calls_execute = MessageToolCallsExecute(state.db_server)
    agent_args = {
        "user_id": user_id,
        "thread_id": thread_id,
        "message_id": message_id,
    }
    # 检查会话线程是否存在
    is_exist = await user_thread_execute.check_user_thread(
        user_id=user_id,
        thread_id=thread_id
    )
    if not is_exist.get("is_exist"):
        return {
            "success": False,
            "agent_args": agent_args,
            "total": 0,
            "data": [],
            "data_type": "error",
            "message": is_exist.get("message")
        }
    # 中断恢复运行智能体请求
    result = await interrypts_judge(
        agent=state.agent,
        user_id=user_id,
        thread_id=thread_id,
        session_redis=state.session_redis,
        message_id=message_id,
        decides=decides,
        is_all_decides=is_all_decides,
    )
    # 检查中断恢复结果
    if result is None:
        return {
            "success": False,
            "agent_args": agent_args,
            "total": 0,
            "data": [],
            "data_type": "error",
            "message": "中断恢复失败：无有效中断信息或决策参数不合法",
        }
    messages_value = result.value["messages"]
    # 获取本轮用户消息的起点
    start = 0
    for i in range(len(messages_value) - 1, -1, -1):
        if isinstance(messages_value[i], HumanMessage):
            start = i
            break
    current_turn = messages_value[start:]

    if is_message_all:
        messages = [agent_message_to_dict(item) for item in current_turn]
    else:
        messages = [agent_message_to_dict(current_turn[-1])]

    if result.interrupts:
        interrupt_info = agent_message_to_dict(result.interrupts[0])
        messages.append(interrupt_info)
    else:
        message_execute = UserThreadMessageExecute(state.db_server)
        db_update_info = await message_execute.update_message(
            user_id=user_id,
            thread_id=thread_id,
            message_id=message_id,
            answer=messages[-1].get("content"),
            model_name=messages[-1].get("response_metadata").get("model_name"),
            model_norm=messages[-1].get(
                "response_metadata").get("model_provider"),
        )

    agent_response = {
        "success": True,
        "agent_args": agent_args,
        "total": len(messages),
        "data": messages,
        "data_type": "agent_message",
        "message": "成功获取智能体消息",
    }
    # 工具调用存表
    tools_list, tool_calls_list = tool_call_to_dict(
        current_turn, user_id, thread_id, message_id)
    if tools_list:
        await tool_calls_execute.create_message_tool_calls_incremental(
            tool_calls=tools_list,
            user_id=user_id,
            thread_id=thread_id,
            message_id=message_id,
            )
    if tool_calls_list:
        await tool_calls_execute.update_message_tool_calls(tool_calls_list)
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
    model_label = request.model_label
    message_id = new_id(id_type="message")
    # 获取应用状态
    state = app_request.app.state
    user_thread_execute = UserThreadExecute(state.db_server)
    message_execute = UserThreadMessageExecute(state.db_server)
    tool_calls_execute = MessageToolCallsExecute(state.db_server)
    agent_args = {
        "user_id": user_id,
        "thread_id": thread_id,
        "message_id": message_id,
        "model_label": model_label,
    }
    # 检查会话线程是否存在
    is_exist = await user_thread_execute.check_user_thread(
        user_id=user_id,
        thread_id=thread_id
    )

    async def generate():
        if not is_exist.get("is_exist"):
            yield json.dumps({
                "success": False,
                "agent_args": agent_args,
                "total": 0,
                "data": [],
                "data_type": "error",
                "message": is_exist.get("message")
            }, ensure_ascii=False, default=str) + "\n"
            return
        ai_messages = []
        tool_calls_list = []
        order_num = 0
        async for chunk in run_agent_astream(
            agent=state.agent,
            query=query,
            thread_id=thread_id,
            user_id=user_id,
            message_id=message_id,
            model_name=model_label,
            api_key=api_key,
            session_redis=state.session_redis,
        ):
            order_num += 1
            if chunk.get("model"):
                data_type = "agent"
                message = "智能体消息"
                data = agent_message_to_dict(chunk['model']['messages'][-1])
                ai_messages.append(data)
            elif chunk.get("tools"):
                data_type = "tool"
                message = "工具消息"
                data = agent_message_to_dict(chunk['tools']['messages'][-1])
                # 工具调用保存
                tool_call_dict = {
                    "user_id": user_id,
                    "thread_id": thread_id,
                    "message_id": message_id,
                    "tool_call_id": data.get("tool_call_id"),
                    "tool_output": json.dumps(data.get("content")) if not isinstance(data.get("content"), str) else data.get("content"),
                }
                tool_calls_list.append(tool_call_dict)
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
        #! 有问题，如果AI回复完以后，又去调用工具，再回复了一回，就只会存储到最后一回的数据
        if ai_messages:
            # 消息存表
            db_insert_info = await message_execute.create_message(
                user_id=user_id,
                thread_id=thread_id,
                message_id=message_id,
                message_type="api",
                query=query,
                model_label=model_label,
                answer=ai_messages[-1].get("content"),
                model_name=ai_messages[-1].get(
                    "response_metadata").get("model_name"),
                model_norm=ai_messages[-1].get(
                    "response_metadata").get("model_provider"),
            )
            # 工具调用存表
            for message in ai_messages:
                tool_calls = message.get("tool_calls")
                if tool_calls:
                    tools_list = []
                    for tool_call in tool_calls:
                        tool_dict = {
                            "user_id": user_id,
                            "thread_id": thread_id,
                            "message_id": message_id,
                            "tool_call_id": tool_call.get("id"),
                            "tool_name": tool_call.get("name"),
                            "tool_input": json.dumps(tool_call.get("args")),
                        }
                        tools_list.append(tool_dict)
                    await tool_calls_execute.create_message_tool_calls(tools_list)
            # 工具调用更新
            if tool_calls_list:
                await tool_calls_execute.update_message_tool_calls(tool_calls_list)
    return StreamingResponse(generate(), media_type="application/x-ndjson")


@router.post("/run_agent/interrupts_judge/stream")
async def run_agent_interrupts_judge_stream(
    request: RunAgentInterruptsJudgeRequest,
    app_request: Request,
):
    """
    中断恢复流式运行智能体请求
    """
    user_id = request.user_id
    thread_id = request.thread_id
    message_id = request.message_id
    decides = request.decides
    is_all_decides = request.is_all_decides
    # 获取应用状态
    state = app_request.app.state
    user_thread_execute = UserThreadExecute(state.db_server)
    message_execute = UserThreadMessageExecute(state.db_server)
    tool_calls_execute = MessageToolCallsExecute(state.db_server)
    agent_args = {
        "user_id": user_id,
        "thread_id": thread_id,
        "message_id": message_id,
    }
    # 检查会话线程是否存在
    is_exist = await user_thread_execute.check_user_thread(
        user_id=user_id,
        thread_id=thread_id
    )

    # 中断恢复流式运行智能体请求
    async def generate():
        if not is_exist.get("is_exist"):
            yield json.dumps({
                "success": False,
                "agent_args": agent_args,
                "total": 0,
                "data": [],
                "data_type": "error",
                "message": is_exist.get("message")
            }, ensure_ascii=False, default=str) + "\n"
            return

        order_num = 0
        ai_messages = []
        tool_calls_list = []
        async for chunk in interrypts_judge_astream(
            agent=state.agent,
            user_id=user_id,
            thread_id=thread_id,
            message_id=message_id,
            session_redis=state.session_redis,
            decides=decides,
            is_all_decides=is_all_decides,
        ):
            if chunk is None:
                yield json.dumps({
                    "success": False,
                    "agent_args": agent_args,
                    "order": {"num": 1, "is_end": True},
                    "data": None,
                    "data_type": "error",
                    "message": "中断恢复失败：无有效中断信息或决策参数不合法",
                }, ensure_ascii=False, default=str) + "\n"
                return

            order_num += 1
            if chunk.get("model"):
                data_type = "agent"
                message = "智能体消息"
                data = agent_message_to_dict(chunk['model']['messages'][-1])
                ai_messages.append(data)
            elif chunk.get("tools"):
                data_type = "tool"
                message = "工具消息"
                data = agent_message_to_dict(chunk['tools']['messages'][-1])
                # 工具调用保存
                tool_call_dict = {
                    "user_id": user_id,
                    "thread_id": thread_id,
                    "message_id": message_id,
                    "tool_call_id": data.get("tool_call_id"),
                    "tool_output": json.dumps(data.get("content")) if not isinstance(data.get("content"), str) else data.get("content"),
                }
                tool_calls_list.append(tool_call_dict)
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
        if ai_messages:
            # 消息存表
            db_insert_info = await message_execute.update_message(
                user_id=user_id,
                thread_id=thread_id,
                message_id=message_id,
                answer=ai_messages[-1].get("content"),
                model_name=ai_messages[-1].get(
                    "response_metadata").get("model_name"),
                model_norm=ai_messages[-1].get(
                    "response_metadata").get("model_provider"),
            )
            # 工具调用存表
            for message in ai_messages:
                tool_calls = message.get("tool_calls")
                if tool_calls:
                    tools_list = []
                    for tool_call in tool_calls:
                        tool_dict = {
                            "user_id": user_id,
                            "thread_id": thread_id,
                            "message_id": message_id,
                            "tool_call_id": tool_call.get("id"),
                            "tool_name": tool_call.get("name"),
                            "tool_input": json.dumps(tool_call.get("args")),
                        }
                        tools_list.append(tool_dict)
                    await tool_calls_execute.create_message_tool_calls(tools_list)
            # 工具调用更新
            if tool_calls_list:
                await tool_calls_execute.update_message_tool_calls(tool_calls_list)
    return StreamingResponse(generate(), media_type="application/x-ndjson")
