"""
系统激活消息模版相关接口
    - query_sys_dict_items_by_dict_code 查询系统激活消息模版
"""


from httpx import AsyncClient
from typing import Optional

from configs.api_config import deming_env
from api.virtue_bright.general_tools import timestamp
from utils.logger_manager import LoggerManager
logger = LoggerManager.get_logger(name="bi_report")

yaoud_env = deming_env
base_url = f"{yaoud_env['url']}/message/sysStationMessageTemplateActive"
TTL = yaoud_env["timeout"]


async def query_sys_dict_items_by_dict_code(
    authorization: str,
    tenant_id: Optional[int] = None,
    dict_code: str = "DX108-001",
):
    """
    查询系统激活消息模版
    Args:
        authorization (str): 授权token
        tenant_id (Optional[int]): 租户ID
        dict_code (str): 字典编码
    """
    url = f"{base_url}/querySysDictItemsByDictCode"
    headers = {
        "Authorization": authorization,
        "client-tom": "Y",
        "tenant-id": str(tenant_id) if tenant_id else "",
    }
    params = {
        "dictCode": dict_code,
        "_t": timestamp()
    }
    async with AsyncClient(timeout=TTL) as client:
        response = await client.get(url, params=params, headers=headers, timeout=TTL)
        return response.json()
