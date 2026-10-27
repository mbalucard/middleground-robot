"""
BI相关接口
    - inventory_report: 库存明细报表
    - warehouse_information: 仓库信息
    - store_retail_report: 门店零汇总报表
    - store_goods_retail_report: 门店商品汇总报表
    - inventory_audit_summary_report: 库存盘点汇总报表
"""

from api.virtue_bright.bi.report import (
    inventory_report,
    warehouse_information,
    store_retail_report,
    store_goods_retail_report,
    inventory_audit_summary_report,
)

__all__ = [
    "inventory_report",
    "warehouse_information",
    "store_retail_report",
    "store_goods_retail_report",
    "inventory_audit_summary_report",
]
