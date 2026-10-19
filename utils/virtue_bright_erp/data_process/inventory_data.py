"""
库存数据处理
    - inventory_data_process: 库存数据处理
"""


import pandas as pd


def inventory_data_process(
    data_json: list[dict],
    is_summary: bool = True
    ):
    """
    库存数据处理
    用以处理德明接口 inventory_report 返回的库存数据
    Args:
        data_json (list[dict]): 库存数据列表
        is_summary (bool): 是否汇总数据
    Returns:
        list[dict]: 处理后的库存数据
    """
    columns_dict = {
        'stockAndStoreName': '门店/仓库名称',
        'stockQtyInway': '在途库存数量',
        'dosage': '剂型',
        'proCode': '商品编码',
        'proTypeName': '商品类型',
        'stockAndStoreShort': '门店/仓库简称',
        'stockQty': '库存数量',
        'spec': '规格/型号',
        'stockCost': '库存成本额',
        'isImportName': '进口药品',
        'vendorCodeStock': '供应商编码',
        'baseUnit': '基本单位',
        'dataClassName': '所属分类',
        'licenseNumber': '批准文号',
        'proName': '商品名称',
        'availableStockQty': '可用库存数量',
        'barcode': '条形码',
        'proCommonName': '通用名称',
        'batchNo': '批号',
        'vendorNameStock': '供应商名称',
        'lockQty': '占用库存',
        'index': '序号',
        'stockAndStoreCode': '门店/仓库编码',
        'isSplitName': '是否拆零',
        'warehouseId': '仓库ID',
        'proId': '商品ID',
        'stockCostPrice': '成本单价',
        'producer': '生产企业',
        'shopType': '门店类型',
        # 'classTypeCode': 'gr_product_2068',
        # 'shopTypeDictCode': '1',
        # 'baseUnitDictCode': 'basic_unit_one',
        # 'productTypeCode': 'traditional_medicin',
        # 'dosageDictCode': '0109'
    }
    if is_summary:
        columns_names = ['商品编码', '通用名称', '商品名称', '规格/型号', '基本单位', '剂型', '批准文号', '条形码','生产企业','库存数量', '可用库存数量', '在途库存数量', '占用库存', '成本单价', '库存成本额', '商品类型', '所属分类', '进口药品','是否拆零']
    else:
        columns_names = ['门店/仓库编码', '仓库ID', '门店类型', '门店/仓库名称', '门店/仓库简称', '商品编码', '通用名称', '商品名称', '规格/型号', '基本单位', '剂型', '批准文号', '批号','条形码', '生产企业', '库存数量', '可用库存数量', '在途库存数量', '占用库存', '成本单价', '库存成本额', '商品类型', '所属分类', '供应商编码', '供应商名称', '是否拆零', '进口药品']

    df = pd.DataFrame(data_json)
    df = df.rename(columns=columns_dict)
    df_data = df.loc[:, columns_names]
    data_dict = df_data.to_dict(orient='records')
    return data_dict
