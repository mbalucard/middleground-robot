"""
零售信息工具
    - get_shop_retail_info: 获取门店零售信息
"""

from langchain.tools import tool, ToolRuntime
from typing import Optional, List
from robot.agents.model_context import Context

from api.virtue_bright.bi import store_retail_report, store_goods_retail_report
from utils.virtue_bright_erp.data_process import shop_sale_data_process, shop_sale_summary_data_process, store_goods_retail_data_process, store_goods_retail_summary_data_process


@tool('get_shop_retail_info', description='获取门店零售信息')
async def get_shop_retail_info(
    start_date: str,
    end_date: str,
    store_code: List[str] = [],
    store_type: List[str] = [],
    tenant_id: Optional[int] = None,
    region_id: List[str] = [],
    current: int = 1,
    size: int = 20,
    runtime: ToolRuntime[Context] = None
):
    """
    获取门店零售信息
    Args:
        start_date: 开始日期
            - 格式为YYYY-MM-DD
        end_date: 结束日期
            - 格式为YYYY-MM-DD
        store_code: 门店编码
        store_type: 门店类型
            - 1-直营, 2-加盟
        tenant_id: 租户ID
        region_id: 区域ID列表
        current: 当前页
        size: 每页大小, 默认20
    Returns:
        dict: 门店零售信息
    """
    authorization = runtime.context.api_key if runtime and runtime.context else None
    if not authorization:
        return {"status": "error", "message": "未授权"}
    data = await store_retail_report(
        authorization=authorization,
        start_date=start_date,
        end_date=end_date,
        store_code=store_code,
        store_type=store_type,
        belongRegion=region_id,
        tenant_id=tenant_id,
        current=current,
        size=size
    )
    data_json = data.get('data').get('records')
    if data_json:
        data_list = shop_sale_data_process(data_json)
        total_summary = shop_sale_summary_data_process(
            data.get('data').get('totalSummary'))
        total = data.get('data').get('total')
        pages = data.get('data').get('pages')
        return {
            "status": "success",
            "data": data_list,
            "total_summary": total_summary,
            "page_info": {
                "current": current,
                "size": size,
                "pages": pages,
                "total": total,
            }
        }
    else:
        return {"status": "error", "message": "未找到门店零售信息"}


@tool('get_store_goods_retail_info', description='获取门店商品零售信息')
async def get_store_goods_retail_info(
    start_date: str,
    end_date: str,
    goods_codes: List[str] = [],
    store_code: List[str] = [],
    store_type: List[str] = [],
    tenant_id: Optional[int] = None,
    region_id: List[str] = [],
    is_store_summary: bool = False,
    current: int = 1,
    size: int = 20,
    runtime: ToolRuntime[Context] = None):
    """
    获取门店商品零售信息
    Args:
        start_date: 开始日期
            - 格式为YYYY-MM-DD
        end_date: 结束日期
            - 格式为YYYY-MM-DD
        goods_codes: 商品编码列表
        store_code: 门店编码列表
        store_type: 门店类型列表
            - 1-直营, 2-加盟
        tenant_id: 租户ID
        region_id: 区域ID列表
        is_store_summary: 是否按门店汇总
        current: 当前页
        size: 每页大小, 默认20
    Returns:
        dict: 门店商品零售信息
    """
    authorization = runtime.context.api_key if runtime and runtime.context else None
    if not authorization:
        return {"status": "error", "message": "未授权"}

    data = await store_goods_retail_report(
        authorization=authorization,
        start_date=start_date,
        end_date=end_date,
        goods_code=goods_codes,
        store_code=store_code,
        store_type=store_type,
        belongRegion=region_id,
        tenant_id=tenant_id,
        is_store_summary=is_store_summary,
        current=current,
        size=size
    )
    data_json = data.get('data').get('records')
    if data_json:
        data_list = store_goods_retail_data_process(
            data_json,
            is_store_summary=is_store_summary,
        )
        total_summary = store_goods_retail_summary_data_process(data.get('data').get('totalSummary'))
        total = data.get('data').get('total')
        pages = data.get('data').get('pages')
        return {
            "status": "success",
            "data": data_list,
            "total_summary": total_summary,
            "page_info": {
                "current": current,
                "size": size,
                "pages": pages,
                "total": total,
            }
        }
    else:
        return {"status": "error", "message": "未找到门店商品零售信息"}