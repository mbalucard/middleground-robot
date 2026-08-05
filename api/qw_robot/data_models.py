"""
数据模型
    - RobotMessage 对话存储表
    - RobotToolCall 工具调用记录表
    - init_db 初始化数据库
"""


from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base

from api.qw_robot.general_tools import get_current_datetime
from utils.db_link import PostgresServer


db_server = PostgresServer()
Base = declarative_base()


class RobotMessage(Base):
    __tablename__ = "qw_robot_messages"
    __table_args__ = {'comment': "对话存储表"}
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    message_id = Column(String(64), nullable=False, comment="消息id")
    thread_id = Column(String(64), nullable=False, comment="对话id")
    user_id = Column(String(64), nullable=False, comment="用户id")
    model_name = Column(String(32), nullable=False, comment="模型名称")
    question = Column(Text, nullable=False, comment="问题")
    answer = Column(Text, nullable=True, comment="回答")
    chat_type = Column(String(16), nullable=False, comment="对话类型")
    aibot_id = Column(String(64), nullable=False, comment="企微机器人id")
    create_time = Column(String(32), nullable=False,
default=get_current_datetime(), comment="创建时间")

    def to_dict(self):
        return {
            "id": self.id,
            "message_id": self.message_id,
            "thread_id": self.thread_id,
            "user_id": self.user_id,
            "model_name": self.model_name,
            "question": self.question,
            "answer": self.answer,
            "chat_type": self.chat_type,
            "aibot_id": self.aibot_id,
            "create_time": self.create_time
        }

    def __repr__(self):
        return f"<Message(id={self.id}, message_id={self.message_id}, thread_id={self.thread_id}, user_id={self.user_id}, model_name={self.model_name}, question={self.question}, answer={self.answer}, chat_type={self.chat_type}, aibot_id={self.aibot_id}, create_time={self.create_time})>"


class RobotToolCall(Base):
    __tablename__ = "qw_robot_tool_calls"
    __table_args__ = {'comment': "工具调用记录表"}
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    message_id = Column(String(64), nullable=False, comment="消息id")
    tool_name = Column(String(64), nullable=False, comment="工具名称")
    tool_input = Column(JSONB, nullable=False, comment="工具输入")
    tool_output = Column(Text, nullable=False, comment="工具输出")
    create_time = Column(String(32), nullable=False, default=get_current_datetime(), comment="创建时间")

    def to_dict(self):
        return {
            "id": self.id,
            "message_id": self.message_id,
            "tool_name": self.tool_name,
            "tool_input": self.tool_input,
            "tool_output": self.tool_output,
            "create_time": self.create_time
        }

    def __repr__(self):
        return f"<ToolCall(id={self.id}, message_id={self.message_id}, tool_name={self.tool_name}, tool_input={self.tool_input}, tool_output={self.tool_output}, create_time={self.create_time})>"


async def init_db():
    """初始化数据库"""
    engine = db_server.get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
