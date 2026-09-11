"""
数据处理工具
    - format_long_term_info_key 格式化长期记忆信息键
    - agent_message_to_dict 将Agent消息转换为字典
"""
from typing import Union
import json
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage
from langgraph.types import Interrupt
from utils.logger_manager import LoggerManager

logger = LoggerManager.get_logger(name="data_processing")

AgentMessageType = Union[AIMessage, ToolMessage, Interrupt, HumanMessage]


def format_long_term_info_key(content: str) -> str:
    """
    格式化长期记忆信息键
    """
    return f"/{content.replace(' ', '_')}.md"


def agent_message_to_dict(message: AgentMessageType) -> dict:
    """
    将Agent消息转换为字典
    Args:
        message: Agent消息
    Returns:
        dict: 转换后的字典
    """
    if isinstance(message, AIMessage):
        data_dict = {
            "type": "AIMessage",
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
            "type": "ToolMessage",
            "content": message.content,
            "name": message.name,
            "id": message.id,
            "tool_call_id": message.tool_call_id,
        }

    elif isinstance(message, Interrupt):
        data_dict = {
            "type": "Interrupt",
            "content": message.value,
            "id": message.id,
        }
    elif isinstance(message, HumanMessage):
        data_dict = {
            "type": "HumanMessage",
            "content": message.content,
            "id": message.id,
            "additional_kwargs": message.additional_kwargs or {},
            "response_metadata": message.response_metadata or {},
        }
    else:
        data_dict = {}
        logger.warning(f"未知消息类型: {type(message)}")
    return data_dict


def tool_call_to_dict(
        agent_call_list: list[AgentMessageType],
        user_id: str,
        thread_id: str,
        message_id: str) -> tuple[list[dict], list[dict]]:
    """
    将Agent消息的工具调用转换为字典
    Args:
        agent_call_list: Agent消息
        user_id: 用户ID
        thread_id: 线程ID
        message_id: 消息ID
    Returns:
        tuple[list[dict], list[dict]]: 工具调用列表和工具调用更新列表
    """
    tools_list = []
    tool_calls_list = []
    for item in agent_call_list:
        if isinstance(item, AIMessage):
            tools = item.tool_calls
            if tools:
                for tool in tools:
                    tool_dict = {
                        "user_id": user_id,
                        "thread_id": thread_id,
                        "message_id": message_id,
                        "tool_call_id": tool.get("id"),
                        "tool_name": tool.get("name"),
                        "tool_input": json.dumps(tool.get("args")),
                    }
                    tools_list.append(tool_dict)
        elif isinstance(item, ToolMessage):
            tool_dict = {
                "user_id": user_id,
                "thread_id": thread_id,
                "message_id": message_id,
                "tool_call_id": item.tool_call_id,
                "tool_output": json.dumps(item.content) if not isinstance(item.content, str) else item.content,
            }
            tool_calls_list.append(tool_dict)
    return tools_list, tool_calls_list


if __name__ == "__main__":
    print(format_long_term_info_key("2026-08-30"))
