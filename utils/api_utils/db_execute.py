"""
数据库执行工具
    - UserThreadExecute: 用户会话线程执行工具
"""


from fastapi import HTTPException
from sqlalchemy import select, update, delete
from utils.api_utils.db_models import UserThread, MessageToolCalls, UserThreadMessage
from utils.date_time import get_current_datetime
from utils.db_link import PostgresServer
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
            raise HTTPException(
                status_code=500, detail=f"创建用户会话线程失败: {str(e)}")

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
            raise HTTPException(
                status_code=500, detail=f"更新用户会话线程失败: {str(e)}")

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
            raise HTTPException(
                status_code=500, detail=f"删除用户会话线程失败: {str(e)}")

    async def select_user_thread(self, *args, **kwargs):
        """
        查询用户会话线程
        Args:
            *args: 查询条件
            **kwargs: 查询参数
        Returns:
            list: 用户会话线程数据
        """
        try:
            async with self.db_server.get_db_session() as db_session:
                stmt = select(UserThread)
                if args:
                    stmt = stmt.where(*args)
                if kwargs:
                    stmt = stmt.filter_by(**kwargs)
                result = await db_session.execute(stmt)
                rows = result.scalars().all()
                if rows:
                    rows = [row.to_dict() for row in rows]
                return rows

        except Exception as e:
            logger.error(f"查询用户会话线程失败: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"查询用户会话线程失败: {str(e)}")

    async def check_user_thread(self, user_id: str, thread_id: str):
        """
        检查用户会话线程
        Args:
            user_id: 用户id
            thread_id: 会话线程id
        Returns:
            bool: 是否存在
        """
        try:
            data = await self.select_user_thread(user_id=user_id, thread_id=thread_id)
            if data:
                if len(data) == 1:
                    if data[0]['is_active'] == 1 and data[0]['is_deleted'] == 0:
                        return {"is_exist": True, "message": "会话线程存在且唯一"}
                    elif data[0]['is_active'] == 0:
                        logger.warning(f"用户会话线程已归档: {user_id} : {thread_id}")
                        return {"is_exist": False, "message": "用户会话线程已归档"}
                    elif data[0]['is_deleted'] == 1:
                        logger.warning(f"用户会话线程已删除: {user_id} : {thread_id}")
                        return {"is_exist": False, "message": "会话线程已删除"}
                else:
                    logger.warning(f"用户会话线程不唯一: {user_id} : {thread_id}")
                    return {"is_exist": False, "message": "会话线程不唯一"}
            else:
                logger.warning(f"用户会话线程不存在: {user_id} : {thread_id}")
                return {"is_exist": False, "message": "用户会话线程不存在"}
        except Exception as e:
            logger.error(f"检查用户会话线程失败: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"检查用户会话线程失败: {str(e)}")


if __name__ == "__main__":
    import asyncio
    db_server = PostgresServer()
    user_thread_execute = UserThreadExecute(db_server)
    data = asyncio.run(user_thread_execute.select_user_thread(
        user_id="user01",
        thread_id="user01-7",
    ))
    print(data)
