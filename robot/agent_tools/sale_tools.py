"""
销售工具集
    - get_shop_sale_data: 获取店铺销售数据
    - list_shops_with_sales: 获取时间段内有销售的店铺信息
"""
from configs.service_config import DemingMySQL
from utils.async_db_con import AsyncCallSQL, read_sql_language
from configs.general_config import FilePath
from utils.date_time import get_current_date
from typing import Optional, Literal

from langchain.tools import tool

db_client = AsyncCallSQL(DemingMySQL)
data_source = DemingMySQL.data_source


@tool('get_shop_sale_data', description='获取店铺销售数据')
async def get_shop_sale_data(
    star_date: str = get_current_date(),
    end_date: str = get_current_date(),
    summary_only: bool = False,
    page: int = 1,
    page_size: int = 20,
    shop_name: Optional[str] = None,
    shop_code: Optional[str] = None,
    store_code: Optional[str] = None,
):
    """
    获取零售数据
    Args:
        star_date: 开始日期 格式为YYYY-MM-DD
        end_date: 结束日期 格式为YYYY-MM-DD
        summary_only: 是否只返回汇总数据
        page: 页码
        page_size: 每页条数
        shop_name: 店铺简称
        shop_code: 店铺编码
        store_code: 门店编码
    Returns:
        dict: 销售数据
    """
    # 读取sql文件
    data_path = f'{FilePath.ROOT_PATH}/data/sql/shop_sale.sql'
    sql_command = read_sql_language(data_path)
    star_date = f'{star_date} 00:00:00'
    end_date = f'{end_date} 23:59:59'
    if store_code:
        store_code_where = f"and sto_c.store_code = '{store_code}'"
    else:
        store_code_where = ''
    if shop_code and not store_code:
        shop_code_where = f"and sale.shop_code = '{shop_code}'"
    else:
        shop_code_where = ''
    if shop_name and not shop_code and not store_code:
        shop_name_where = f"and sale.shop_name like '%{shop_name}%'"
    else:
        shop_name_where = ''

    sql = sql_command.format(
        star_date=star_date, 
        end_date=end_date, 
        shop_name_where=shop_name_where, 
        shop_code_where=shop_code_where, 
        store_code_where=store_code_where
    )
    # 执行sql
    df = await db_client.get_data(sql)
    # 检查数据是否为空
    if df.empty:
        return {
            "status": "error",
            "message": "数据为空，请检查日期范围或店铺简称",
            "data": {},
            "metadata": {
                "start_date": star_date,
                "end_date": end_date,
                "data_source": data_source,
            }
        }
    # 转换数据类型为float
    data = df.copy()
    cols = ['amount_receivable', 'amount_received', 'cost_amount', 'gross_profit',
            'discount_amount', 'average_order_value', 'gross_profit_margin']
    data[cols] = data[cols].astype(float)
    # 计算汇总数据
    sum_cols = [
        'number_of_orders',
        'amount_receivable',
        'amount_received',
        'cost_amount',
        'gross_profit',
        'discount_amount',
    ]
    group_cols = ['tenant_id', 'enterprise_id', 'enterprise_name']
    summary = (
        data
        .groupby(group_cols, as_index=False)[sum_cols]
        .sum()
        .round(2)
    )
    summary['average_order_value'] = (
        summary['amount_received'] / summary['number_of_orders']
    ).round(2)
    summary['gross_profit_margin'] = (
        summary['gross_profit'] / summary['amount_received']
    ).round(4)
    sum_result = summary.iloc[0].to_dict()
    if summary_only:
        summary_dict = {
            "status": "success",
            "data": {
                "summary": sum_result,
                "shop_sales_list": [],
            },
            "metadata": {
                "start_date": star_date,
                "end_date": end_date,
                "data_source": data_source,
            }
        }
        return summary_dict

    # 处理明细数据
    total_lines = len(data)
    start = (page - 1) * page_size
    end = min(start + page_size, total_lines)
    data_list = []
    
    for i in range(start, end):
        item_dict = data.iloc[i].to_dict()
        data_list.append(item_dict)

    if data_list:
        data_dict = {
            "status": "success",
            "data": {
                "summary": sum_result,
                "shop_sales_list": data_list,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_lines": total_lines,
                    "lines_per_page": len(data_list),
                    "next_page": 'True' if end < total_lines else 'False',
                }
            },
            "metadata": {
                "start_date": star_date,
                "end_date": end_date,
                "data_source": data_source
            }
        }
        return data_dict

@tool('list_shops_with_sales', description='获取时间段内有销售的店铺信息')
async def list_shops_with_sales(
    star_date: str = get_current_date(),
    end_date: str = get_current_date(),
    page: int = 1,
    page_size: int = 20,
    search_name: Optional[str] = None,
    search_type: Optional[Literal['shop', 'store']] = 'store',
):
    """
    获取时间段内有销售的店铺信息
    Args:
        star_date: 开始日期 格式为YYYY-MM-DD
        end_date: 结束日期 格式为YYYY-MM-DD
        page: 页码
        page_size: 每页条数
        search_name: 搜索名称
        search_type: 搜索类型 默认store
            - shop: 搜索店铺 store: 搜索门店
    """
    # 读取sql文件
    data_path = f'{FilePath.ROOT_PATH}/data/sql/shops_with_sales.sql'
    sql_command = read_sql_language(data_path)
    star_date = f'{star_date} 00:00:00'
    end_date = f'{end_date} 23:59:59'

    if search_name:
        if search_type == 'shop':
            search_name_where = f" and sale.shop_name like '%{search_name}%'"
        elif search_type == 'store':
            search_name_where = f" and stores.name like '%{search_name}%'"
    else:
        search_name_where = ''


    sql = sql_command.format(star_date=star_date, end_date=end_date, search_name_where=search_name_where)
    df = await db_client.get_data(sql)
    if df.empty:
        res_dict = {
            "status": "error",
            "message": "数据为空，请检查日期范围或搜索名称",
            "data": {},
            "metadata": {
                "start_date": star_date,
                "end_date": end_date,
                "data_source": data_source
            }
        }
        return res_dict
    
    data = df.copy()
    total_lines = len(data)
    start = (page - 1) * page_size
    end = min(start + page_size, total_lines)
    data_list = []
    for i in range(start, end):
        item_dict = data.iloc[i].to_dict()
        data_list.append(item_dict)

    res_dict = {
        "status": "success",
        "data": {
            "data_list": data_list,
            "pagination": {
                "total_lines": total_lines,
                "page": page,
                "page_size": page_size,
                "lines_per_page": len(data_list),
                "next_page": 'True' if end < total_lines else 'False',
            },
            "metadata": {
                "start_date": star_date,
                "end_date": end_date,
                "data_source": data_source
            }
        }
    }
    return res_dict


if __name__ == "__main__":
    print(get_shop_sale_data.name)
    print(get_shop_sale_data.description)
    print(get_shop_sale_data.args)
