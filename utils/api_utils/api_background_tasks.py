"""
API后台任务
    - run_agent_background_task: 运行智能体后台任务存表
"""
from utils.api_utils.data_processing import AgentMessageType, tool_call_to_dict
from utils.logger_manager import LoggerManager
from fastapi import HTTPException
from utils.api_utils.db_execute import UserThreadExecute, UserThreadMessageExecute, MessageToolCallsExecute

logger = LoggerManager.get_logger("api_background_tasks")


async def run_agent_background_task(
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
        model_label: str = '',
):
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
