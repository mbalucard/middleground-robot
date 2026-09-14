"""
API后台任务
    - run_agent_background_task: 运行智能体后台任务存表
    - run_agent_stream_background_task: 流式运行智能体后台任务存表
"""
import json
from utils.api_utils.data_processing import AgentMessageType, tool_call_to_dict
from utils.logger_manager import LoggerManager
from utils.api_utils.db_execute import UserThreadMessageExecute, MessageToolCallsExecute

logger = LoggerManager.get_logger("api_background_tasks")


async def agent_storage_background_task(
        message_execute: UserThreadMessageExecute,
        tool_calls_execute: MessageToolCallsExecute,
        *,
        user_id: str,
        thread_id: str,
        message_id: str,
        messages: list[dict],
        current_turn: list[AgentMessageType],
        is_interrupt: bool = False,
        run_interrupt_task: bool = False,
        query: str = '',
        model_label: str = '',):
    """
    运行智能体后台任务存表 覆盖静态任务和中断恢复任务
    Args:
        message_execute: 用户消息执行类
        tool_calls_execute: 工具调用执行类
        user_id: 用户ID
        thread_id: 会话ID
        message_id: 消息ID
        messages: 消息列表
        current_turn: 当前轮次消息列表
        is_interrupt: 是否中断
        run_interrupt_task: 是否运行中断任务，默认False
        query: 用户问题
        model_label: 模型标签
    Returns:
        None
    """
    try:
        if is_interrupt and not run_interrupt_task:
            await message_execute.create_message(
                user_id=user_id,
                thread_id=thread_id,
                message_id=message_id,
                message_type="api",
                query=query,
                model_label=model_label,
            )
        else:
            meta = messages[-1].get("response_metadata") or {}
            if not run_interrupt_task:
                await message_execute.create_message(
                    user_id=user_id,
                    thread_id=thread_id,
                    message_id=message_id,
                    message_type="api",
                    query=query,
                    model_label=model_label,
                    answer=messages[-1].get("content"),
                    model_name=meta.get("model_name"),
                    model_norm=meta.get("model_provider"),
                )
            else:
                await message_execute.update_message(
                    user_id=user_id,
                    thread_id=thread_id,
                    message_id=message_id,
                    answer=messages[-1].get("content"),
                    model_name=meta.get("model_name"),
                    model_norm=meta.get("model_provider"),
                )
        tools_list, tool_calls_list = tool_call_to_dict(
            agent_call_list=current_turn,
            user_id=user_id,
            thread_id=thread_id,
            message_id=message_id,
        )
        if tools_list:
            await tool_calls_execute.create_message_tool_calls_incremental(
                tool_calls=tools_list,
                user_id=user_id,
                thread_id=thread_id,
                message_id=message_id,
            )
        if tool_calls_list:
            await tool_calls_execute.update_message_tool_calls(tool_calls_list)
    except Exception as e:
        logger.exception(f"run_agent落库失败,message_id: {message_id}, {str(e)}")


async def agent_storage_stream_background_task(
        message_execute: UserThreadMessageExecute,
        tool_calls_execute: MessageToolCallsExecute,
        *,
        user_id: str,
        thread_id: str,
        message_id: str,
        query: str = '',
        model_label: str = '',
        messages: list[dict] = [],
        tool_calls_list: list[dict] = [],
        is_interrupt=False,):
    if messages:
        #! 有问题，如果AI回复完以后，又去调用工具，再回复了一回，就只会存储到最后一回的数据
        meta = messages[-1].get("response_metadata") or {}
        if not is_interrupt:
            await message_execute.create_message(
                user_id=user_id,
                thread_id=thread_id,
                message_id=message_id,
                message_type="api",
                query=query,
                model_label=model_label,
                answer=messages[-1].get("content"),
                model_name=meta.get("model_name"),
                model_norm=meta.get("model_provider"),
            )
        else:
            await message_execute.update_message(
                user_id=user_id,
                thread_id=thread_id,
                message_id=message_id,
                answer=messages[-1].get("content"),
                model_name=meta.get("model_name"),
                model_norm=meta.get("model_provider"),
            )
        for message in messages:
            tool_calls = message.get("tool_calls")
            if tool_calls:
                tools_list = []
                for tool_call in tool_calls:
                    tools_list.append({
                        "user_id": user_id,
                        "thread_id": thread_id,
                        "message_id": message_id,
                        "tool_call_id": tool_call.get("id"),
                        "tool_name": tool_call.get("name"),
                        "tool_input": json.dumps(tool_call.get("args")),
                    })
                await tool_calls_execute.create_message_tool_calls(tools_list)
        if tool_calls_list:
            await tool_calls_execute.update_message_tool_calls(tool_calls_list)
