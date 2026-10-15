"""
系统管理
    - 切换到租户切换页: switch_owner_page
    - 切换机构: switch_organ
    - 获取企业列表: get_enterprise_list
    - 获取机构列表: get_organ_list
"""

from httpx import AsyncClient
from typing import Optional, List

from configs.api_config import deming_env
from api.virtue_bright.general_tools import timestamp, get_current_date, get_date_start_and_end_time

yaoud_env = deming_env
base_url = f"{yaoud_env['url']}/infra/system"
TTL = yaoud_env["timeout"]


async def switch_owner_page(authorization: str) -> dict:
    """
    切换到租户切换页
    Args:
        authorization (str): 认证信息
    Returns:
        dict: 是否切换成功，bool
    """
    url = f"{base_url}/switchOwnerPage"
    params = {"_t": timestamp()}
    headers = {
        "authorization": authorization,
        "client-tom": "Y",
        "skipToken": "true",
    }
    async with AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params, timeout=TTL)
    return response.json()


async def switch_organ(authorization: str, organ_id: int) -> dict:
    """
    切换机构
    Args:
        authorization (str): 认证信息
        organ_id (int): 机构ID
    Returns:
        dict: 切换机构结果
    """
    url = f"{base_url}/switchOrgan"
    headers = {
        "authorization": authorization,
        "client-tom": "Y",
    }
    params = {
        "id": organ_id,
        "mac": "",
        "forceRestriction": "true",
        "_t": timestamp()
    }
    async with AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params, timeout=TTL)
    return response.json()


async def get_enterprise_list(
    authorization: str,
    tenant_id: Optional[int] = None,
) -> dict:
    """
    获取企业列表
    Args:
        authorization (str): 认证信息
        tenant_id (int, None): 租户ID. Defaults to None.
    Returns:
        dict: 企业列表
    """
    url = f"{base_url}/getEnterpriseList"
    headers = {
        "Authorization": authorization,
        "client-tom": "Y",
        "tenant-id": str(tenant_id) if tenant_id else "",
    }
    params = {"_t": timestamp()}
    async with AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params, timeout=TTL)
    return response.json()


async def get_organ_list(
    authorization: str,
    tenant_id: Optional[int] = None,
) -> dict:
    """
    获取机构列表
    Args:
        authorization (str): 认证信息
        tenant_id (int, None): 租户ID. Defaults to None.
    Returns:
        dict: 机构列表
    """
    url = f"{base_url}/getOrganList"
    headers = {
        "Authorization": authorization,
        "client-tom": "Y",
        "tenant-id": str(tenant_id) if tenant_id else "",
    }
    params = {"_t": timestamp()}
    async with AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params, timeout=TTL)
    return response.json()







if __name__ == "__main__":
    import asyncio
    authorization = "Bearer new_b8be0910-252d-47a3-8223-364f8d129c2b"
    tenant_id = 148

    async def main():
        data = await get_organ_list(authorization, tenant_id)
        print(data)
    asyncio.run(main())
