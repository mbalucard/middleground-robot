"""
BI相关接口
    - inventory_report: 库存明细报表
    - warehouse_information: 仓库信息
"""

from api.virtue_bright.bi.report import inventory_report, warehouse_information

__all__ = [
    "inventory_report",
    "warehouse_information",
]