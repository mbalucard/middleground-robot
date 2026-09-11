"""
数据库执行工具
    - UserThreadExecute: 用户会话线程执行工具
    - UserThreadMessageExecute: 用户会话消息执行工具
"""


from fastapi import HTTPException
from sqlalchemy import select, update, bindparam
from sqlalchemy.orm import selectinload
from utils.api_utils.db_models import UserThread, UserThreadMessage, MessageToolCalls
from utils.date_time import get_current_datetime
from utils.db_link import PostgresServer
from utils.logger_manager import LoggerManager

logger = LoggerManager.get_logger(name='db_execute')


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
        删除用户会话线程，并级联删除关联的消息和工具调用
        Args:
            user_id: 用户id
            thread_id: 会话线程id
        Returns:
            int: 删除的线程行数
        """
        try:
            async with self.db_server.get_db_session() as db_session:
                stmt = (
                    select(UserThread)
                    .where(
                        UserThread.user_id == user_id,
                        UserThread.thread_id == thread_id,
                    )
                    .options(
                        selectinload(UserThread.messages).selectinload(
                            UserThreadMessage.tool_calls
                        )
                    )
                )
                result = await db_session.execute(stmt)
                threads = result.scalars().all()
                if not threads:
                    return 0
                for user_thread in threads:
                    await db_session.delete(user_thread)
                await db_session.commit()
                return len(threads)
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


class UserThreadMessageExecute:
    """
    用户会话消息执行工具
    """

    def __init__(self, db_server: PostgresServer):
        self.db_server = db_server

    async def create_message(
            self,
            user_id: str,
            thread_id: str,
            message_id: str,
            **kwargs,):
        """
        创建用户会话消息
        Args:
            user_id: 用户id
            thread_id: 会话线程id
            message_id: 消息id
            **kwargs: 插入参数
        Returns:
            dict: 用户会话消息数据
        """
        try:
            async with self.db_server.get_db_session() as db_session:
                thread_message = UserThreadMessage(
                    user_id=user_id,
                    thread_id=thread_id,
                    message_id=message_id,
                    **kwargs,
                )
                db_session.add(thread_message)
                await db_session.commit()
                return thread_message.to_dict()
        except Exception as e:
            logger.error(f"创建用户会话消息失败: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"创建用户会话消息失败: {str(e)}")

    async def select_message(self, *args, **kwargs):
        """
        查询用户会话消息
        Args:
            *args: 查询条件
            **kwargs: 查询参数
        Returns:
            list: 用户会话消息数据
        """
        try:
            async with self.db_server.get_db_session() as db_session:
                stmt = select(UserThreadMessage)
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
            logger.error(f"查询用户会话消息失败: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"查询用户会话消息失败: {str(e)}")

    async def delete_message(
            self,
            user_id: str,
            thread_id: str,
            **kwargs):
        """
        删除用户会话消息,并级联删除关联的工具调用
        Args:
            user_id: 用户id
            thread_id: 会话线程id
            **kwargs: 删除条件
        Returns:
            int: 删除的行数
        """
        try:
            async with self.db_server.get_db_session() as db_session:
                stmt = (
                    select(UserThreadMessage)
                    .where(
                        UserThreadMessage.user_id == user_id,
                        UserThreadMessage.thread_id == thread_id,
                    ).options(
                        selectinload(UserThreadMessage.tool_calls)
                    )
                )
                if kwargs:
                    stmt = stmt.filter_by(**kwargs)
                result = await db_session.execute(stmt)
                rows = result.scalars().all()
                if not rows:
                    return 0
                for row in rows:
                    await db_session.delete(row)
                await db_session.commit()
                return len(rows)
        except Exception as e:
            logger.error(f"删除用户会话消息失败: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"删除用户会话消息失败: {str(e)}")

    async def update_message(
            self,
            user_id: str,
            thread_id: str,
            message_id: str,
            **kwargs,):
        """
        更新用户会话消息
        Args:
            user_id: 用户id
            thread_id: 会话线程id
            message_id: 消息id
            **kwargs: 更新参数
        Returns:
            int: 更新行数
        """
        try:
            async with self.db_server.get_db_session() as db_session:
                stmt = update(UserThreadMessage).where(
                    UserThreadMessage.user_id == user_id,
                    UserThreadMessage.thread_id == thread_id,
                    UserThreadMessage.message_id == message_id
                ).values(update_time=get_current_datetime(), **kwargs)
                result = await db_session.execute(stmt)
                await db_session.commit()
                return result.rowcount
        except Exception as e:
            logger.error(f"更新用户会话消息失败: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"更新用户会话消息失败: {str(e)}")


class MessageToolCallsExecute:
    """
    用户会话消息工具调用执行工具
    """

    def __init__(self, db_server: PostgresServer):
        self.db_server = db_server

    async def create_message_tool_calls(self, tool_calls: list[dict]):
        """
        创建用户会话消息工具调用
        Args:
            tool_calls: 工具调用列表
        Returns:
            int: 创建的行数
        """
        try:
            async with self.db_server.get_db_session() as db_session:
                mes_tool_calls = [MessageToolCalls(
                    **tool_call) for tool_call in tool_calls]
                db_session.add_all(mes_tool_calls)
                await db_session.commit()
                return len(mes_tool_calls)
        except Exception as e:
            logger.error(f"创建用户会话消息工具调用失败: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"创建用户会话消息工具调用失败: {str(e)}")

    async def update_message_tool_calls(self, tool_calls: list[dict]):
        """
        更新用户会话消息工具调用
        Args:
            tool_calls: 工具调用列表
        Returns:
            int: 创建的行数
        """
        if not tool_calls:
            return 0
        try:
            now = get_current_datetime()
            params = [{**item, "update_time": now} for item in tool_calls]
            stmt = (update(MessageToolCalls).where(
                MessageToolCalls.user_id == bindparam("b_user_id"),
                MessageToolCalls.thread_id == bindparam("b_thread_id"),
                MessageToolCalls.message_id == bindparam("b_message_id"),
                MessageToolCalls.tool_call_id == bindparam("b_tool_call_id"),
            ).values(
                tool_output=bindparam("tool_output"),
                update_time=bindparam("update_time"),
            )
            )
            exec_params = [{
                "b_user_id": p["user_id"],
                "b_thread_id": p["thread_id"],
                "b_message_id": p["message_id"],
                "b_tool_call_id": p["tool_call_id"],
                "tool_output": p["tool_output"],
                "update_time": p["update_time"],
            } for p in params]
            async with self.db_server.get_db_session() as db_session:
                conn = await db_session.connection()
                result = await conn.execute(stmt, exec_params)
                await db_session.commit()
                return result.rowcount
        except Exception as e:
            logger.error(f"更新用户会话消息工具调用失败: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"更新用户会话消息工具调用失败: {str(e)}")

    async def select_message_tool_calls(self, *args, **kwargs):
        """
        查询用户会话消息工具调用
        Args:
            *args: 查询条件
            **kwargs: 查询参数
        Returns:
            list: 用户会话消息工具调用数据
        """
        try:
            async with self.db_server.get_db_session() as db_session:
                stmt = select(MessageToolCalls)
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
            logger.error(f"查询用户会话消息工具调用失败: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"查询用户会话消息工具调用失败: {str(e)}")

    async def create_message_tool_calls_incremental(
            self,
            tool_calls: list[dict],
            user_id: str,
            thread_id: str,
            message_id: str,):
        """
        创建用户会话消息工具调用增量
        Args:
            tool_calls: 工具调用列表
            user_id: 用户id
            thread_id: 会话线程id
            message_id: 消息id
        Returns:
            int: 创建的行数
        """
        if not tool_calls:
            return 0
        existing_tool_calls = await self.select_message_tool_calls(
            user_id=user_id,
            thread_id=thread_id,
            message_id=message_id,
        )
        existing_ids = {row["tool_call_id"]
                        for row in (existing_tool_calls or [])}
        new_tools = [
            t for t in tool_calls
            if t.get("tool_call_id") not in existing_ids
        ]
        if not new_tools:
            return 0
        return await self.create_message_tool_calls(new_tools)

    async def delete_message_tool_calls(self, user_id: str, **kwargs):
        """
        删除用户会话消息工具调用
        Args:
            *args: 查询条件
            **kwargs: 查询参数
        Returns:
            int: 删除的行数
        """
        try:
            async with self.db_server.get_db_session() as db_session:
                stmt = (
                    select(MessageToolCalls)
                    .where(
                        MessageToolCalls.user_id == user_id,
                    )
                )
                if kwargs:
                    stmt = stmt.filter_by(**kwargs)
                result = await db_session.execute(stmt)
                rows = result.scalars().all()
                if not rows:
                    return 0
                for row in rows:
                    await db_session.delete(row)
                await db_session.commit()
                return len(rows)
        except Exception as e:
            logger.error(f"删除用户会话消息工具调用失败: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"删除用户会话消息工具调用失败: {str(e)}")


if __name__ == "__main__":
    import asyncio
    db_server = PostgresServer()
    user_thread_execute = UserThreadExecute(db_server)
    data = asyncio.run(user_thread_execute.select_user_thread(
        user_id="user01",
        thread_id="user01-7",
    ))
    print(data)
