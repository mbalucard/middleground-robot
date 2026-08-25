"""
会话管理
    - normalize_tool_content 规范化工具内容
    - session_hset 会话存表
    - tool_calls_hset 工具调用存表
"""
import redis.asyncio as redis
import json
from api.qw_robot.data_interaction import insert_message, insert_tool_call
from utils.logger_manager import LoggerManager
from utils.db_link import PostgresServer

pg_link = PostgresServer()

logger = LoggerManager.get_logger(name=__name__)
ttl = 60

#! 目前只考虑到tool_call和mcp中的text类型，后续需要优化
def normalize_tool_content(content) -> str:
    """
    规范化工具内容
    Args:
        content: 工具内容
    Returns:
        str: 规范化后的工具内容
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_value = content[-1]
        if isinstance(text_value, dict):
            if text_value.get("type") == "text":
                return text_value.get("text")
    logger.warning(f"tool_output 工具输出规范化失败: {content}")
    return ""


async def session_hset(
    redis_client: redis.Redis,
    message_id: str,
    user_id: str,
    aibot_id: str = '',
    chat_type: str = '',
    thread_id: str = '',
    question: str = '',
    answer: str = '',
    model_name: str = '',
):
    """
    会话存表
    Args:
        redis_client: Redis连接
        message_id: 消息ID
        user_id: 用户ID
        aibot_id: 企微机器人ID
        chat_type: 对话类型
        thread_id: 对话ID
        question: 问题
        answer: 答案
        model_name: 模型名称
    Returns:
        message_key: 消息键
    """
    message_key = f"message:{user_id}+{message_id}"

    if await redis_client.exists(message_key):
        message_dict = await redis_client.hgetall(message_key)
        if answer:
            message_dict['answer'] = answer
        if model_name:
            message_dict['model_name'] = model_name
        await redis_client.hset(message_key, mapping=message_dict)
        async with pg_link.get_db_session() as db_session:
            try:
                await insert_message(
                    db_session=db_session,
                    message_id=message_id,
                    user_id=user_id,
                    aibot_id=message_dict.get('aibot_id'),
                    chat_type=message_dict.get('chat_type'),
                    thread_id=message_dict.get('thread_id'),
                    question=message_dict.get('question'),
                    answer=message_dict.get('answer'),
                    model_name=message_dict.get('model_name'),
                )
                await redis_client.delete(message_key)  # 删除缓存
            except Exception as e:
                logger.error(f"插入数据库失败: {e}")
    else:
        message_dict = {
            "message_id": message_id,
            "user_id": user_id,
            "aibot_id": aibot_id,
            "chat_type": chat_type,
            "thread_id": thread_id,
            "question": question,
            "answer": answer,
            "model_name": model_name,
        }
        await redis_client.hset(message_key, mapping=message_dict)
    await redis_client.expire(message_key, time=ttl)
    return message_key


async def tool_calls_hset(
        redis_client: redis.Redis,
        message_id: str,
        tool_call_id: str,
        tool_name: str = '',
        tool_input: str = '',
        tool_output: str = '',):
    """
    工具调用存表
    Args:
        redis_client: Redis连接
        message_id: 消息ID
        tool_call_id: 工具调用ID
        tool_name: 工具名称
        tool_input: 工具输入
        tool_output: 工具输出
    Returns:
        tool_call_key: 工具调用键
    """
    tool_call_key = f"tool_calls:{message_id}+{tool_call_id}"
    if await redis_client.exists(tool_call_key):
        value = await redis_client.hgetall(tool_call_key)
        if tool_output:
            # logger.info(f"tool_output 工具输出: {tool_output}")
            tool_output = normalize_tool_content(tool_output)
            value['tool_output'] = tool_output
        await redis_client.hset(tool_call_key, mapping=value)
        async with pg_link.get_db_session() as db_session:
            try:
                await insert_tool_call(
                    db_session=db_session,
                    message_id=message_id,
                    tool_call_id=tool_call_id,
                    tool_name=value.get('tool_name'),
                    tool_input=value.get('tool_input'),
                    tool_output=tool_output,
                )
                await redis_client.delete(tool_call_key)  # 删除缓存
            except Exception as e:
                logger.error(f"插入数据库失败: {e}")
    else:
        value = {
            "message_id": message_id,
            "tool_call_id": tool_call_id,
            "tool_name": tool_name,
            "tool_input": tool_input,
            "tool_output": tool_output,
        }
        # logger.info(f"tool_redis_call_value 工具调用: {value}")  
        await redis_client.hset(tool_call_key, mapping=value)
    await redis_client.expire(tool_call_key, time=ttl)
    return tool_call_key
