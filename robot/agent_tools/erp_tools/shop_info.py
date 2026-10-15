"""
店铺信息工具
    - get_warehouse_info: 获取仓库信息
"""


from langchain.tools import tool, ToolRuntime
from typing import Optional
from robot.agents.model_context import Context

from api.virtue_bright.bi.report import warehouse_information
from utils.virtue_bright_erp.data_process.ins_data import warehouse_information_data_process

@tool('get_warehouse_info', description='获取仓库信息')
async def get_warehouse_info(
    keyword: str,
    current: int = 1,
    size: int = 10,
    runtime: ToolRuntime[Context] = None
):
    """
    获取仓库信息
    Args:
        keyword: 模糊查询
            - 门店名称/简称、门店编码、助记码
        current: 当前页
        size: 每页大小
    Returns:
        dict: 仓库信息
    """
    authorization = runtime.context.api_key if runtime and runtime.context else None
    if not authorization:
        return {"status": "error", "message": "未授权"}
    data = await warehouse_information(
        authorization=authorization,
        keyword=keyword,
        current=current,
        size=size
    )
    data_json = data.get('data').get('records')
    if data_json:
        data_list = warehouse_information_data_process(data_json)
        return {
            "status": "success",
            "data": data_list,
            "page_info": {
                "current": current,
                "size": size,
                "pages": data.get('data').get('pages'),
                "total": data.get('data').get('total'),
            }
        }
    else:
        return {"status": "error", "message": "未找到店铺信息"}