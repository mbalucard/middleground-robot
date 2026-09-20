"""
请求数据模型
    - LongTermInfoRequest: 长期记忆信息请求模型
    - UserThreadRequest: 用户会话线程请求模型
    - ImageInput: 图文请求中的单张图片
    - RunAgentRequest: 运行智能体请求模型
    - RunAgentInterruptsJudgeRequest: 中断恢复流式运行智能体请求模型
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from robot.agents.model_context import ModelLabel
from robot.agents.agent_invoke import AllowedDecisions

VisionProviderField = Literal["openai", "anthropic"]


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


class ImageInput(BaseModel):
    """
    图文请求中的单张图片（JSON base64）
    """
    data: str = Field(..., description="图片 base64 或 data URL")
    media_type: Optional[str] = Field(
        default=None, description="可选 MIME，如 image/jpeg；缺省则按文件头探测"
    )


class RunAgentRequest(BaseModel):
    """
    运行智能体请求模型
    """
    user_id: str = Field(..., description="用户ID")
    query: str = Field(..., description="查询字符串")
    thread_id: str = Field(..., description="线程ID")
    model_label: ModelLabel = Field(default="deepseek", description="模型标签")
    is_message_all: bool = Field(default=False, description="是否返回所有消息")
    images: List[ImageInput] = Field(
        default_factory=list, description="可选图片列表（base64），最多 10 张"
    )
    provider: Optional[VisionProviderField] = Field(
        default=None,
        description="有图时必填：openai / anthropic，决定多模态 content 协议",
    )


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
