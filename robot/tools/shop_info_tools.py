"""
机构信息
    - dataframe_to_list 将DataFrame转换为字典列表
    - _shop_info_response 响应机构信息
    - _search_name_where 搜索名称条件
    - get_shop_info 获取机构信息
"""

from configs.service_config import DemingMySQL
from utils.async_db_con import AsyncCallSQL, read_sql_language
from configs.general_config import FilePath
from typing import Optional, Literal, List, Dict
from pandas import DataFrame

from langchain.tools import tool

db_client = AsyncCallSQL(DemingMySQL)
data_source = DemingMySQL.data_source


def dataframe_to_list(data: DataFrame) -> List[Dict]:
    """
    将DataFrame转换为字典列表
    Args:
        data: DataFrame
    Returns:
        list: 字典列表
    """
    data_list = []
    if data.empty:
        return data_list
    for i in range(len(data)):
        item_dict = data.iloc[i].to_dict()
        data_list.append(item_dict)
    return data_list


def _shop_info_response(data_list: List[Dict], search_type: Literal['enterprise', 'store', 'shop']) -> Dict:
    if data_list:
        response = {
            "status": "success",
            "data": {
                "data_list": data_list,
                "data_type": search_type,
            },
            "pagination": {"total": len(data_list)},
            "metadata": {
                "data_source": data_source
            }
        }
        return response
    else:
        response = {
            "status": "error",
            "message": "No data found",
            "data": {"data_list": [], "data_type": search_type, },
            "pagination": {"total": 0},
            "metadata": {
                "data_source": data_source
            }
        }
        return response


def _search_name_where(
    search_name: Optional[str],
    search_type: Literal['enterprise', 'store', 'shop']
) -> str:
    if search_name:
        if search_type == 'enterprise':
            return f"and ent.name like '%{search_name}%'"
        elif search_type == 'store':
            return f"and sto.name like '%{search_name}%'"
        elif search_type == 'shop':
            return f"and sto_c.shop_name like '%{search_name}%'"
    else:
        return ""


@tool('get_shop_info', description='获取企业，门店机构，店铺信息')
async def get_shop_info(
    search_name: str,
    search_type: Literal['enterprise', 'store', 'shop'] = 'shop',
    shop_status: Literal[0, 1] = 1,
) -> Dict:
    """
    获取企业，门店机构，店铺信息
    Args:
        search_name: 搜索名称
        search_type: 数据类型, 默认'shop'
            - enterprise:企业 store:门店机构 shop:店铺
        shop_status: 店铺状态, 默认1
            - 1: 正常 0: 禁用
    Returns:
        dict: 企业，门店机构，店铺信息
    """
    data_path = f"{FilePath.ROOT_PATH}/data/sql/shop_info.sql"
    sql_command = read_sql_language(data_path)
    search_name_where = _search_name_where(search_name, search_type)
    sql = sql_command.format(shop_status=shop_status,
                             search_name_where=search_name_where)
    df = await db_client.get_data(sql)
    data = df.copy()

    if search_type == 'enterprise':
        enterprise_group_cols = ['tenant_id', 'tenant_name',
                                 'enterprise_id', 'enterprise_name', 'enterprise_credit_code']
        enterprise_group_data = data.groupby(enterprise_group_cols, as_index=False).agg(
            shore_count=('store_id', 'nunique'), shop_count=('shop_code', 'count'))
        data_list = dataframe_to_list(enterprise_group_data)
        res = _shop_info_response(data_list, search_type)
        return res
    elif search_type == 'store':
        store_group_cols = ['tenant_id', 'tenant_name', 'enterprise_id',
                            'enterprise_name', 'enterprise_credit_code', 'store_id', 'store_name', 'store_credit_code']
        store_group_data = data.groupby(store_group_cols, as_index=False).agg(
            shop_count=('shop_code', 'count'))
        data_list = dataframe_to_list(store_group_data)
        res = _shop_info_response(data_list, search_type)
        return res

    elif search_type == 'shop':
        data_list = dataframe_to_list(data)
        res = _shop_info_response(data_list, search_type)
        return res


if __name__ == "__main__":
    print(get_shop_info.name)
    print(get_shop_info.description)
    print(get_shop_info.args)
