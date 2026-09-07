"""
数据库模型
    - UserThread: 用户会话线程表
    - UserThreadMessage: 用户会话消息表
    - MessageToolCalls: 消息工具调用表
    - init_db: 初始化数据库
"""

from sqlalchemy import Column, Integer, String, Text, UniqueConstraint, Index
from sqlalchemy.orm import declarative_base

from utils.date_time import get_current_datetime
from utils.db_link import PostgresServer

db_server = PostgresServer()
Base = declarative_base()


class UserThread(Base):
    __tablename__ = "user_threads"
    __table_args__ = (
        UniqueConstraint("user_id", "thread_id", name="uq_user_thread"),
        {"comment": "用户会话线程表"},
    )
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    user_id = Column(String(64), nullable=False, comment="用户id")
    thread_id = Column(String(64), nullable=False, comment="会话线程id")
    is_active = Column(Integer, nullable=False, default=1, comment="是否活跃")
    is_deleted = Column(Integer, nullable=False, default=0, comment="是否删除")
    create_time = Column(String(32), nullable=False,
                         default=get_current_datetime(), comment="创建时间")
    update_time = Column(String(32), nullable=False,
                         default=get_current_datetime(), comment="更新时间")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "thread_id": self.thread_id,
            "is_active": self.is_active,
            "is_deleted": self.is_deleted,
            "create_time": self.create_time,
            "update_time": self.update_time
        }

    def __repr__(self):
        return f"<UserThread(id={self.id}, user_id={self.user_id}, thread_id={self.thread_id}, is_active={self.is_active}, is_deleted={self.is_deleted}, create_time={self.create_time}, update_time={self.update_time})>"


class UserThreadMessage(Base):
    __tablename__ = "user_thread_messages"
    __table_args__ = (
        UniqueConstraint("user_id", "thread_id", "message_id",
                         name="uq_user_thread_message"),
        {"comment": "用户会话消息表"},
    )
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    user_id = Column(String(64), nullable=False, comment="用户id")
    thread_id = Column(String(64), nullable=False, comment="会话线程id")
    message_id = Column(String(64), nullable=False, comment="消息id")
    message_type = Column(String(64), nullable=False, comment="消息类型")
    query = Column(Text, nullable=False, comment="问题内容")
    answer = Column(Text, nullable=True, comment="回答内容")
    model_name = Column(String(64), nullable=False, comment="模型名称")
    model_norm = Column(String(64), nullable=True, comment="模型规范")
    create_time = Column(String(32), nullable=False,
                         default=get_current_datetime(), comment="创建时间")
    update_time = Column(String(32), nullable=False,
                         default=get_current_datetime(), comment="更新时间")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "thread_id": self.thread_id,
            "message_id": self.message_id,
            "message_type": self.message_type,
            "query": self.query,
            "answer": self.answer,
            "model_name": self.model_name,
            "model_norm": self.model_norm,
            "create_time": self.create_time,
            "update_time": self.update_time
        }

    def __repr__(self):
        return f"<UserThreadMessage(id={self.id}, user_id={self.user_id}, thread_id={self.thread_id}, message_id={self.message_id}, message_type={self.message_type}, query={self.query}, answer={self.answer}, model_name={self.model_name}, model_norm={self.model_norm}, create_time={self.create_time}, update_time={self.update_time})>"


class MessageToolCalls(Base):
    __tablename__ = "message_tool_calls"
    __table_args__ = (
        UniqueConstraint("user_id", "thread_id", "message_id",
                         "tool_call_id", name="uq_user_thread_message_tool_call"),
        {"comment": "消息工具调用表"},
    )
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    user_id = Column(String(64), nullable=False, comment="用户id")
    thread_id = Column(String(64), nullable=False, comment="会话线程id")
    message_id = Column(String(64), nullable=False, comment="消息id")
    tool_call_id = Column(String(64), nullable=False, comment="工具调用id")
    tool_name = Column(String(64), nullable=False, comment="工具名称")
    tool_input = Column(Text, nullable=True, comment="工具输入")
    tool_output = Column(Text, nullable=True, comment="工具输出")
    create_time = Column(String(32), nullable=False,
                         default=get_current_datetime(), comment="创建时间")
    update_time = Column(String(32), nullable=False,
                         default=get_current_datetime(), comment="更新时间")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "thread_id": self.thread_id,
            "message_id": self.message_id,
            "tool_call_id": self.tool_call_id,
            "tool_name": self.tool_name,
            "tool_input": self.tool_input,
            "tool_output": self.tool_output,
            "create_time": self.create_time,
            "update_time": self.update_time
        }

    def __repr__(self):
        return f"<MessageToolCalls(id={self.id}, user_id={self.user_id}, thread_id={self.thread_id}, message_id={self.message_id}, tool_call_id={self.tool_call_id}, tool_name={self.tool_name}, tool_input={self.tool_input}, tool_output={self.tool_output}, create_time={self.create_time}, update_time={self.update_time})>"


async def init_db():
    """初始化数据库"""
    engine = db_server.get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())
