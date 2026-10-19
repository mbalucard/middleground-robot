"""
库存信息工具
    - get_inventory_details: 获取商品库存明细
"""

from langchain.tools import tool, ToolRuntime
from typing import Optional, List
from robot.agents.model_context import Context

from api.virtue_bright.bi.report import inventory_report
from utils.virtue_bright_erp.data_process.inventory_data import inventory_data_process


@tool('get_inventory_data', description='获取商品库存数据')
async def get_inventory_data(
    tenant_id: Optional[int] = None,
    current: int = 1,
    size: int = 20,
    goods_codes: List[str] = [],
    goods_mnemonic_code: Optional[str] = None,
    shop_type: List[str] = [],
    warehouse_id: List[str] = [],
    is_summary: bool = True,
    runtime: ToolRuntime[Context] = None
):
    """
    获取库存数据
    Args:
        tenant_id: 租户ID
        current: 当前页码
        size: 每页大小
        goods_codes: 商品编码列表
        goods_mnemonic_code: 商品助记码
        shop_type: 门店类型列表
        warehouse_id: 仓库ID列表
        is_summary: 是否汇总查询
    Returns:
        dict: 库存数据
    """
    authorization = runtime.context.api_key if runtime and runtime.context else None
    if not authorization:
        return {"status": "error", "message": "未授权"}

    data = await inventory_report(
        authorization=authorization,
        tenant_id=tenant_id,
        current=current,
        size=size,
        codes=goods_codes,
        mnemonic_code=goods_mnemonic_code,
        shop_type=shop_type,
        warehouse_id=warehouse_id,
        is_summary=is_summary,
    )
    data_json = data.get('data').get('records')
    if data_json:
        data_list = inventory_data_process(data_json,is_summary=is_summary)
        total_summary = data.get('data').get('totalSummary')
        pages = data.get('data').get('pages')
        total = data.get('data').get('total')
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
        return {"status": "error", "message": "未找到库存明细"}

