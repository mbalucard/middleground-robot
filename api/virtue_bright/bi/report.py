"""
商品模块
    - inventory_report: 库存明细报表
    - warehouse_information: 仓库信息
    - store_retail_report: 门店零汇总报表
    - store_goods_retail_report: 门店商品汇总报表
"""

from httpx import AsyncClient
from typing import Optional, List

from configs.api_config import deming_env
from api.virtue_bright.general_tools import timestamp, get_current_date, get_date_start_and_end_time
from utils.logger_manager import LoggerManager
from api.virtue_bright.bi.report_args import report_field_args
logger = LoggerManager.get_logger(name="bi_report")

yaoud_env = deming_env
base_url = f"{yaoud_env['url']}/bi/report"
TTL = yaoud_env["timeout"]


async def inventory_report(
        authorization: str,
        tenant_id: Optional[int] = None,
        current: int = 1,
        size: int = 20,
        codes: List[str] = [],
        mnemonic_code: Optional[str] = None,
        shop_type: List[str] = [],
        warehouse_id: List[str] = [],
        is_summary: bool = True,):
    """
    库存报表
    Args:
        authorization (str): 授权token
        tenant_id (Optional[int]): 租户ID
        current (int): 当前页码
        size (int): 每页大小
        codes (List[str]): 商品编码
        mnemonic_code (Optional[str]): 商品助记码
        shop_type (List[str]): 门店类型, 字段为[] 可查询总公司仓库库存
            - 1-直营, 2-加盟 
        warehouse_id (List[str]): 仓库ID
            - 可在 warehouse_information 接口中查询
        is_summary (bool): 是否按门店汇总
    Returns:
        dict: 库存报表数据
    """
    if is_summary:
        report_code = 63
    else:
        report_code = 61
    report_args = report_field_args(report_code)
    orderFields = report_args.get("orderFields")
    reportFieldIds = report_args.get("reportFieldIds")

    url = f"{base_url}/query/{report_code}/list"
    headers = {
        "authorization": authorization,  # 必须
        "client-tom": "Y",
        "tenant-id": str(tenant_id) if tenant_id else "",
    }
    conditions = [
        # 是否显示0库存，以下为不显示
        {
            "val": 0,
            "field": "F_1_623_F",
            "rule": "ne"
        },
        # 商品编码
        {
            "field": "F_1_3_F",
            "rule": "in",
            "val": codes
        },
        # 商品拼音码，必须大写
        {
            "field": "F_1_7_F", "rule": "like", "val": mnemonic_code
        },
        # 门店类型：1-直营，2-加盟
        {"field": "F_1_75_F", "rule": "in", "val": shop_type},
        # 仓库ID
        {"field": "F_1_600_F", "rule": "in", "val": warehouse_id}
    ]

    payload = {
        "current": current,
        "size": size,
        "conditions": conditions,
        "orderFields": orderFields,
        "reportFieldIds": reportFieldIds,
        "reportId": report_code
    }

    async with AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload, timeout=TTL)

    result = response.json()

    data = await _result_data_processing(
        result=result,
        authorization=authorization,
        request_dict=payload,
        tenant_id=tenant_id,
    )
    result['data'] = data
    return result


async def _report_count(
        authorization: str,
        request_dict: dict,
        tenant_id: Optional[int] = None,):
    """
    库存报表条目数
    Args:
        authorization (str): 授权token
        request_dict (dict): 请求参数
        tenant_id (Optional[int]): 租户ID
    Returns:
        dict: 库存报表条目数
    """
    url = f"{base_url}/query/{request_dict.get('reportId')}/count"
    headers = {
        "authorization": authorization,  # 必须
        "client-tom": "Y",
        "tenant-id": str(tenant_id) if tenant_id else "",
    }
    payload = {
        "conditions": request_dict.get('conditions'),
        "reportFieldIds": request_dict.get('reportFieldIds'),
    }
    async with AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload, timeout=TTL)
    return response.json()


async def _report_sum(
        authorization: str,
        request_dict: dict,
        tenant_id: Optional[int] = None,):
    """
    库存报表合计
    Args:
        authorization (str): 授权token
        request_dict (dict): 请求参数
        tenant_id (Optional[int]): 租户ID
    Returns:
        dict: 库存报表合计
    """
    url = f"{base_url}/query/{request_dict.get('reportId')}/sum"
    headers = {
        "authorization": authorization,  # 必须
        "client-tom": "Y",
        "tenant-id": str(tenant_id) if tenant_id else "",
    }
    payload = {
        "conditions": request_dict.get('conditions'),
        "reportFieldIds": request_dict.get('reportFieldIds'),
    }
    async with AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload, timeout=TTL)
    return response.json()


async def _result_data_processing(
        result: dict,
        authorization: str,
        request_dict: dict,
        tenant_id: Optional[int] = None,):
    """
    报表结果数据处理
    #! 就是因为写接口的人偷懒不写total和pages，所以这里需要自己计算
    Args:
        result (dict): 结果数据
        authorization (str): 授权token
        request_dict (dict): 请求参数
        tenant_id (Optional[int]): 租户ID
    Returns:
        dict: 报表结果数据
    """
    data = result.get('data')
    if isinstance(data, dict):
        if data.get('records'):
            if data.get("total") == 0:
                count_data = await _report_count(
                    authorization=authorization,
                    request_dict=request_dict,
                    tenant_id=tenant_id
                )
                total = count_data.get('data').get('total')

                if total > 0:
                    data['total'] = total
                    data['pages'] = total // request_dict.get('size', 1) + 1

            # 计算总合计
            if not data.get("totalSummary"):
                sum_data = await _report_sum(
                    authorization=authorization,
                    request_dict=request_dict,
                    tenant_id=tenant_id,
                )
                total_summary = sum_data.get('data').get('totalSummary')
                if total_summary:
                    data['totalSummary'] = total_summary

            if data.get('size') != request_dict.get('size'):
                data['current'] = request_dict.get('current')
                data['size'] = request_dict.get('size')
    return data


async def warehouse_information(
        authorization: str,
        tenant_id: Optional[int] = None,
        current: int = 1,
        size: int = 20,
        keyword: Optional[str] = None,):
    """
    仓库信息
    Args:
        authorization (str): 授权token
        tenant_id (Optional[int]): 租户ID
        current (int): 当前页码
        size (int): 每页大小
        keyword (Optional[str]): 模糊查询
            - 门店名称/简称、门店编码、助记码
    Returns:
        dict: 仓库信息数据
    """
    url = f"{base_url}/listDcAndStoInfo"
    headers = {
        "authorization": authorization,  # 必须
        "client-tom": "Y",
        "tenant-id": str(tenant_id) if tenant_id else "",
    }
    params = {
        "current": current,
        "size": size,
        "keyword": keyword,
        "status": 0,  # 0-启用，1-禁用
        "_t": timestamp(),
    }
    async with AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params, timeout=TTL)
    return response.json()


async def store_retail_report(
        authorization: str,
        start_date: str,
        end_date: str,
        store_code: List[str] = [],
        store_type: List[str] = [],
        belongRegion: List[str] = [],
        tenant_id: Optional[int] = None,
        current: int = 1,
        size: int = 20,):
    """
    门店零汇总报表
    Args:
        authorization (str): 授权token
        start_date (str): 开始日期
            - 格式为YYYY-MM-DD
        end_date (str): 结束日期
            - 格式为YYYY-MM-DD
        store_code (List[str]): 门店编码
        store_type (List[str]): 门店类型
            - 1-直营, 2-加盟
        belongRegion (List[str]): 直属区域ID
        tenant_id (Optional[int]): 租户ID
        current (int): 当前页码
        size (int): 每页大小
    Returns:
        dict: 门店零售报表数据
    """
    report_code = 32
    url = f"{base_url}/query/{report_code}/list"
    headers = {
        "authorization": authorization,  # 必须
        "client-tom": "Y",
        "tenant-id": str(tenant_id) if tenant_id else "",
    }
    conditions = [
        # 销售日期
        {
            "field": "F_1_3973_F",
            "rule": "between",
            "val": [
                start_date,
                end_date
            ]
        },
        # 门店编码
        {
            "field": "F_1_71_F",
            "rule": "in",
            "val": store_code
        },
        # 门店类型
        {
            "field": "F_1_75_F",
            "rule": "in",
            "val": store_type
        },
        # 商品类型
        {
            "field": "F_1_4008_F",
            "rule": "in",
            "val": []
        },
        # 直属区域
        {
            "field": "F_1_1154_F",
            "rule": "in",
            "val": belongRegion
        }
    ]
    report_args = report_field_args(report_code)
    orderFields = report_args.get("orderFields")
    reportFieldIds = report_args.get("reportFieldIds")
    payload = {
        "current": current,
        "size": size,
        "conditions": conditions,
        "orderFields": orderFields,
        "reportFieldIds": reportFieldIds,
        "reportId": report_code
    }
    async with AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload, timeout=TTL)
    result = response.json()
    data = await _result_data_processing(
        result=result,
        authorization=authorization,
        request_dict=payload,
        tenant_id=tenant_id,
    )
    result['data'] = data
    return result


async def store_goods_retail_report(
        authorization: str,
        start_date: str,
        end_date: str,
        store_code: List[str] = [],
        store_type: List[str] = [],
        belongRegion: List[str] = [],
        goods_code: List[str] = [],
        tenant_id: Optional[int] = None,
        is_store_summary: bool = False,
        current: int = 1,
        size: int = 20,):
    """
    门店商品汇总报表
    Args:
        authorization (str): 授权token
        start_date (str): 开始日期
            - 格式为YYYY-MM-DD
        end_date (str): 结束日期
            - 格式为YYYY-MM-DD
        store_code (List[str]): 门店编码列表
        store_type (List[str]): 门店类型
            - 1-直营, 2-加盟
        belongRegion (List[str]): 直属区域ID
        goods_code (List[str]): 商品编码列表
        tenant_id (Optional[int]): 租户ID
        is_store_summary (bool): 是否按门店汇总
        current (int): 当前页码
        size (int): 每页大小
    Returns:
        dict: 门店商品汇总报表数据
    """
    report_code = 31
    url = f"{base_url}/query/{report_code}/list"
    headers = {
        "authorization": authorization,  # 必须
        "client-tom": "Y",
        "tenant-id": str(tenant_id) if tenant_id else "",
    }
    conditions = [
        # 日期
        {
            "field": "F_1_3973_F",
            "rule": "between",
            "val": [
                start_date,
                end_date
            ]
        },
        # 门店编码
        {
            "field": "F_1_71_F",
            "rule": "in",
            "val": store_code
        },
        # 区域
        {
            "field": "F_1_1154_F",
            "rule": "in",
            "val": belongRegion
        },
        # 商品编码
        {
            "field": "F_1_4002_F",
            "rule": "in",
            "val": goods_code
        },
        # 门店类型
        {
            "field": "F_1_75_F",
            "rule": "in",
            "val": store_type
        }
    ]
    report_args = report_field_args(
        report_code=report_code,
        is_summary=is_store_summary,
    )
    orderFields = report_args.get("orderFields")
    reportFieldIds = report_args.get("reportFieldIds")
    payload = {
        "current": current,
        "size": size,
        "conditions": conditions,
        "orderFields": orderFields,
        "reportFieldIds": reportFieldIds,
        "reportId": report_code
    }
    async with AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload, timeout=TTL)
    result = response.json()
    data = await _result_data_processing(
        result=result,
        authorization=authorization,
        request_dict=payload,
        tenant_id=tenant_id,
    )
    result['data'] = data
    return result


async def inventory_audit_summary_report(
        authorization: str,
        start_date: str,
        end_date: str,
        tenant_id: Optional[int] = None,
        current: int = 1,
        size: int = 20,
        take_stock_type: List[str] = [],
        warehouse_id: List[str] = [],
        profit_loss_status: List[str] = [],
        is_profit_loss: List[str] = ["是"],
        store_type: List[str] = ["1"],
        goods_codes: List[str] = [],
        is_store_summary: bool = True,):
    """
    库存盘点汇总报表
    Args:
        authorization (str): 授权token
        start_date (str): 制单开始日期
            - 格式为YYYY-MM-DD
        end_date (str): 制单结束日期
            - 格式为YYYY-MM-DD
        tenant_id (Optional[int]): 租户ID
        current (int): 当前页码
        size (int): 每页大小
        take_stock_type (List[str]): 盘点类型
            - 1-抽盘 2-全盘
        warehouse_id (List[str]): 仓库ID
        profit_loss_status (List[str]): 盈亏状态
            - 不盈不亏 盘盈 盘亏
        is_profit_loss (List[str]): 是否产生盈亏
            - 是 否
        store_type (List[str]): 门店类型
            - 1-直营 2-加盟
        goods_codes (List[str]): 商品编码列表
        is_store_summary (bool): 是否按门店汇总
    Returns:
        dict: 库存盘点汇总报表数据
    """
    report_code = 185
    url = f"{base_url}/query/{report_code}/list"
    headers = {
        "authorization": authorization,  # 必须
        "client-tom": "Y",
        "tenant-id": str(tenant_id) if tenant_id else "",
    }
    report_args = report_field_args(report_code, is_summary=is_store_summary)
    orderFields = report_args.get("orderFields")
    reportFieldIds = report_args.get("reportFieldIds")
    conditions = [
        {  # 制单日期
            "field": "F_1_1895_F",
            "rule": "between",
            "val": [
                start_date,
                end_date
            ]
        },
        {  # 盘点类型 1-抽盘 2-全盘
            "field": "F_1_1903_F",
            "rule": "in",
            "val": take_stock_type
        },
        {  # 仓库ID
            "field": "F_1_600_F",
            "rule": "in",
            "val": warehouse_id
        },
        {  # 是否产生盈亏 是 否
            "field": "F_3_107995_F",
            "rule": "in",
            "val": is_profit_loss
        },
        {  # 盈亏状态 ["不盈不亏", "盘盈", "盘亏"]
            "field": "F_3_120733_F",
            "rule": "in",
            "val": profit_loss_status
        },
        {  # 门店类型 1-直营 2-加盟
            "field": "F_1_75_F",
            "rule": "in",
            "val": store_type
        },
        {  # 商品编码列表
            "field": "F_1_3_F",
            "rule": "in",
            "val": goods_codes
        }
    ]
    payload = {
        "current": current,
        "size": size,
        "conditions": conditions,
        "orderFields": orderFields,
        "reportFieldIds": reportFieldIds,
        "reportId": report_code
    }
    async with AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload, timeout=TTL)
    result = response.json()
    data = await _result_data_processing(
        result=result,
        authorization=authorization,
        request_dict=payload,
        tenant_id=tenant_id,
    )
    result['data'] = data
    return result
