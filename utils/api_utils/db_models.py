"""
SQLAlchemy 2.0 写法的数据模型对照
    - UserThread: 用户会话线程表
    - UserThreadMessage: 用户会话消息表
    - MessageToolCalls: 消息工具调用表
    - init_db: 初始化数据库
"""

from typing import Optional

from sqlalchemy import ForeignKeyConstraint, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from utils.date_time import get_current_datetime
from utils.db_link import PostgresServer

db_server = PostgresServer()


class Base(DeclarativeBase):
    pass


class UserThread(Base):
    __tablename__ = "user_threads"
    __table_args__ = (
        UniqueConstraint("user_id", "thread_id", name="uq_user_thread"),
        {"comment": "用户会话线程表"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="主键")
    user_id: Mapped[str] = mapped_column(String(64), comment="用户id")
    thread_id: Mapped[str] = mapped_column(String(64), comment="会话线程id")
    is_active: Mapped[int] = mapped_column(default=1, comment="是否活跃")
    is_deleted: Mapped[int] = mapped_column(default=0, comment="是否删除")
    create_time: Mapped[str] = mapped_column(
        String(32), default=get_current_datetime, comment="创建时间")
    update_time: Mapped[str] = mapped_column(
        String(32), default=get_current_datetime, comment="更新时间")

    messages: Mapped[list["UserThreadMessage"]] = relationship(
        back_populates="thread",
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        """
        转为字典
        Returns:
            dict: 线程字段
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "thread_id": self.thread_id,
            "is_active": self.is_active,
            "is_deleted": self.is_deleted,
            "create_time": self.create_time,
            "update_time": self.update_time,
        }

    def __repr__(self):
        return (
            f"<UserThread(id={self.id}, user_id={self.user_id}, "
            f"thread_id={self.thread_id}, is_active={self.is_active}, "
            f"is_deleted={self.is_deleted}, create_time={self.create_time}, "
            f"update_time={self.update_time})>"
        )


class UserThreadMessage(Base):
    __tablename__ = "user_thread_messages"
    __table_args__ = (
        UniqueConstraint("user_id", "thread_id", "message_id",
                         name="uq_user_thread_message"),
        ForeignKeyConstraint(
            ["user_id", "thread_id"],
            ["user_threads.user_id", "user_threads.thread_id"],
            name="fk_message_thread",
            ondelete="CASCADE",
        ),
        {"comment": "用户会话消息表"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="主键")
    user_id: Mapped[str] = mapped_column(String(64), comment="用户id")
    thread_id: Mapped[str] = mapped_column(String(64), comment="会话线程id")
    message_id: Mapped[str] = mapped_column(String(64), comment="消息id")
    message_type: Mapped[str] = mapped_column(String(64), comment="消息类型")
    query: Mapped[str] = mapped_column(Text, comment="问题内容")
    answer: Mapped[Optional[str]] = mapped_column(Text, comment="回答内容")
    model_name: Mapped[str] = mapped_column(String(64), comment="模型名称")
    model_norm: Mapped[Optional[str]] = mapped_column(String(64), comment="模型规范")
    create_time: Mapped[str] = mapped_column(
        String(32), default=get_current_datetime, comment="创建时间")
    update_time: Mapped[str] = mapped_column(
        String(32), default=get_current_datetime, comment="更新时间")

    thread: Mapped["UserThread"] = relationship(back_populates="messages")
    tool_calls: Mapped[list["MessageToolCalls"]] = relationship(
        back_populates="message",
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        """
        转为字典
        Returns:
            dict: 消息字段
        """
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
            "update_time": self.update_time,
        }

    def __repr__(self):
        return (
            f"<UserThreadMessage(id={self.id}, user_id={self.user_id}, "
            f"thread_id={self.thread_id}, message_id={self.message_id}, "
            f"message_type={self.message_type}, query={self.query}, "
            f"answer={self.answer}, model_name={self.model_name}, "
            f"model_norm={self.model_norm}, create_time={self.create_time}, "
            f"update_time={self.update_time})>"
        )


class MessageToolCalls(Base):
    __tablename__ = "message_tool_calls"
    __table_args__ = (
        UniqueConstraint("user_id", "thread_id", "message_id",
                         "tool_call_id", name="uq_user_thread_message_tool_call"),
        ForeignKeyConstraint(
            ["user_id", "thread_id", "message_id"],
            ["user_thread_messages.user_id", "user_thread_messages.thread_id",
             "user_thread_messages.message_id"],
            name="fk_tool_call_message",
            ondelete="CASCADE",
        ),
        {"comment": "消息工具调用表"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="主键")
    user_id: Mapped[str] = mapped_column(String(64), comment="用户id")
    thread_id: Mapped[str] = mapped_column(String(64), comment="会话线程id")
    message_id: Mapped[str] = mapped_column(String(64), comment="消息id")
    tool_call_id: Mapped[str] = mapped_column(String(64), comment="工具调用id")
    tool_name: Mapped[str] = mapped_column(String(64), comment="工具名称")
    tool_input: Mapped[Optional[str]] = mapped_column(Text, comment="工具输入")
    tool_output: Mapped[Optional[str]] = mapped_column(Text, comment="工具输出")
    create_time: Mapped[str] = mapped_column(
        String(32), default=get_current_datetime, comment="创建时间")
    update_time: Mapped[str] = mapped_column(
        String(32), default=get_current_datetime, comment="更新时间")

    message: Mapped["UserThreadMessage"] = relationship(back_populates="tool_calls")

    def to_dict(self):
        """
        转为字典
        Returns:
            dict: 工具调用字段
        """
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
            "update_time": self.update_time,
        }

    def __repr__(self):
        return (
            f"<MessageToolCalls(id={self.id}, user_id={self.user_id}, "
            f"thread_id={self.thread_id}, message_id={self.message_id}, "
            f"tool_call_id={self.tool_call_id}, tool_name={self.tool_name}, "
            f"tool_input={self.tool_input}, tool_output={self.tool_output}, "
            f"create_time={self.create_time}, update_time={self.update_time})>"
        )


async def init_db():
    """
    初始化数据库
    """
    engine = db_server.get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())
