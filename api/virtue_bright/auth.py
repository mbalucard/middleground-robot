"""
登录VIRTUE_BRIGHT系统
    - log_in: 登录药德系统
    - get_authorization: 获取药德系统的授权信息
"""
import json
from httpx import AsyncClient
from api.virtue_bright.aes_tool import aes_cfb_encrypt_base64
from configs.api_config import deming_env, deming_uat_env
from utils.redis_link import RedisManager

yaoud_env = deming_env
base_url = f"{yaoud_env['url']}/auth"

TTL = yaoud_env["timeout"]


async def log_in(
    username: str, 
    password: str,) -> dict:
    """
    登陆药德系统

    Args:
        username (str): 药德用户名
        password (str): 药德密码

    Returns:
        dict: 登陆成功返回的人员信息
    """
    url = f"{base_url}/oauth2/token"
    password_encrypted = aes_cfb_encrypt_base64(password)
    headers = {
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "authorization": yaoud_env["public_key"],
        "client-tom": "Y",
        "skipToken": "true",
    }
    params = {
        "grant_type": "password",
        "username": username,
        "randomStr": "blockPuzzle",
        "code": "",
        "scope": "server",
    }
    payload = {
        "password": password_encrypted,
    }
    async with AsyncClient() as client:
        response = await client.post(
            url, headers=headers,
            params=params, data=payload, timeout=TTL)
    return response.json()


async def get_authorization(username: str, password: str) -> dict:
    """
    获取药德系统的授权信息

    Args:
        username (str): 药德用户名
        password (str): 药德密码

    Returns:
        dict: 包含授权信息和租户ID的字典
    """

    response = await log_in(username, password)
    authorization = response.get("token_type")+" "+response.get("access_token")
    auth = {
        "authorization": authorization,
        "expires_in": response.get("expires_in"),  
    }
    # 当前状态
    current_status = {
        "tenantId": response.get("tenantId"),  # 租户ID
        "enterpriseId": response.get("enterpriseId"),  # 企业ID
        "organId": response.get("organId"),  # 机构ID
        "organType": response.get("organType"),  # 机构类型
        "systemId": response.get("systemId"),  # 模块ID
        "currentPath": response.get("systemPath"),  # 模块路径
        "user_id": response.get("user_id"),
        "username": response.get("username"),
        "is_admin": response.get("tenantAdmin")  # 是否为租户管理员
    }
    # 资源信息
    resource = {"organIds": response.get("organIds", []),  # 机构ID列表
                "tenantIds": response.get("tenantIds", []),  # 租户ID列表
                "systemIds": response.get("systemIds", []),  # 模块ID列表
                "enterpriseIds": response.get("enterpriseIds", [])}  # 企业ID列表
    # 员工信息
    if response.get("employee"):
        employee_data = json.loads(response.get("employee"))
        employee = {
            "id": employee_data["id"],
            "code": employee_data["code"],
            "name": employee_data["name"],
            "yaoudAccount": employee_data["yaoudAccount"],
            "status": employee_data["status"],
        }
    else:
        employee = None
        
    result = {
        "auth": auth,
        "currentStatus": current_status,
        "resource": resource,
        "employee": employee
    }
    return result




if __name__ == "__main__":
    import asyncio
    import os
    from dotenv import load_dotenv
    load_dotenv()

    username = os.getenv("TEST_USERNAME")
    password = os.getenv("TEST_PASSWORD")

    # res = asyncio.run(log_in(username, password))
    # print(res)
    auth = asyncio.run(log_in(username, password))
    print("auth:", auth)
