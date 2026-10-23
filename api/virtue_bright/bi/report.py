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
    is_summary: bool = True,
):
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
        "reportFieldIds": reportFieldIds
    }

    async with AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload, timeout=TTL)

    data_dict = response.json()
    #! 就是因为写接口的人偷懒不写total和pages，所以这里需要自己计算
    if data_dict.get("data").get("records"):
        if data_dict.get("data").get("total") == 0:
            count_data = await _report_count(
                authorization=authorization,
                conditions=conditions,
                reportFieldIds=reportFieldIds,
                tenant_id=tenant_id,
                report_code=report_code,
            )
            total = count_data.get("data").get("total")

            if total > 0:
                data_dict['data']['total'] = total
                data_dict['data']['pages'] = total // size + 1

        # 计算总合计
        if not data_dict.get("data").get("totalSummary"):
            sum_data = await _report_sum(
                authorization=authorization,
                conditions=conditions,
                reportFieldIds=reportFieldIds,
                tenant_id=tenant_id,
                report_code=report_code,
            )
            total_summary = sum_data.get("data").get("totalSummary")
            if total_summary:
                data_dict['data']['totalSummary'] = sum_data.get(
                    "data").get("totalSummary")

    if data_dict['data']['size'] != size:
        data_dict['data']['current'] = current
        data_dict['data']['size'] = size

    return data_dict


async def _report_count(
        authorization: str,
        report_code: str,
        conditions: List[dict],
        reportFieldIds: List[str],
        tenant_id: Optional[int] = None,):
    """
    库存报表条目数
    Args:
        authorization (str): 授权token
        report_code (str): 报表代码
        conditions (List[dict]): 查询条件
        reportFieldIds (List[str]): 报表字段ID
        tenant_id (Optional[int]): 租户ID
    Returns:
        dict: 库存报表条目数
    """
    url = f"{base_url}/query/{report_code}/count"
    headers = {
        "authorization": authorization,  # 必须
        "client-tom": "Y",
        "tenant-id": str(tenant_id) if tenant_id else "",
    }
    payload = {
        "conditions": conditions,
        "reportFieldIds": reportFieldIds,
    }
    async with AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload, timeout=TTL)
    return response.json()


async def _report_sum(
        authorization: str,
        report_code: str,
        conditions: List[dict],
        reportFieldIds: List[str],
        tenant_id: Optional[int] = None,):
    """
    库存报表合计
    Args:
        authorization (str): 授权token
        conditions (List[dict]): 查询条件
        reportFieldIds (List[str]): 报表字段ID
        tenant_id (Optional[int]): 租户ID
        report_code (str): 报表代码
    Returns:
        dict: 库存报表合计
    """
    url = f"{base_url}/query/{report_code}/sum"
    headers = {
        "authorization": authorization,  # 必须
        "client-tom": "Y",
        "tenant-id": str(tenant_id) if tenant_id else "",
    }
    payload = {
        "conditions": conditions,
        "reportFieldIds": reportFieldIds,
    }
    async with AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload, timeout=TTL)
    return response.json()


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
    size: int = 20,
):
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
        "reportFieldIds": reportFieldIds
    }
    async with AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload, timeout=TTL)
    data_json = response.json()

    if data_json.get("data").get("records"):
        if data_json.get("data").get("total") == 0:
            count_data = await _report_count(
                authorization=authorization,
                conditions=conditions,
                reportFieldIds=reportFieldIds,
                tenant_id=tenant_id,
                report_code=report_code,
            )
            total = count_data.get("data").get("total")
            if total > 0:
                data_json['data']['total'] = total
                data_json['data']['pages'] = total // size + 1

        if not data_json.get("data").get("totalSummary"):
            sum_data = await _report_sum(
                authorization=authorization,
                conditions=conditions,
                reportFieldIds=reportFieldIds,
                tenant_id=tenant_id,
                report_code=report_code,
            )
            total_summary = sum_data.get("data").get("totalSummary")
            if total_summary:
                data_json['data']['totalSummary'] = sum_data.get(
                    "data").get("totalSummary")
    if data_json['data']['size'] != size:
        data_json['data']['current'] = current
        data_json['data']['size'] = size

    return data_json


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
    size: int = 20,
):
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
        "reportFieldIds": reportFieldIds
    }
    async with AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload, timeout=TTL)
    data_json = response.json()

    if data_json.get("data").get("records"):
        if data_json.get("data").get("total") == 0:
            count_data = await _report_count(
                authorization=authorization,
                conditions=conditions,
                reportFieldIds=reportFieldIds,
                tenant_id=tenant_id,
                report_code=report_code,
            )
            total = count_data.get("data").get("total")
            if total > 0:
                data_json['data']['total'] = total
                data_json['data']['pages'] = total // size + 1

        if not data_json.get("data").get("totalSummary"):
            sum_data = await _report_sum(
                authorization=authorization,
                conditions=conditions,
                reportFieldIds=reportFieldIds,
                tenant_id=tenant_id,
                report_code=report_code,
            )
            total_summary = sum_data.get("data").get("totalSummary")
            if total_summary:
                data_json['data']['totalSummary'] = sum_data.get(
                    "data").get("totalSummary")
    if data_json['data']['size'] != size:
        data_json['data']['current'] = current
        data_json['data']['size'] = size
    return data_json
