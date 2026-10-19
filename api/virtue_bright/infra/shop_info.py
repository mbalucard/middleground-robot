"""
门店信息模块

"""

from httpx import AsyncClient
from typing import Optional, List

from configs.api_config import deming_env
from api.virtue_bright.general_tools import timestamp, get_current_date, get_date_start_and_end_time
from utils.logger_manager import LoggerManager

logger = LoggerManager.get_logger(name="shop_info")


yaoud_env = deming_env
base_url = f"{yaoud_env['url']}/infra/shopinfo"
TTL = yaoud_env["timeout"]


async def get_shop_info(
    authorization: str,
    current: int = 1,
    size: int = 20,
    status: Optional[int] = 1,
    keyword: Optional[str] = None,
    tenant_id: Optional[int] = None,
):
    """
    获取门店信息
    Args:
        authorization (str): 授权token
        current (int): 当前页码
        size (int): 每页大小
        status (int): 门店状态,
            - 1-正常, None-正常和停用门店
        keyword (Optional[str]): 门店简称,门店编码,助记码
    Returns:
        dict: 门店信息
    """
    url = f"{base_url}/getCommonOrganOfLoginPageAuth"
    headers = {
        "Authorization": authorization,
        "client-tom": "Y",
        "tenant-id": str(tenant_id) if tenant_id else "",
    }
    payload = {
        "current": current,
        "size": size,
        "status": status,  
        "keyword": keyword,
    }
    async with AsyncClient(timeout=TTL) as client:
        response = await client.post(url, json=payload, headers=headers)
    data_json = response.json()
    return data_json