"""
数据交互
    - insert_message 插入消息
"""
from api.qw_robot.data_models import RobotMessage, RobotToolCall


async def insert_message(
    db_session,
    message_id: str,
    thread_id: str,
    user_id: str,
    model_name: str,
    question: str,
    answer: str,
    chat_type: str,
    aibot_id: str,):
    """
    插入消息
    Args:
        db_session: 数据库会话对象
        message_id: 消息ID
        thread_id: 对话ID
        user_id: 用户ID
        model_name: 模型名称
        question: 问题
        answer: 答案
        chat_type: 对话类型
        aibot_id: 企微机器人ID
    Returns:
        RobotMessage: 插入后的消息
    """
    message = RobotMessage(
        message_id=message_id,
        thread_id=thread_id,
        user_id=user_id,
        model_name=model_name,
        question=question,
        answer=answer,
        chat_type=chat_type,
        aibot_id=aibot_id,
    )
    db_session.add(message)
    await db_session.commit()
    await db_session.refresh(message)
    return message


async def insert_tool_call(
    db_session,
    message_id: str,
    tool_name: str,
    tool_input: dict,
    tool_output: str,
):
    """
    插入工具调用
    Args:
        db_session: 数据库会话对象
        message_id: 消息ID
        tool_name: 工具名称
        tool_input: 工具输入
        tool_output: 工具输出
    Returns:
        RobotToolCall: 插入后的工具调用
    """
    tool_call = RobotToolCall(
        message_id=message_id,
        tool_name=tool_name,
        tool_input=tool_input,
        tool_output=tool_output,
    )
    db_session.add(tool_call)
    await db_session.commit()
    await db_session.refresh(tool_call)
    return tool_call