"""
零售信息工具
"""

from langchain.tools import tool, ToolRuntime
from typing import Optional, List
from robot.agents.model_context import Context

from api.virtue_bright.bi import store_retail_report
from utils.virtue_bright_erp.data_process import shop_sale_data_process, shop_sale_summary_data_process



@tool('get_shop_retail_info', description='获取门店零售信息')
async def get_shop_retail_info(
    start_date: str,
    end_date: str,
    store_code: List[str] = [],
    store_type: List[str] = [],
    tenant_id: Optional[int] = None,
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
        tenant_id=tenant_id,
        current=current,
        size=size
    )
    data_json = data.get('data').get('records')
    if data_json:
        data_list = shop_sale_data_process(data_json)
        total_summary = shop_sale_summary_data_process(data.get('data').get('totalSummary'))
        total = data.get('data').get('total')
        pages = data.get('data').get('pages')
        return {
            "status": "success",
            "data": data_list,
            "total_summary":total_summary,
            "page_info": {
                "current": current,
                "size": size,
                "pages": pages,
                "total": total,
            }
        }
    else:
        return {"status": "error", "message": "未找到门店零售信息"}