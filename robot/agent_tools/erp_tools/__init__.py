"""
ERP接口相关工具集
    - get_goods_info: 获取商品信息
    - get_warehouse_info: 获取仓库信息
    - get_inventory_details: 获取库存明细
    - get_inventory_audit_summary_data: 获取库存盘点商品或门店汇总数据
    - get_shop_available_info: 获取可用门店信息
    - get_shop_retail_info: 获取门店零售信息
    - get_store_goods_retail_info: 获取门店商品零售信息
"""

from robot.agent_tools.erp_tools.goods import get_goods_info
from robot.agent_tools.erp_tools.inventory import get_inventory_data, get_inventory_audit_summary_data
from robot.agent_tools.erp_tools.shop_info import get_warehouse_info, get_shop_available_info, get_region_tree_info
from robot.agent_tools.erp_tools.retail_info import get_shop_retail_info, get_store_goods_retail_info

__all__ = [
    "get_goods_info",
    "get_warehouse_info",
    "get_inventory_data",
    "get_inventory_audit_summary_data",
    "get_shop_available_info",
    "get_shop_retail_info",
    "get_region_tree_info",
    "get_store_goods_retail_info",
]