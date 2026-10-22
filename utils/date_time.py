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
    获取当前日期时间, 格式为: YYYY-MM-DDTHH:MM:SS+00:00
    Args:
        zone: 时区
    Returns:
        str: 当前日期时间
    """
    return datetime.now(ZoneInfo(zone)).isoformat()


def format_rfc3339_like_current_date(
    value: str,
    zone: str = "Asia/Shanghai",) -> str:
    """
    将 UTC RFC 3339 时间转成与 get_current_date 相同的本地时间字符串
    Args:
        value(str): RFC 3339 时间，例如 2026-10-19T16:00:00+00:00
        zone(str): IANA 时区名, default="Asia/Shanghai"
    Returns:
        str: YYYY-MM-DD HH:MM:SS 星期几
    """
    weekdays = ("星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日")
    local = datetime.fromisoformat(value).astimezone(ZoneInfo(zone))
    return f"{local.strftime('%Y-%m-%d %H:%M:%S')} {weekdays[local.weekday()]}"


if __name__ == "__main__":
    print(get_current_date())
    print(timestamp())
    print(get_current_datetime())
    print(get_current_datetime_with_zone())
    print(format_rfc3339_like_current_date('2026-10-19T20:00:00+00:00'))