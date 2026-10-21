"""
机构数据
    - warehouse_information_data_process: 机构仓库信息数据处理-查询用
    - shop_info_data_process: 门店信息数据处理-查询用
    - region_tree_data_process: 区域树数据处理-查询用
"""

from typing import List
import pandas as pd


def warehouse_information_data_process(data_json: List[dict]):
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
    columns_names = ["租户ID", "企业ID", "企业名称", "门店/仓库编码", "门店/仓库名称",
                     "门店/仓库简称", "仓库ID", "仓库名称", "区域名称", "仓库类型", "座机号码", "仓库地址"]
    warehouse_type = {"sto": "门店仓", "dc": "企业仓库"}

    df = pd.DataFrame(data_json)
    df = df.rename(columns=columns_dict)
    df_data = df.loc[:, columns_names]
    df_data['仓库类型'] = df_data['仓库类型'].map(warehouse_type)
    data_dict = df_data.to_dict(orient='records')
    return data_dict


def shop_info_data_process(data_json: List[dict]):
    """
    门店信息数据处理-查询用
    用以处理德明接口 get_shop_info 返回的门店信息数据
    Args:
        data_json (list[dict]): 门店数据列表
    Returns:
        list[dict]: 处理后的门店数据
    """
    columns_dict = {
        'tenantId': '租户ID',
                    'code': '门店编码',
                    'name': '门店名称',
                    'nameAbc': '助记码',
                    'shortName': '门店简称',
                    'nationalMiCode': '国家定点医保机构码',
                    'miZoning': '就医地医保区划码',
                    'miOrganName': '定点医保机构名称',
                    'organId': '机构ID',
                    'oldCode': '旧门店编码',
                    'shopType': '门店类型',  # 1-直营,2-加盟
                    'status': '门店状态',  # 1-正常,0-停用
                    'enterpriseId': '企业ID',
                    "belongRegion": "区域ID",
                    'belongRegionCode': '区域编码',
                    'belongRegionLabel': '区域名称',
                    'telephone': '座机号码',
                    'address': '门店地址',
    }
    columns_names = ["租户ID", "企业ID", "机构ID", "门店编码", "门店名称", "门店简称", "助记码", "门店类型",
                     "门店状态", "区域ID", "区域编码", "区域名称", "座机号码", "门店地址", "国家定点医保机构码", "就医地医保区划码", "定点医保机构名称"]
    shop_type = {"1": "直营", "2": "加盟"}
    status = {1: "正常", 0: "停用"}

    df = pd.DataFrame(data_json)
    df = df.rename(columns=columns_dict)
    df_data = df.loc[:, columns_names]
    df_data['门店类型'] = df_data['门店类型'].map(shop_type)
    df_data['门店状态'] = df_data['门店状态'].map(status)
    data_dict = df_data.to_dict(orient='records')
    return data_dict


def _flatten_region_tree(nodes: list) -> list:
    """
    扁平化区域树
    """
    result = []
    for node in nodes or []:
        children = node.get("children") or []
        if children:
            node['is_leaf'] = False
        else:
            node['is_leaf'] = True
        item = {k: v for k, v in node.items() if k != "children"}
        result.append(item)
        result.extend(_flatten_region_tree(children))
    return result

def region_tree_data_process(data_json: List[dict]):
    """
    区域树数据处理-查询用
    """
    data_list = _flatten_region_tree(data_json)
    columns_dict = {
        'id': '区域ID',
        'code': '区域编码',
        'level': '区域层级',
        'name': '区域名称',
        'shopStatus': '区域状态',
        'parentId': '父区域ID',
        'parentName': '父区域名称',
        'is_leaf': '是否子节点',
        }
    columns_names = ['区域ID', '区域编码', '区域层级', '区域名称', '区域状态', '父区域ID', '父区域名称', '是否子节点']
    shop_status = {"1": '正常', "0": '停用'}

    df = pd.DataFrame(data_list)
    df = df.rename(columns=columns_dict)
    df_data = df.loc[:, columns_names]
    df_data['区域状态'] = df_data['区域状态'].map(shop_status)
    data_dict = df_data.to_dict(orient='records')
    return data_dict
    