"""
订单管理
    - 零售订单列表-出库: order_page
    - 零售订单详情-出库: get_order_detail
"""


from httpx import AsyncClient
from typing import Optional, List

from configs.api_config import deming_env
from api.virtue_bright.general_tools import timestamp, get_current_date, get_date_start_and_end_time

yaoud_env = deming_env
base_url = f"{yaoud_env['url']}/oms/order"
TTL = yaoud_env["timeout"]


async def order_page(
        authorization: str,
        tenant_id: Optional[int] = None,
        current: int = 1,
        size: int = 20,
        buyerOrderTimeStart: Optional[str] = None,
        buyerOrderTimeEnd: Optional[str] = None,
        shopCodes: Optional[List[str]] = None,
        storeCode: Optional[str] = None,
        yaoudGoodsCode: Optional[str] = None,
        orderId: Optional[str] = None,
        isOutbound: Optional[int] = None,
        isFlag: Optional[int] = None,
        orderSources: Optional[List[str]] = None,
        orderTypes: Optional[List[str]] = None,
        status: Optional[int] = None,
        deliveryCode: Optional[int] = None,
        orderErrorTypes: Optional[List[str]] = None,
        thirdpartyOrderId: Optional[str] = None,
        buyerName: Optional[str] = None,
        buyerTelephone: Optional[str] = None,
        shippingAddressRecipient: Optional[str] = None,
        shippingAddressPhone: Optional[str] = None,
        orderSubType: Optional[int] = 1,) -> dict:
    """
    获取零售订单列表-出库
    Args:
        authorization (str): 认证信息
        tenant_id (int, None): 租户ID. Defaults to None.
        current (int): 当前页. Defaults to 1.
        size (int): 每页条目数最大100. Defaults to 20.
        buyerOrderTimeStart (Optional[str]): 下单开始时间. Defaults to 当前日期0点.
            - 日期格式为yyyy-MM-dd HH:mm:ss
        buyerOrderTimeEnd (Optional[str]): 下单结束时间. Defaults to 当前日期23:59:59.
            - 日期格式为yyyy-MM-dd HH:mm:ss
        shopCodes (Optional[List[str]]): 店铺编码列表. Defaults to None.
        storeCode (Optional[str]): 门店编码. Defaults to None.
        yaoudGoodsCode (Optional[str]): 企业商品编码. Defaults to None.
        orderId (Optional[str]): 系统单号. Defaults to None.
        isOutbound (Optional[int]): 是否出库. Defaults to None.
            - 可选值：0-未出库，1-已出库
        isFlag (Optional[int]): 是否标记. Defaults to None.
            - 可选值：0-未标记，1-已标记
        orderSources (Optional[List[str]]): 订单来源列表. Defaults to None.
            - 可在 list_order_source 中获取"
        orderTypes (Optional[List[str]]): 订单类型列表. Defaults to None.
            - 可在 dict_item_list 中获取 keyword="销售订单类型"
        status (Optional[int]): 订单状态. Defaults to None.
            - 可选值：1-待配货，2-待确认，3-待发货，4-待自提，5-部分发货，6-已发货，7-已自提，9-已关闭
        deliveryCode (Optional[int]): 配送方式. Defaults to None.
            - 可选值：1-门店自提，2-骑手配送，3-快递配送
        orderErrorTypes (Optional[List[str]]): 订单异常类型列表. Defaults to None.
            - 2:系统-缺货 , 11:系统-退款 , 31: 系统-刷单, 40:系统-盘点 , 15:系统-未对码 , 32:系统-已路由 , 33:系统-快递停发 , 5:系统-修改地址
            - 仅针对线上订单
        thirdpartyOrderId (Optional[str]): 第三方单号. Defaults to None.
        buyerName (Optional[str]): 下单人姓名. Defaults to None.
            - 仅针对线上订单
        buyerTelephone (Optional[str]): 下单人手机号. Defaults to None.
            - 仅针对线上订单
        shippingAddressRecipient (Optional[str]): 收货人姓名. Defaults to None.
            - 仅针对线上订单
        shippingAddressPhone (Optional[str]): 收货人手机号. Defaults to None.
            - 仅针对线上订单
        orderSubType (Optional[int]): 订单子类型，作用未知. Defaults to 1.
    Returns:
        dict: 零售订单列表
    """
    url = f"{base_url}/getPage"
    headers = {
        "Authorization": authorization,
        "client-tom": "Y",
        "tenant-id": str(tenant_id) if tenant_id else "",
    }
    if buyerOrderTimeStart:
        start_time = get_date_start_and_end_time(buyerOrderTimeStart)
    else:
        taday = get_current_date()
        start_time = get_date_start_and_end_time(taday)
    if buyerOrderTimeEnd:
        end_time = get_date_start_and_end_time(buyerOrderTimeEnd)
    else:
        end_time = None
    params = {
        "current": current,
        "size": size,
        # 开始时间,必填
        "buyerOrderTimeStart": start_time['start_time'] if start_time else None,
        # 结束时间
        "buyerOrderTimeEnd": end_time['end_time'] if end_time else None,
        "shopCodes": shopCodes,  # 店铺编码  List["str"]
        "storeCode": storeCode,  # 门店编码 str
        "yaoudGoodsCode": yaoudGoodsCode,  # 企业商品编码
        "orderId": orderId,  # 系统单号
        "isOutbound": isOutbound,  # 是否出库(0:未出库，1:已出库)
        "isFlag": isFlag,  # 是否标记(0:未标记，1:已标记)
        "orderSources": orderSources,
        "orderSubType": 1,  # ? 订单子类型，作用未知
        "_t": timestamp(),
        #! 以下参数仅针对线上订单
        "orderTypes": orderTypes,
        "status": status,
        "deliveryCode": deliveryCode,
        "orderErrorTypes": orderErrorTypes,
        "thirdpartyOrderId": thirdpartyOrderId,  # 第三方单号
        "buyerName": buyerName,  # 下单人姓名
        "buyerTelephone": buyerTelephone,  # 下单人手机号
        "shippingAddressRecipient": shippingAddressRecipient,  # 收货人姓名
        "shippingAddressPhone": shippingAddressPhone,  # 收货人手机号
    }
    async with AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params, timeout=TTL)
    return response.json()


async def get_order_detail(
        authorization: str,
        order_id: str,
        tenant_id: Optional[int] = None,) -> dict:
    """
    获取零售订单详情-出库
    Args:
        authorization (str): 认证信息
        order_id (str): 订单ID
        tenant_id (int, None): 租户ID. Defaults to None.
    Returns:
        dict: 订单详情
    """
    url = f"{base_url}/getOrderDetail/{order_id}"
    headers = {
        "Authorization": authorization,
        "client-tom": "Y",
        "tenant-id": str(tenant_id) if tenant_id else "",
    }
    params = {
        "_t": timestamp(),
    }
    async with AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params, timeout=TTL)
    return response.json()


async def list_order_source(
    authorization: str,
    tenant_id: Optional[int] = None,) -> dict:
    """
    获取订单来源列表
    Args:
        authorization (str): 认证信息
        tenant_id (int, None): 租户ID. Defaults to None.
    Returns:
        dict: 订单来源列表
    """
    url = f"{base_url}/listOrderSource"
    headers = {
        "Authorization": authorization,
        "client-tom": "Y",
        "tenant-id": str(tenant_id) if tenant_id else "",
    }
    payload = {}
    async with AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload, timeout=TTL)
    return response.json()




if __name__ == "__main__":
    import asyncio

    authorization = "Bearer new_d58dec78-1278-4152-bad5-86f36bf6ff31"
    async def main():
        data = await list_order_source(
            authorization=authorization,
        )
        print(data)
    asyncio.run(main())