"""
销售数据处理
    - shop_sale_data_process: 门店销售数据处理-查询用
    - shop_sale_summary_data_process: 门店销售汇总数据处理
    - store_goods_retail_data_process: 门店商品汇总报表数据处理
"""

from typing import List
import pandas as pd


def shop_sale_data_process(data_json: List[dict]):
    """
    门店销售数据处理-查询用
    用以处理德明接口 store_retail_report 返回的门店销售数据
    Args:
        data_json (list[dict]): 门店销售数据列表
    Returns:
        list[dict]: 处理后的门店销售数据
    """
    columns_dict = {
        'saleVipBillNo_2_0_0': '会员交易次数',
        'saleItemsRate': '动销率',  # 动销品项数/库存品项数
        'saleDailyAmt': '日均实收金额',  # 实收金额/期间天数
        'stoName': '门店名称',
        'saleAvaItems': '客品数',  # 销售数量/交易次数
        'stoIvItemQty': '库存品项数',
        'saleUnitPrice': '应收金额',
        'stoShortName': '门店简称',
        'saleOrderNo_2_0_0': '交易次数',
        # 'saleBillOrderNo_2_0_0': '交易次数',
        'saleDiscountRate': '折扣率',
        'saleAmt': '实收金额',
        # 'saleBillSaleAmt': '实收金额',
        'saleReferenceGross': '毛利额',
        'saleReferenceGrossRate': '毛利率',
        # 'saleBillSaleQty': '销售数量',
        'saleQty': '销售数量',
        'goodsTime': '客品次',
        'stoCode': '门店编码',
        'saleDate_2_0_0': '动销天数',
        'saleVipAmtRate': '会员销售占比',  # 会员实收金额/实收金额
        'stoSalesItemQtyCode_2_0_0': '动销品项数',
        # 'proCode_2_0_0': '动销品项数',
        # 'index': 1,
        'saleCost': '成本额',
        'saleDailyGross': '日均毛利额',  # 毛利额/期间天数
        'saleVipAmt': '会员实收金额',
        'saleItemPrice': '品单价',  # 实收金额/销售数量

        'saleAvaBillPrice': '客单价',  # 实收金额/交易次数
        'saleDailyBillCount': '日均交易次数',  # 交易次数/期间天数
        'shopType': '门店类型',
        # 'shopTypeDictCode': '1',
        'saleDiscount': '折扣金额',

        'saleVipBillQtyRate': '会员交易次数占比'  # 会员交易次数/交易次数
    }
    columns_names = ['门店编码', '门店名称', '门店简称', '门店类型', '销售数量', '应收金额', '实收金额', '成本额', '折扣金额', '折扣率', '毛利额', '毛利率', '交易次数', '品单价',
                     '客单价', '客品数', '客品次', '会员交易次数', '会员交易次数占比', '会员实收金额', '会员销售占比', '动销品项数', '库存品项数', '动销率', '动销天数', '日均实收金额', '日均毛利额', '日均交易次数']
    df = pd.DataFrame(data_json)
    df = df.rename(columns=columns_dict)
    df_data = df.loc[:, columns_names]
    data_dict = df_data.to_dict(orient='records')
    return data_dict


def shop_sale_summary_data_process(data_json: dict):
    """
    门店销售汇总数据处理
    用以处理德明接口 store_retail_report 返回的totalSummary字段数据
    Args:
        data_json (dict): totalSummary字段数据
    Returns:
        dict: 处理后的门店销售数据
    """
    columns_dict = {
        'saleVipBillNo_2_0_0': '会员交易次数',
        'saleItemsRate': '动销率',
        'saleDailyAmt': '日均实收金额',
        # 'saleBillSaleAmt': '实收金额',
        'saleAvaItems': '客品数',
        'stoIvItemQty': '库存品项数',
        'saleUnitPrice': '应收金额',
        'saleOrderNo_2_0_0': '交易次数',
        'saleDiscountRate': '折扣率',
        # 'saleBillItemQty': 11325.0,
        'saleAmt': '实收金额',
        'saleReferenceGross': '毛利额',
        'saleReferenceGrossRate': '毛利率',
        # 'saleBillSaleQty': '销售数量',
        'goodsTime': '客品次',
        # 'proCode_2_0_0': '动销品项数',
        'saleDate_2_0_0': '动销天数',
        'saleVipAmtRate': '会员销售占比',
        # 'saleDateParamDiff': 7.0,
        'stoSalesItemQtyCode_2_0_0': '动销品项数',
        # 'index': '合计',
        'saleCost': '成本额',
        'saleDailyGross': '日均毛利额',
        'saleVipAmt': '会员实收金额',
        'saleItemPrice': '品单价',
        # 'saleBillOrderNo_2_0_0': '交易次数',
        'saleAvaBillPrice': '客单价',
        'saleDailyBillCount': '日均交易次数',
        'saleDiscount': '折扣金额',
        'saleQty': '销售数量',
        'saleVipBillQtyRate': '会员交易次数占比'
    }
    columns_names = ['会员交易次数', '动销率', '日均实收金额', '客品数', '库存品项数', '应收金额', '交易次数', '折扣率', '实收金额', '毛利额', '毛利率', '客品次',
                     '动销天数', '会员销售占比', '动销品项数', '成本额', '日均毛利额', '会员实收金额', '品单价', '客单价', '日均交易次数', '折扣金额', '销售数量', '会员交易次数占比']
    df = pd.DataFrame([data_json])
    df = df.rename(columns=columns_dict)
    df_data = df.loc[:, columns_names]
    data_dict = df_data.to_dict(orient='records')
    return data_dict[0]


def store_goods_retail_data_process(
    data_json: list[dict],
    is_store_summary: bool = False,
):
    """
    门店商品汇总报表数据处理
    用以处理德明接口 store_goods_retail_report 返回的数据
    Args:
        data_json (list[dict]): 门店商品汇总报表数据列表
        is_store_summary (bool): 是否按门店汇总
    Returns:
        list[dict]: 处理后的门店商品汇总报表数据
    """
    columns_dict = {
        'dosage': '剂型',
        'proCode': '商品编码',
        'proTypeName': '商品类型',
        'stoName': '门店名称',
        'saleUnitPrice': '应收金额',
        'stoShortName': '门店简称',
        'saleOrderNo_2_0_0': '交易次数',
        'spec': '规格/型号',
        'dcIvQty': '总部库存',
        'baseUnit': '基本单位',
        'saleAmt': '实收金额',
        'saleReferenceGross': '毛利额',
        'dataClassName': '所属分类',
        'saleReferenceGrossRate': '毛利率',
        'licenseNumber': '批准文号',
        'proName': '商品名称',
        'stoCode': '门店编码',
        'proCommonName': '通用名称',
        'stoIvQty': '门店库存',
        'saleCost': '成本额',
        'producer': '生产企业',
        'shopType': '门店类型',
        'saleQty': '销售数量',
    }
    columns_names = ['门店编码', '门店名称', '门店简称', '门店类型', '商品编码', '通用名称', '商品名称', '规格/型号', '基本单位', '剂型',
                     '批准文号', '生产企业', '商品类型', '所属分类', '销售数量', '应收金额', '实收金额', '成本额', '毛利额', '毛利率', '交易次数', '门店库存', '总部库存']
    if not is_store_summary:
        remove_list = ['门店编码', '门店名称', '门店简称',]
        columns_names = [i for i in columns_names if i not in remove_list]
    df = pd.DataFrame(data_json)
    df = df.rename(columns=columns_dict)
    df_data = df.loc[:, columns_names]
    data_dict = df_data.to_dict(orient='records')
    return data_dict


def store_goods_retail_summary_data_process(data_json: dict):
    """
    门店商品汇总报表汇总数据处理
    用以处理德明接口 store_goods_retail_report 返回的totalSummary字段数据
    Args:
        data_json (dict): totalSummary字段数据
    Returns:
        dict: 处理后的门店商品汇总报表汇总数据
    """
    columns_dict = {'dcIvQty': '总部库存',
                    'saleAmt': '实收金额',
                    'saleDateParamDiff': '期间天数',
                    'saleReferenceGross': '毛利额',
                    'stoIvQty': '门店库存',
                    'saleReferenceGrossRate': '毛利率',
                    'saleUnitPrice': '应收金额',
                    'saleCost': '成本额',
                    'saleQty': '销售数量',
                    'saleOrderNo_2_0_0': '交易次数'}
    columns_names = ['总部库存', '实收金额', '期间天数', '毛利额',
                     '门店库存', '毛利率', '应收金额',  '成本额', '销售数量', '交易次数']
    df = pd.DataFrame([data_json])
    df = df.rename(columns=columns_dict)
    df_data = df.loc[:, columns_names]
    data_dict = df_data.to_dict(orient='records')
    return data_dict[0]