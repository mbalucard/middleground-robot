"""
员工相关接口
    - get_employee_list 获取员工列表
"""


from httpx import AsyncClient
from typing import Optional

from configs.api_config import deming_env
from api.virtue_bright.general_tools import timestamp
from utils.logger_manager import LoggerManager
logger = LoggerManager.get_logger(name="bi_report")

yaoud_env = deming_env
base_url = f"{yaoud_env['url']}/infra/external"
TTL = yaoud_env["timeout"]


async def get_employee_list(
    authorization: str,
    tenant_id: Optional[int] = None,
    keyword: Optional[str] = None,):
    """
    获取员工列表
    Args:
        authorization (str): 授权token
        tenant_id (Optional[int]): 租户ID
        keyword (Optional[str]): 关键字
            - 可搜索内容：姓名，编号，账号，电话
    """
    url = f"{base_url}/employee/getEmployeeList"
    headers = {
        "Authorization": authorization,
        "client-tom": "Y",
        "tenant-id": str(tenant_id) if tenant_id else "",
    }
    params = {
        "keyword": keyword if keyword else "",
        "_t": timestamp(),
    }
    async with AsyncClient(timeout=TTL) as client:
        response = await client.get(url, headers=headers, params=params)
        return response.json()