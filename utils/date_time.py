"""
日期时间工具
    - get_current_date: 获取当前日期，格式为YYYY-MM-DD
    - timestamp: 获取当前时间戳(单位为秒)
    - get_current_datetime: 获取当前日期时间, 格式为: YYYY-MM-DD HH:MM:SS
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo
import time


def get_current_date() -> str:
    """
    获取当前日期，格式为YYYY-MM-DD
    Returns:
        str: 当前日期，格式为YYYY-MM-DD
    """
    return date.today().strftime("%Y-%m-%d")


def timestamp() -> int:
    """
    获取当前时间戳(单位为秒)
    Returns:
        int: 当前时间戳
    """
    return int(time.time())

def get_current_datetime() -> str:
    """
    获取当前日期时间, 格式为: YYYY-MM-DD HH:MM:SS
    Returns:
        str: 当前日期时间
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_current_datetime_with_zone(zone: str = "Asia/Shanghai") -> str:
    """
    获取当前日期时间, 格式为: YYYY-MM-DD HH:MM:SS
    Args:
        zone: 时区
    Returns:
        str: 当前日期时间
    """
    return datetime.now(ZoneInfo(zone)).isoformat()


if __name__ == "__main__":
    print(get_current_date())
    print(timestamp())
    print(get_current_datetime())
    print(get_current_datetime_with_zone())