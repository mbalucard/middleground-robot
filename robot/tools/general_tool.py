"""
通用工具
"""

import uuid
from typing import Literal, Optional

IdType = Literal["thread", "message", ]


def new_id(id_type: Optional[IdType] = None) -> str:
    """
    生成唯一会话ID
    Args:
        id_type: 唯一ID类型
    Returns:
        str: 唯一会话ID
    """
    if id_type == "thread":
        return f"t-{str(uuid.uuid4())}"
    elif id_type == "message":
        return f"m-{str(uuid.uuid4())}"
    else:
        return f"G-{str(uuid.uuid4())}"
