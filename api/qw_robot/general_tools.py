"""
通用工具
    - new_req_id: 生成唯一请求id
    - get_redis_id: 获取redis id
    - send_json: 发送json数据
"""

import uuid
import json
from configs.service_config import ConfigRedis
from redis import Redis
from typing import Literal
from random import randint

r = Redis(host=ConfigRedis.HOST, port=ConfigRedis.PORT, db=ConfigRedis.DB,
          password=ConfigRedis.PASSWORD, decode_responses=True)


def new_req_id() -> str:
    """
    生成唯一请求id，用于标识一次请求
    Returns:
        str: 唯一请求id
    """
    return str(uuid.uuid4())


def get_redis_id(
    key: str,
    id_type: Literal['thread_id', 'u_id'] = 'u_id',
    ttl: int = ConfigRedis.TIMEOUT) -> str:
    """
    获取ID
    Args:
        key: 键
        id_type: id类型 default: u_id
            - thread_id: 会话ID
            - u_id: 通用ID
        ttl: 过期时间 单位: 秒
    Returns:
        str: ID
    """
    out_time = ttl + randint(1, 30)
    if r.exists(key):
        r.expire(key, out_time)
        return r.hget(key, id_type)
    else:
        if id_type == 'thread_id':
            value = {'key': key, id_type: f"t-{str(uuid.uuid4())}"}
        else:
            value = {'key': key, id_type: f"u-{str(uuid.uuid4())}"}
        r.hset(key, mapping=value)
        r.expire(key, out_time)
        return value[id_type]


async def send_json(ws, payload: dict) -> None:
    """
    发送json数据
    Args:
        ws:  websocket连接
        payload: 发送的数据，字典类型
    Returns:
        None
    """
    await ws.send(json.dumps(payload, ensure_ascii=False))
