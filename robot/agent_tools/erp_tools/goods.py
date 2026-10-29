"""
商品信息工具
    - get_goods_info: 获取商品信息
"""

from langchain.tools import tool, ToolRuntime
from typing import Optional, List
from robot.agents.model_context import Context

from api.virtue_bright.product.bs import goods_page_list
from utils.virtue_bright_erp.data_process.goods_data import goods_data_process


@tool('get_goods_info', description='获取商品信息')
async def get_goods_info(
    common_name: Optional[str] = None,
    producer: Optional[str] = None,
    license_number: Optional[str] = None,
    goods_code: Optional[str] = None,
    goods_name: Optional[str] = None,
    goods_barcode: Optional[str] = None,
    current: int = 1,
    size: int = 10,
    runtime: ToolRuntime[Context] = None
):
    """
    获取商品信息
    Args:
        common_name: 通用名称
        producer: 生产企业
        license_number: 批准文号
        goods_code: 商品编码
        goods_name: 商品名称
        goods_barcode: 商品条码
        current: 当前页
        size: 每页大小
    Returns:
        dict: 商品信息
    """
    authorization = runtime.context.api_key if runtime and runtime.context else None
    if not authorization:
        return {"status": "error", "message": "未授权"}
    result = await goods_page_list(
        authorization=authorization,
        codes=goods_code,
        name=goods_name,
        commonName=common_name,
        producer=producer,
        licenseNumber=license_number,
        barcode=goods_barcode,
        current=current,
        size=size
    )
    data = result.get('data')
    if isinstance(data, dict):
        records = data.get('records')
        if isinstance(records, List) and records:
            data_list = goods_data_process(records)
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
        return {"status": "error", "message": "未找到商品信息"}
