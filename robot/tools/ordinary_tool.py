"""
普通工具
    - internet_search 互联网搜索工具
    - get_current_date 获取当前日期
"""


import datetime

from tavily import TavilyClient
from configs.model_config import Tavily
from langchain.tools import tool
from typing import Literal
tavily_client = TavilyClient(api_key=Tavily.API_KEY)

@tool('internet_search',description='互联网搜索工具')
def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """
    使用互联网搜索工具进行搜索
    Args:
        query: 搜索关键词
        max_results: 最大搜索结果数
        topic: 搜索主题
        include_raw_content: 是否包含原始内容
    Returns:
        list: 搜索结果
    """
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )


@tool("get_current_date", description="获取当前日期")
def get_current_date() -> str:
    """
    获取当前日期
    Returns:
        str: 当前日期，格式为YYYY-MM-DD HH:MM:SS
    """
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    tools = [internet_search,get_current_date]
    for tool in tools:
        print(tool.name)
        print(tool.description)
        print(tool.args)
        print("="*100)
    