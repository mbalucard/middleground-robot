"""
库存信息工具

"""

from langchain.tools import tool, ToolRuntime
from typing import Optional, List
from robot.agents.model_context import Context

from api.virtue_bright.bi.report import inventory_report
from utils.virtue_bright_erp.data_process.inventory_data import inventory_data_process


@tool('get_inventory_details', description='获取商品库存明细')
async def get_inventory_details(
    tenant_id: Optional[int] = None,
    current: int = 1,
    size: int = 20,
    goods_codes: List[str] = [],
    goods_mnemonic_code: Optional[str] = None,
    shop_type: List[str] = ["1"],
    warehouse_id: List[str] = [],
    runtime: ToolRuntime[Context] = None
):
    """
    获取库存明细
    Args:
        tenant_id: 租户ID
        current: 当前页码
        size: 每页大小
        goods_codes: 商品编码列表
        goods_mnemonic_code: 商品助记码
        shop_type: 门店类型列表
        warehouse_id: 仓库ID列表
    Returns:
        dict: 库存明细
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
        warehouse_id=warehouse_id
    )
    data_json = data.get('data').get('records')
    if data_json:
        data_list = inventory_data_process(data_json)
        total_summary = data.get('data').get('totalSummary')
        return {
            "status": "success",
            "data": data_list,
            "total_summary": total_summary,
            "page_info": {
                "current": current,
                "size": size,
                "pages": data.get('data').get('pages'),
                "total": data.get('data').get('total'),
            }
        }
    else:
        return {"status": "error", "message": "未找到库存明细"}

