"""
请求数据模型
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class LongTermInfoRequest(BaseModel):
    """
    长期记忆信息请求模型
    """
    user_id: str  # 用户ID