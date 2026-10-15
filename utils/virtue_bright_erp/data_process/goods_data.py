"""
商品数据处理
    - goods_data_process: 商品数据处理-查询用
"""
import pandas as pd


def goods_data_process(data_json: list[dict]) -> list[dict]:
    """
    商品数据处理-查询用
    用以处理德明接口 goods_page_list 返回的商品数据
    Args:
        data_json (list[dict]): 商品数据列表
    Returns:
        list[dict]: 处理后的商品数据
    """
    columns_dict = {
        "code": "商品编码",
        "commonName": "通用名称",
        "name": "商品名称",
        "spec": "规格/型号",
        "baseUnitName": "基本单位",
        "dosageName": "剂型",
        "producer": "生产企业",
        "licenseNumber": "批准文号",
        "barcode": "条形码",
        "productTypeName": "商品类型",
        "classTypeName": "所属分类"
    }
    columns_names = ["商品编码", "通用名称", "商品名称", "规格/型号","基本单位", "剂型", "生产企业", "批准文号", "条形码", "商品类型", "所属分类"]

    df = pd.DataFrame(data_json)
    df = df.rename(columns=columns_dict)
    df_data = df.loc[:, columns_names]
    data_dict = df_data.to_dict(orient='records')
    return data_dict