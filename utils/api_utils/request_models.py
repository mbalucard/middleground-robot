"""
请求数据模型
"""

from typing import List
from pydantic import BaseModel, Field
from robot.agents.agent_invoke import ModelLabel
from robot.agents.agent_invoke import AllowedDecisions


class ReadLongTermInfoRequest(BaseModel):
    """
    长期记忆信息请求模型
    """
    user_id: str = Field(..., description="用户ID")


class LongTermInfoDetailRequest(BaseModel):
    """
    长期记忆信息详情请求模型
    """
    user_id: str = Field(..., description="用户ID")
    key: str = Field(..., description="记忆键")


class WriteLongTermInfoRequest(BaseModel):
    """
    写入长期记忆信息请求模型
    """
    user_id: str = Field(..., description="用户ID")
    key: str = Field(..., description="记忆键")
    content: str = Field(..., description="记忆内容")


class RunAgentRequest(BaseModel):
    """
    运行智能体请求模型
    """
    user_id: str = Field(..., description="用户ID")
    query: str = Field(..., description="查询字符串")
    thread_id: str = Field(..., description="线程ID")
    model_label: ModelLabel = Field(default="deepseek", description="模型标签")
    is_message_all: bool = Field(default=False, description="是否返回所有消息")


class RunAgentInterruptsJudgeRequest(BaseModel):
    """
    中断恢复流式运行智能体请求模型
    """
    user_id: str = Field(..., description="用户ID")
    thread_id: str = Field(..., description="线程ID")
    decides: List[AllowedDecisions] = Field(..., description="决策列表")
    is_all_decides: bool = Field(default=False, description="是否全部决策一致"),
    is_message_all: bool = Field(default=False, description="是否返回所有消息"),


if __name__ == "__main__":
    data = WriteLongTermInfoRequest(
        user_id="user01", key="/2026-08-30.md", content="今天苏州下大雨！")
    print(data)
