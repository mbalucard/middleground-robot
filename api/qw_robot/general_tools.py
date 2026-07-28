import uuid
import time
import json


def new_req_id() -> str:
    """
    生成唯一请求id，用于标识一次请求
    Returns:
        str: 唯一请求id
    """
    return str(uuid.uuid4())


def timestamp() -> int:
    """
    获取当前时间戳
    Returns:
        int: 当前时间戳，单位为秒
    """
    return int(time.time())


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


