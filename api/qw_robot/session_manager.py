"""
会话管理
"""
import redis.asyncio as redis

from api.qw_robot.data_interaction import insert_message
from utils.logger_manager import LoggerManager
from utils.db_link import PostgresServer

pg_link = PostgresServer()

logger = LoggerManager.get_logger(name=__name__)


async def session_hset(
    redis_client:redis.Redis, 
    message_id:str,
    user_id:str,
    aibot_id:str = '',
    chat_type:str = '',
    thread_id:str = '',
    question:str = '',
    answer:str = '',
    model_name:str = '',
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
    message_key = f"{user_id}+{message_id}"

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
    await redis_client.expire(message_key, time=30)
    return message_key