"""
机构数据

"""

from typing import List
import pandas as pd


def warehouse_information_data_process(data_json: list[dict]):
    """
    机构仓库信息数据处理-查询用
    用以处理德明接口 warehouse_information 返回的机构仓库信息数据
    Args:
        data_json (list[dict]): 机构数据列表
    Returns:
        list[dict]: 处理后的机构数据
    """

    columns_dict = {
        'tenant_id': '租户ID',
        'address': '仓库地址',
        'code': '门店/仓库编码',
        'stoId': '门店ID',
        'stoName': '门店名称',
        'regionName': '区域名称',
        'type': '仓库类型',
        'warehouseName': '仓库名称',
        'regionCode': '区域编码',
        'nameAbc': '助记码',
        'name': '门店/仓库名称',
        'statusName': 'statusName',
        'tel': '座机号码',
        'enterpriseId': '企业ID',
        'id': '仓库ID',
        'shortName': '门店/仓库简称',
        'enterpriseName': '企业名称',
        'status': '状态'
    }
    columns_names = ["租户ID","企业ID","企业名称","门店/仓库编码", "门店/仓库名称","门店/仓库简称","仓库ID","仓库名称","区域名称","仓库类型","座机号码","仓库地址"]
    warehouse_type ={"sto":"门店仓","dc":"企业仓库"}

    df = pd.DataFrame(data_json)
    df = df.rename(columns=columns_dict)
    df_data = df.loc[:, columns_names]
    df_data['仓库类型'] = df_data['仓库类型'].map(warehouse_type)
    data_dict = df_data.to_dict(orient='records')
    return data_dict
    