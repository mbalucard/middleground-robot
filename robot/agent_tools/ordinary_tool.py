"""
普通工具
    - internet_search 互联网搜索工具
    - get_current_date 获取当前日期
"""

from datetime import datetime

from tavily import TavilyClient
from configs.model_config import Tavily
from langchain.tools import tool
from typing import Literal, Optional
from api.deepseek_tool import DeepSeekSearchEngine
from utils.date_time import format_rfc3339_like_current_date

deepseek_search_engine = DeepSeekSearchEngine()
tavily_client = TavilyClient(api_key=Tavily.API_KEY)


@tool('tavily_internet_search', description='互联网搜索工具')
def tavily_internet_search(
        query: str,
        max_results: int = 5,
        topic: Literal["general", "news", "finance"] = "general",
        include_raw_content: bool = False,):
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
        str: 当前日期，格式为YYYY-MM-DD HH:MM:SS 星期几
    """
    weekdays = ("星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日")
    now = datetime.now()
    return f"{now.strftime('%Y-%m-%d %H:%M:%S')} {weekdays[now.weekday()]}"


@tool('internet_search', description='按 query 搜索网页，返回结构化的结果列表')
async def internet_search(
    query: str,
    count: int = 3,
    need_content: bool = False,
    ori_question: Optional[str] = None,
):
    """
    使用互联网搜索工具进行搜索
    Args:
        query: 搜索关键词
        count: 搜索结果数量
        need_content: 是否包含原始内容
        ori_question: 用户的原始问题，帮引擎理解意图
    Returns:
        dict: 搜索结果
    """
    search_data = await deepseek_search_engine.search(
        query=query,
        count=count,
        need_content=need_content,
        ori_question=ori_question,
    )
    results = search_data.get('results', [])
    if results:
        result_list = []
        for item in results:
            item_dict = {k: v for k, v in item.items() if k != 'site_icon'}
            if item_dict.get('date'):
                item_dict['date'] = format_rfc3339_like_current_date(
                    item_dict['date'])
            result_list.append(item_dict)
        return {"status": "success", "data": result_list}
    else:
        return {"status": "error", "message": search_data, }


@tool('fetch_internet_content', description='抓取网页，返回页面标题与 Markdown 格式的内容')
async def fetch_internet_content(url: str):
    """
    抓取网页，返回页面标题与 Markdown 格式的内容
    Args:
        url: 网页 URL
    Returns:
        dict: 抓取结果
    """
    fetch_data = await deepseek_search_engine.fetch(url)
    if fetch_data.get('error'):
        return {"status": "error", "message": fetch_data}
    else:
        return {"status": "success", "data": fetch_data}


if __name__ == "__main__":
    tools = [internet_search, get_current_date]
    for tool in tools:
        print(tool.name)
        print(tool.description)
        print(tool.args)
        print("="*100)
