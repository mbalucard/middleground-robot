from configs.service_config import DemingMySQL
from utils.async_db_con import AsyncCallSQL, read_sql_language
from configs.general_config import FilePath
from utils.date_time import get_current_date
from typing import Optional

from langchain.tools import tool

db_client = AsyncCallSQL(DemingMySQL)


@tool('get_shop_sale_data', description='获取店铺销售数据')
async def get_shop_sale_data(
    star_date: str = get_current_date(),
    end_date: str = get_current_date(),
    summary_only: bool = False,
    page: int = 1,
    page_size: int = 20,
    shop_name: Optional[str] = None,
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
    Returns:
        dict: 销售数据
    """
    # 读取sql文件
    data_path = f'{FilePath.ROOT_PATH}/data/sql/shop_sale.sql'
    sql_command = read_sql_language(data_path)
    star_date = f'{star_date} 00:00:00'
    end_date = f'{end_date} 23:59:59'
    if shop_name:
        shop_where = f"and sale.shop_name like '%{shop_name}%'"
    else:
        shop_where = ''
    sql = sql_command.format(
        star_date=star_date, end_date=end_date, shop_where=shop_where)
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
                "data_source": "ERP_产线",
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
                "data_source": "ERP_产线",
            }
        }
        return summary_dict

    # 处理明细数据
    data_list = []
    for i in range(len(data)):
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
                    "total": len(data_list),
                    # "shop_names": data['shop_name'].tolist()
                }
            },
            "metadata": {
                "start_date": star_date,
                "end_date": end_date,
                "data_source": "ERP_产线"
            }
        }
        return data_dict


if __name__ == "__main__":
    print(get_shop_sale_data.name)
    print(get_shop_sale_data.description)
    print(get_shop_sale_data.args)
