"""
库存数据处理
    - inventory_data_process: 库存数据处理
    - inventory_audit_data_process: 库存盘点数据处理
"""


import pandas as pd


def inventory_data_process(
        data_json: list[dict],
        is_summary: bool = True):
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
        columns_names = ['商品编码', '通用名称', '商品名称', '规格/型号', '基本单位', '剂型', '批准文号', '条形码', '生产企业',
                         '库存数量', '可用库存数量', '在途库存数量', '占用库存', '成本单价', '库存成本额', '商品类型', '所属分类', '进口药品', '是否拆零']
    else:
        columns_names = ['门店/仓库编码', '仓库ID', '门店类型', '门店/仓库名称', '门店/仓库简称', '商品编码', '通用名称', '商品名称', '规格/型号', '基本单位', '剂型', '批准文号',
                         '批号', '条形码', '生产企业', '库存数量', '可用库存数量', '在途库存数量', '占用库存', '成本单价', '库存成本额', '商品类型', '所属分类', '供应商编码', '供应商名称', '是否拆零', '进口药品']

    df = pd.DataFrame(data_json)
    df = df.rename(columns=columns_dict)
    df_data = df.loc[:, columns_names]
    data_dict = df_data.to_dict(orient='records')
    return data_dict


def inventory_audit_data_process(
        data_json: list[dict],
        is_summary: bool = True):
    """
    库存盘点汇总数据处理
    用以处理德明接口 inventory_audit_summary_report 返回的库存盘点汇总数据
    Args:
        data_json (list[dict]): 库存盘点汇总数据列表
        is_summary (bool): 是否汇总数据
    Returns:
        list[dict]: 处理后的库存盘点汇总数据
    """
    columns_dict = {
        'dosage': '剂型',
        'proCommonName': '通用名称',
        'costIfProfitLoss': '是否产生盈亏',
        'proCode': '商品编码',
        'ivOutQty': '出库数量',
        'inventoryQuantity': '盘点数量',
        'ivInQty': '入库数量',
        'profitLossQuantity': '盈亏数量',
        'spec': '规格/型号',
        'profitLossCostAmt': '盈亏成本额',
        'baseUnit': '基本单位',
        'snapshotQuantity': '账面库存',
        'dataClassName': '所属分类',
        'producer': '生产企业',
        'costProfitLossStatus': '盈亏状态',  # 针对盈亏成本额的盈亏状态
        'licenseNumber': '批准文号',
        'proName': '商品名称',
        'shopType': '门店类型',
        'warehouseId': '仓库ID',
        'oneRegion': '直属区域',
        'stockAndStoreName': '门店/仓库名称',
        'stockAndStoreShort': '门店/仓库简称',
        'stockAndStoreCode': '门店/仓库编码',
        'ivObjectId_2_0_0': '盘点品相数',
        'oneRegionCode': '区域ID',
        'snapshotCost': '账面库存成本额',
        'stockCost': '盘点库存成本额',
    }
    if is_summary:
        columns_names = ['门店类型', '区域ID', '直属区域', '门店/仓库编码', '仓库ID', '门店/仓库名称', '门店/仓库简称', '盘点品相数',
                         '账面库存', '出库数量', '入库数量', '盘点数量', '盈亏数量', '账面库存成本额', '盘点库存成本额', '盈亏成本额', '盈亏状态']
    else:
        columns_names = ['门店类型', '商品编码', '通用名称', '商品名称', '规格/型号', '剂型', '基本单位', '批准文号',
                         '生产企业', '所属分类', '账面库存', '出库数量', '入库数量', '盘点数量', '盈亏数量', '盈亏成本额', '盈亏状态']
    df = pd.DataFrame(data_json)
    df = df.rename(columns=columns_dict)
    df_data = df.loc[:, columns_names]
    data_dict = df_data.to_dict(orient='records')
    return data_dict


def inventory_audit_summary_data_process(
        data_json: dict,
        is_summary: bool = True):
    """
    库存盘点汇总数据处理
    用以处理德明接口 inventory_audit_summary_report 返回的totalSummary数据
    Args:
        data_json (list[dict]): totalSummary数据列表
        is_summary (bool): 是否汇总数据
    Returns:
        list[dict]: 处理后的totalSummary数据
    """
    columns_dict = {
        'snapshotQuantity': "账面库存数量",
        'snapshotCost': "账面库存成本额",
        'ivOutQty': "出库数量",
        'inventoryQuantity': "盘点数量",
        'ivInQty': "入库数量",
        'costProfitLossStatus': "盈亏状态",
        'ivObjectId_2_0_0': "盘点品相数",
        'profitLossQuantity': "盈亏数量",
        'stockCost': "盘点库存成本额",
        'profitLossCostAmt': "盈亏成本额"
    }
    if is_summary:
        columns_names = ["账面库存数量", "账面库存成本额", "出库数量", "入库数量",
                         "盘点数量", "盈亏状态", "盘点品相数", "盈亏数量", "盘点库存成本额", "盈亏成本额"]
    else:
        columns_names = ["账面库存数量", "出库数量", "入库数量", "盘点数量", "盈亏数量", "盈亏成本额"]
    df = pd.DataFrame([data_json])
    df = df.rename(columns=columns_dict)
    df_data = df.loc[:, columns_names]
    data_dict = df_data.to_dict(orient='records')
    return data_dict[0] if data_dict else {}
