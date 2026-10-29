"""
机构信息工具
    - get_warehouse_info: 获取仓库信息
    - get_shop_available_info: 获取可用门店信息
    - get_region_tree_info: 获取区域树信息
"""


from langchain.tools import tool, ToolRuntime
from typing import Optional, List
from robot.agents.model_context import Context

from api.virtue_bright.bi import warehouse_information
from api.virtue_bright.infra import get_shop_info, query_region_tree
from utils.virtue_bright_erp.data_process import warehouse_information_data_process, shop_info_data_process, region_tree_data_process


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
    result = await warehouse_information(
        authorization=authorization,
        keyword=keyword,
        current=current,
        size=size
    )
    data = result.get('data')
    if isinstance(data, dict):
        records = data.get('records')
        if isinstance(records, List) and records:
            data_list = warehouse_information_data_process(records)
            return {
                "status": "success",
                "data": data_list,
                "page_info": {
                    "current": current,
                    "size": size,
                    "pages": data.get('pages'),
                    "total": data.get('total'),
                }
            }
        else:
            return {"status": "success","data":[]} 
    elif isinstance(data, str):
        return {"status": "error", "message": f"{result.get('msg')},{data}"}
    else:
        return {"status": "error", "message": "未找到店铺信息"}


@tool('get_shop_available_info', description='获取可用门店信息')
async def get_shop_available_info(
    keyword: str,
    current: int = 1,
    size: int = 10,
    tenant_id: Optional[int] = None,
    runtime: ToolRuntime[Context] = None
):
    """
    获取可用门店信息
    Args:
        keyword: 模糊查询
            - 门店名称/简称、门店编码、助记码
        current: 当前页
        size: 每页大小
        tenant_id: 租户ID
    Returns:
        dict: 可用门店信息
    """
    authorization = runtime.context.api_key if runtime and runtime.context else None
    if not authorization:
        return {"status": "error", "message": "未授权"}
    result = await get_shop_info(
        authorization=authorization,
        keyword=keyword,
        current=current,
        size=size,
        tenant_id=tenant_id
    )
    data = result.get('data')
    if isinstance(data, dict):
        records = data.get('records')
        if isinstance(records, List) and records:
            data_list = shop_info_data_process(records)
            return {
                "status": "success",
                "data": data_list,
                "page_info": {
                    "current": current,
                    "size": size,
                    "pages": data.get('pages'),
                    "total": data.get('total'),
                }
            }
        else:
            return {"status": "success","data":[]} 
    elif isinstance(data, str):
        return {"status": "error", "message": f"{result.get('msg')},{data}"}
    else:
        return {"status": "error", "message": "未找到可用门店信息"}


@tool('get_region_tree_info', description='获取区域树信息')
async def get_region_tree_info(
    tenant_id: Optional[int] = None,
    runtime: ToolRuntime[Context] = None
):
    """
    获取区域树信息
    Args:
        tenant_id: 租户ID
    Returns:
        dict: 区域树信息
    """
    authorization = runtime.context.api_key if runtime and runtime.context else None
    if not authorization:
        return {"status": "error", "message": "未授权"}
    result = await query_region_tree(
        authorization=authorization,
        tenant_id=tenant_id
    )
    data = result.get('data')
    if isinstance(data, List) and data:
        data_list = region_tree_data_process(data)
        return {
            "status": "success",
            "data": data_list,
        }
    elif isinstance(data, str):
        return {"status": "error", "message": f"{result.get('msg')},{data}"}
    else:
        return {"status": "error", "message": "未找到区域树信息"}
