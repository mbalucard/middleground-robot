"""
基础信息接口
    - get_shop_info: 获取门店信息
    - query_region_tree: 获取区域信息-查询用
"""

from api.virtue_bright.infra.shop_info import get_shop_info
from api.virtue_bright.infra.stores import query_region_tree

__all__ = [
    "get_shop_info",
    "query_region_tree",
]