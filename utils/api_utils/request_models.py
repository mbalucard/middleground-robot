"""
请求数据模型
    - LongTermInfoRequest: 长期记忆信息请求模型
    - UserThreadRequest: 用户会话线程请求模型
    - RunAgentRequest: 运行智能体请求模型
    - RunAgentInterruptsJudgeRequest: 中断恢复流式运行智能体请求模型
"""

from typing import List
from pydantic import BaseModel, Field
from robot.agents.agent_invoke import ModelLabel
from robot.agents.agent_invoke import AllowedDecisions


class LongTermInfoRequest(BaseModel):
    """
    长期记忆信息请求模型
    """
    user_id: str = Field(..., description="用户ID")
    key: str = Field(None, description="记忆键")
    content: str = Field(None, description="记忆内容")


class UserThreadRequest(BaseModel):
    """
    用户会话线程请求模型
    """
    user_id: str = Field(..., description="用户ID")
    thread_id: str = Field(None, description="线程ID")


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
    message_id: str = Field(default='', description="消息ID")
    decides: List[AllowedDecisions] = Field(..., description="决策列表")
    is_all_decides: bool = Field(default=False, description="是否全部决策一致"),
    is_message_all: bool = Field(default=False, description="是否返回所有消息"),


if __name__ == "__main__":
    data = LongTermInfoRequest(
        user_id="user01", key="/2026-08-30.md", content="今天苏州下大雨！")
    print(data)
