"""
通用工具
"""

import uuid

def new_thread_id() -> str:
    """
    生成唯一会话ID
    Returns:
        str: 唯一会话ID
    """
    return f"t-{str(uuid.uuid4())}"