"""
人员数据处理
    - employee_data_process: 人员数据处理
"""

from typing import List
import pandas as pd


def employee_data_process(data_json: List[dict]):
    """
    人员数据处理
    用以处理德明接口 get_employee_list 返回的data
    Args:
        data_json (List[dict]): 人员数据
    Returns:
        List[dict]: 处理后的人员数据
    """
    columns_dict = {
        'code': '工号',
        'name': '姓名',
        'status': '状态',
        'telephone': '电话',
        'id': 'ID'
    }
    keys = ["code","name","status","telephone","id"]
    rows_data = []
    for item in data_json:
        row = {k:v for k,v in item.items() if k in keys}
        rows_data.append(row)
    df = pd.DataFrame(rows_data)
    df = df.rename(columns=columns_dict)
    df_json = df.to_dict(orient="records")
    return df_json