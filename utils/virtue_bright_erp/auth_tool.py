"""
登录相关工具集
    - get_auth_data: 获取授权信息
    - change_organ: 切换机构
    - get_authorization_test: 测试获取授权信息
"""
import json
import os
from typing import Optional
from utils.redis_link import RedisManager
from api.virtue_bright.auth import get_authorization, logout
from api.virtue_bright.infra import switch_organ, switch_system
from utils.logger_manager import LoggerManager
from dotenv import load_dotenv

load_dotenv()
logger = LoggerManager.get_logger(name="auth_tool")

r_link = RedisManager()


async def get_auth_data(username: str, password: str) -> dict:
    """
    获取药德系统的授权信息
    Args:
        username: 用户名
        password: 密码
    Returns:
        dict: 授权信息
    """

    r = await r_link.get_client()

    key = f"auth_{username}"
    if await r.exists(key):
        data = await r.get(key)
        data = json.loads(data)
        data['auth']['expires_in'] = await r.ttl(key)
        return data
    else:
        auth = await get_authorization(username, password)
        await r.set(key, json.dumps(auth), ex=auth['auth']['expires_in'])
        return auth


async def logout_auth(
    username: str,
    authorization: str,
    tenant_id: Optional[int] = None):
    """
    退出登录
    Args:
        username: 用户名
        authorization: 授权信息
        tenant_id: 租户ID
    Returns:
        dict: 退出登录结果
    """
    r = await r_link.get_client()
    key = f"auth_{username}"
    if await r.exists(key):
        response = await logout(authorization, tenant_id)
        if response['ok']:
            await r.delete(key)
            return response
        else:
            return response
    else:
        return {"error": "用户未登录"}


async def change_organ(username: str, authorization: str, organ_id: int) -> dict:
    """
    切换机构
    Args:
        username: 用户名
        authorization: 授权信息
        organ_id: 节点ID, 与企业ID一一对应
    Returns:
        dict: 授权信息
    """
    r = await r_link.get_client()
    key = f"auth_{username}"
    if await r.exists(key):
        organ_data = await switch_organ(authorization, organ_id)
        if organ_data['ok']:
            auth_data = await r.get(key)
            auth_data = json.loads(auth_data)
            auth_data['currentStatus']['organId'] = organ_data['data']['organId']
            auth_data['currentStatus']['enterpriseId'] = organ_data['data']['enterpriseId']
            ttl = await r.ttl(key)
            await r.set(key, json.dumps(auth_data), ex=ttl)
            return organ_data
        else:
            return organ_data
    else:
        return {"error": "用户未登录"}


async def get_authorization_test():
    """
    测试获取授权信息
    Returns:
        dict: 授权信息
    """
    username = os.getenv("TEST_USERNAME")
    password = os.getenv("TEST_PASSWORD")
    organ_id = os.getenv("TEST_ORGAN_ID")

    auth = await get_auth_data(username, password)
    authorization = auth.get("auth").get("authorization")
    current_status = auth.get("currentStatus")
    # 切换至ERP系统
    if current_status.get("systemId") != 1:
        response = await switch_system(authorization)
        if response['ok']:
            out_mes = await logout_auth(
                username=username, 
                authorization=authorization, 
                tenant_id=current_status.get("tenantId")
                )
            logger.info(f"退出日志信息:{out_mes}")
            auth = await get_auth_data(username, password)
            authorization = auth.get("auth").get("authorization")
            current_status = auth.get("currentStatus")
        else:
            logger.error(f"切换系统失败,mes:{response}")

    # 切换至指定机构
    if current_status.get("organId") != organ_id:
        response = await change_organ(username, authorization, organ_id)
        logger.info(f"切换机构成功,mes:{response}")
    return authorization

if __name__ == "__main__":
    import asyncio

    data = asyncio.run(get_authorization_test())
    print("data:", data)
