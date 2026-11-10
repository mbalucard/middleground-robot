"""
角色管理
    - 获取企业模块树: get_bloc_enterprise_tree
"""

from httpx import AsyncClient
from typing import Optional, List

from configs.api_config import deming_env
from api.virtue_bright.general_tools import timestamp, get_current_date, get_date_start_and_end_time

yaoud_env = deming_env
base_url = f"{yaoud_env['url']}/infra/role"
TTL = yaoud_env["timeout"]


async def get_bloc_enterprise_tree(authorization: str) -> dict:
    """
    获取企业模块输
    Args:
        authorization (str): 认证信息
    Returns:
        dict: 企业树
    """
    url = f"{base_url}/getBlocEnterpriseTree"
    headers = {
        "Authorization": authorization,
        "client-tom": "Y",
    }
    params = {
        "_t": timestamp()
    }
    async with AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params, timeout=TTL)
    return response.json()


if __name__ == "__main__":
    import asyncio
    auth = "Bearer new_fb2e194c-427f-487e-b1a6-7389608d9d62"
    result = asyncio.run(get_bloc_enterprise_tree(auth))
    print(result)