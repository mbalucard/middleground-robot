"""
基础信息接口
    - get_shop_info: 获取门店信息
    - query_region_tree: 获取区域信息-查询用
    - get_employee_list: 获取员工信息-查询用
    - get_bloc_enterprise_tree: 获取企业模块树
    - switch_owner_page: 切换到租户切换页
    - switch_organ: 切换机构
    - switch_system: 切换系统
    - get_enterprise_list: 获取企业列表
    - get_organ_list: 获取机构列表
"""

from api.virtue_bright.infra.shop_info import get_shop_info
from api.virtue_bright.infra.stores import query_region_tree
from api.virtue_bright.infra.external import get_employee_list
from api.virtue_bright.infra.role import get_bloc_enterprise_tree
from api.virtue_bright.infra.system import switch_owner_page, switch_organ, switch_system, get_enterprise_list, get_organ_list



__all__ = [
    "get_shop_info",
    "query_region_tree",
    "get_employee_list",
    "get_bloc_enterprise_tree",
    "switch_owner_page",
    "switch_organ",
    "switch_system",
    "get_enterprise_list",
    "get_organ_list",
]