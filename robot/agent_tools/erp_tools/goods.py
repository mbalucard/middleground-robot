"""
商品信息工具
    - get_goods_info: 获取商品信息
"""

from langchain.tools import tool, ToolRuntime
from typing import Optional
from robot.agents.model_context import Context

from api.virtue_bright.product.bs import goods_page_list
from utils.virtue_bright_erp.data_process.goods_data import goods_data_process


@tool('get_goods_info', description='获取商品信息')
async def get_goods_info(
    commonName: Optional[str] = None,
    producer: Optional[str] = None,
    licenseNumber: Optional[str] = None,
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
        commonName: 通用名称
        producer: 生产企业
        licenseNumber: 批准文号
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
    data = await goods_page_list(
        authorization=authorization,
        codes=goods_code,
        name=goods_name,
        commonName=commonName,
        producer=producer,
        licenseNumber=licenseNumber,
        barcode=goods_barcode,
        current=current,
        size=size
    )
    data_json = data.get('data').get('records')
    if data_json:
        data_list = goods_data_process(data_json)
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
        return {"status": "error", "message": "未找到商品信息"}
