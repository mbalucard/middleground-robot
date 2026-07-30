"""
上下文模型
    - Context: 上下文模型
    - SearchSubAgentFindings: 查询子代理输出结构
    - invoke_config: 生成调用配置
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


@dataclass
class Context:
    """ 上下文模型 """
    model: Optional[str] = None  # 模型名称
    api_key: Optional[str] = None  # 通行密匙
    thread_id: Optional[str] = None  # 线程ID
    user_id: Optional[str] = None  # 用户ID


class SearchSubAgentFindings(BaseModel):
    """ 查询子代理输出结构 """
    summary: str = Field(description="结果摘要")
    confidence: float = Field(description="置信度分数,范围从0到1")
    sources: list[str] = Field(description="源网址列表")


def invoke_config(thread_id: str, user_id: str) -> Dict[str, Any]:
    """
    生成调用配置
    Args:
        thread_id(str): 线程ID
        user_id(str): 用户ID
    Returns:
        Dict[str, Any]: 调用配置
    """
    config = {"configurable": {"thread_id": thread_id,"user_id": user_id}}
    return config
