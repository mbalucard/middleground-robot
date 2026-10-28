"""
门店相关模块
    - query_region_tree: 获取区域信息-查询用
"""

from httpx import AsyncClient
from typing import Optional, List

from configs.api_config import deming_env
from api.virtue_bright.general_tools import timestamp, get_current_date, get_date_start_and_end_time
from utils.logger_manager import LoggerManager

logger = LoggerManager.get_logger(name="stores")


yaoud_env = deming_env
base_url = f"{yaoud_env['url']}/infra/stores"
TTL = yaoud_env["timeout"]


async def query_region_tree(
    authorization: str,
    tenant_id: Optional[int] = None,):
    """
    获取区域信息-查询用

    Args:
        authorization: 授权
        tenant_id: 租户ID
    Returns:
        dict: 区域信息
    """
    url = f"{base_url}/queryRegionTree"
    headers = {
        "Authorization": authorization,
        "client-tom": "Y",
        "tenant-id": str(tenant_id) if tenant_id else "",
    }
    params = {"_": timestamp()}
    async with AsyncClient(timeout=TTL) as client:
        response = await client.get(url, headers=headers, params=params)
        return response.json()


