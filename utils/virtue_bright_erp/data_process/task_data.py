"""
任务数据处理
    - task_brief_data_process: 任务简要数据处理
"""

from typing import List
import pandas as pd


def task_brief_data_process(data_json: List[dict]):
    """
    任务简要数据处理
    用于清洗 get_task_todo_list 返回的data字段中records部分数据
    Args:
        data_json (List[dict]): get_task_todo_list 返回的data字段中records部分数据
    Returns:
        List[dict]: 清洗后的数据
    """

    keys = ["taskId", "instanceId", "processDefName", "orderId", "contentOne",
            "contentTwo", "organName", "extendInfo", "createTime", 'startTime', "resultName", "taskName"]
    columns_dict = {
        'taskId': '编号',
        'instanceId': '编号',  # 类型为 initiated 时特有
        'processDefName': '事项类型',
        'createTime': '发起时间',
        'startTime': '发起时间',  # 类型为 initiated 时特有
        'tenantId': '租户ID',
        'enterpriseId': '企业ID',
        'orgId': '机构ID',
        'createId': '创建人ID',
        'createName': '创建人姓名',
        'orderId': '业务单据号',
        'resultName': '审批状态',
        'taskName': '审批状态',  # 类型为 initiated 时特有
        'organName': '登陆机构',
        'contentOne': '内容一',
        'contentTwo': '内容二'
    }
    # 找到目标数据
    rows_data = []
    for item in data_json:
        item_dict = {}
        for k, v in item.items():
            if k in keys:
                if k == "extendInfo":
                    item_dict["tenantId"] = v.get("tenantId")
                    item_dict["enterpriseId"] = v.get("enterpriseId")
                    item_dict["orgId"] = v.get("orgId")
                    item_dict["createId"] = v.get("createId")
                    item_dict["createName"] = v.get("createName")
                    continue
                item_dict[k] = v
        rows_data.append(item_dict)
    # 数据清洗
    df = pd.DataFrame(rows_data)
    df = df.rename(columns=columns_dict)
    df_json = df.to_dict(orient="records")
    return df_json
