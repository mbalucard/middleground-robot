"""
数据库执行工具
    - UserThreadExecute: 用户会话线程执行工具
"""

from utils.db_link import PostgresServer
from sqlalchemy import select, update, delete
from utils.api_utils.db_models import UserThread, MessageToolCalls, UserThreadMessage
from utils.date_time import get_current_datetime
from utils.logger_manager import LoggerManager

logger = LoggerManager.get_logger(name='user_thread_execute')

class UserThreadExecute:
    """
    用户会话线程执行工具
    """

    def __init__(self, db_server: PostgresServer):
        self.db_server = db_server

    async def create_user_thread(self, user_id: str, thread_id: str):
        """
        创建用户会话线程
        Args:
            user_id: 用户id
            thread_id: 会话线程id
        Returns:
            dict: 用户会话线程数据
        """
        try:
            async with self.db_server.get_db_session() as db_session:
                user_thread = UserThread(user_id=user_id, thread_id=thread_id)
                db_session.add(user_thread)
                await db_session.commit()
                return user_thread.to_dict()
        except Exception as e:
            logger.error(f"创建用户会话线程失败: {str(e)}")
            return None

    async def update_user_thread(self, user_id: str, thread_id: str, **kwargs):
        """
        更新用户会话线程
        Args:
            user_id: 用户id
            thread_id: 会话线程id
            **kwargs: 更新参数
        Returns:
            int: 更新行数
        """
        try:
            async with self.db_server.get_db_session() as db_session:
                result = await db_session.execute(update(UserThread).where(UserThread.user_id == user_id, UserThread.thread_id == thread_id).values(update_time=get_current_datetime(), **kwargs))
                await db_session.commit()
                return result.rowcount
        except Exception as e:
            logger.error(f"更新用户会话线程失败: {str(e)}")
            return None

    async def delete_user_thread(self, user_id: str, thread_id: str):
        """
        删除用户会话线程
        Args:
            user_id: 用户id
            thread_id: 会话线程id
        Returns:
            int: 删除行数
        """
        try:
            async with self.db_server.get_db_session() as db_session:
                result = await db_session.execute(delete(UserThread).where(UserThread.user_id == user_id, UserThread.thread_id == thread_id))
                await db_session.commit()
                return result.rowcount
        except Exception as e:
            logger.error(f"删除用户会话线程失败: {str(e)}")
            return None


if __name__ == "__main__":
    import asyncio
    db_server = PostgresServer()
    user_thread_execute = UserThreadExecute(db_server)
    data = asyncio.run(user_thread_execute.create_user_thread(
        user_id="user01",
        thread_id="t-000",
        # is_active=1,
        # is_deleted=0,
    ))
    print(data)
