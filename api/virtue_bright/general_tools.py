"""
通用工具函数
    - timestamp: 获取当前时间戳
    - get_current_date: 获取当前日期
    - get_date_start_and_end_time: 获取指定日期的开始和结束时间
    - retrieve_past_date: 获取过去的日期
"""
import time
import datetime
from utils.logger_manager import LoggerManager

logger = LoggerManager.get_logger(name=__name__)

def timestamp():
    """
    获取当前时间戳
    Returns:
        int: 当前时间戳，单位为毫秒
    """
    return time.time_ns() // 1000000


def get_current_date():
    """
    获取当前日期
    Returns:
        str: 当前日期，格式为YYYY-MM-DD
    """
    return datetime.date.today().strftime("%Y-%m-%d")


def get_date_start_and_end_time(date_input: str):
    """
    获取指定日期的开始和结束时间
    Args:
        date (str): 日期，格式为YYYY-MM-DD
    Returns:
        dict: 包含开始时间和结束时间的字典
        - start_time(str): 指定日期的开始时间 格式为YYYY-MM-DD 00:00:00
        - end_time(str): 指定日期的结束时间，格式为YYYY-MM-DD 23:59:59
    """
    # 如果输入是字符串，转换为date对象
    if isinstance(date_input, str):
        try:
            target_date = datetime.datetime.strptime(
                date_input, "%Y-%m-%d").date()
        except ValueError as e:
            logger.error(f"日期格式错误: {e}")
            return None
    elif isinstance(date_input, datetime.date):
        target_date = date_input
    else:
        raise ValueError(
            f"不支持的日期格式: {type(date_input)}，请使用字符串 'YYYY-MM-DD' 或 datetime.date 对象")

    start_time = datetime.datetime.combine(
        target_date, datetime.time.min).strftime("%Y-%m-%d %H:%M:%S")
    end_time = datetime.datetime.combine(
        target_date, datetime.time.max).strftime("%Y-%m-%d %H:%M:%S")
    return {
        "start_time": start_time,
        "end_time": end_time
    }


def retrieve_past_date(days_ago: int):
    """
    获取过去的日期
    Args:
        days_ago (int): 天数，例如1表示昨天，2表示前天，以此类推
    Returns:
        str: 过去的日期，格式为YYYY-MM-DD
    """
    current_date = datetime.date.today()
    # 创建一个 timedelta 对象，表示要减去的天数
    delta = datetime.timedelta(days=days_ago)
    # 从当前日期减去 timedelta
    target_date = current_date - delta
    return target_date.strftime("%Y-%m-%d")


if __name__ == "__main__":
    print(f"当前时间戳为{timestamp()}毫秒")
    print(f"当前日期为{get_current_date()}")
    print(f"昨天的日期为{retrieve_past_date(1)}")
    print(get_date_start_and_end_time("2025/12/10"))
