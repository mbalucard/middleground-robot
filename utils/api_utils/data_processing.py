"""
数据处理工具
"""
from typing import Union
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.types import Interrupt
from utils.logger_manager import LoggerManager

logger = LoggerManager.get_logger(name="data_processing")

def format_long_term_info_key(content: str) -> str:
    """
    格式化长期记忆信息键
    """
    return f"/{content.replace(' ', '_')}.md"



def agent_message_to_dict(message:Union[AIMessage, ToolMessage, Interrupt]) -> dict:
    """
    将Agent消息转换为字典
    """
    if isinstance(message, AIMessage):
        data_dict = {
            "content": message.content,
            "additional_kwargs": message.additional_kwargs,
            "response_metadata": message.response_metadata,
            "id": message.id,
            "tool_calls": message.tool_calls,
            "invalid_tool_calls": message.invalid_tool_calls,
            "usage_metadata": message.usage_metadata,
        }
    elif isinstance(message, ToolMessage):
        data_dict = {
            "content": message.content,
            "name": message.name,
            "id": message.id,
            "tool_call_id": message.tool_call_id,
        }

    elif isinstance(message, Interrupt):
        data_dict = {
            "content": message.value,
            "id": message.id,
        }

    else:
        data_dict = {
            "message": "未知消息类型,无法转换为字典",
        }
        logger.error(f"未知消息类型: {type(message)}")
        logger.error(f"消息内容: {message}")


    return data_dict





if __name__ == "__main__":
    print(format_long_term_info_key("2026-08-30"))