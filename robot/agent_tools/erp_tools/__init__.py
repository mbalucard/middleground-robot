"""
ERP接口相关工具集
    - get_goods_info: 获取商品信息
    - get_warehouse_info: 获取仓库信息
    - get_inventory_details: 获取库存明细
    - get_shop_available_info: 获取可用门店信息
    - get_shop_retail_info: 获取门店零售信息
"""

from robot.agent_tools.erp_tools.goods import get_goods_info
from robot.agent_tools.erp_tools.inventory import get_inventory_data
from robot.agent_tools.erp_tools.shop_info import get_warehouse_info, get_shop_available_info, get_region_tree_info
from robot.agent_tools.erp_tools.retail_info import get_shop_retail_info

__all__ = [
    "get_goods_info",
    "get_warehouse_info",
    "get_inventory_data",
    "get_shop_available_info",
    "get_shop_retail_info",
    "get_region_tree_info",
]