"""
德明ERP数据处理
    - warehouse_information_data_process: 机构仓库信息数据处理-查询用
    - shop_info_data_process: 门店信息数据处理-查询用
    - goods_data_process: 商品数据处理-查询用
    - inventory_data_process: 库存数据处理-查询用
    - shop_sale_data_process: 门店销售数据处理-查询用
    - shop_sale_summary_data_process: 门店销售汇总数据处理
"""

from utils.virtue_bright_erp.data_process.ins_data import (
    warehouse_information_data_process,
    shop_info_data_process,
)
from utils.virtue_bright_erp.data_process.goods_data import (
    goods_data_process,
)
from utils.virtue_bright_erp.data_process.inventory_data import (
    inventory_data_process,
)
from utils.virtue_bright_erp.data_process.sale_data import (
    shop_sale_data_process,
    shop_sale_summary_data_process,
)

__all__ = [
    "warehouse_information_data_process",
    "shop_info_data_process",
    "goods_data_process",
    "inventory_data_process",
    "shop_sale_data_process",
    "shop_sale_summary_data_process",
]