"""
通用数据处理工具
"""


def remove_none(obj):
    """
    移除对象中的None值
    Args:
        obj: 对象
    Returns:
        obj: 移除None值后的对象
    """
    if isinstance(obj, dict):
        return {k: remove_none(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [remove_none(item) for item in obj]
    return obj