"""
登录相关工具集
"""
import json
import os
from utils.redis_link import RedisManager
from api.virtue_bright.auth import get_authorization
from api.virtue_bright.system import switch_organ
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
    username = os.getenv("TEST_USERNAME")
    password = os.getenv("TEST_PASSWORD")
    organ_id = os.getenv("TEST_ORGAN_ID")

    auth = await get_auth_data(username, password)
    authorization = auth.get("auth").get("authorization")
    if auth.get("currentStatus").get("tenantId") != organ_id:
        response = await change_organ(username, authorization, organ_id)
        logger.info(f"切换机构成功,mes:{response}")
    return authorization

if __name__ == "__main__":
    import asyncio
    
    data = asyncio.run(get_authorization_test())
    print("data:", data)
