"""
请求数据模型
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


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


if __name__ == "__main__":
    data = WriteLongTermInfoRequest(user_id="user01", key="/2026-08-30.md", content="今天苏州下大雨！")
    print(data)