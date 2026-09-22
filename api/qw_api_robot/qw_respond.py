"""
企微出站消息与心跳
    - respond_stream / respond_template_card / respond_update_template_card: 被动回复
    - send_template_card / send_markdown: 主动推送
    - heartbeat_loop: 心跳包
"""

from __future__ import annotations

import asyncio
from typing import Optional

from api.qw_api_robot.general_tools import new_req_id, send_and_wait_response
from utils.logger_manager import LoggerManager

logger = LoggerManager.get_logger(name="qw_respond")


async def respond_stream(
    ws,
    callback_req_id: str,
    stream_id: str,
    content: str,
    *,
    finish: bool = True,
    feedback_id: Optional[str] = None,
    max_retries: int = 2,
    base_delay: float = 0.3,
) -> dict:
    """
    发送流式消息
    Args:
        ws: websocket连接
        callback_req_id(str): 回调请求ID
        stream_id(str): 流式消息ID
        content(str): 回复内容
        finish(bool): 是否结束本条流式消息, default=True
        feedback_id(str): 反馈ID, default=None
        max_retries(int): 版本冲突最大重试次数, default=2
        base_delay(float): 重试基础延迟秒数, default=0.3
    Returns:
        企微应答字典
    """
    stream_body: dict = {
        "id": stream_id,
        "finish": finish,
        "content": content,
    }
    if feedback_id:
        stream_body["feedback"] = {"id": feedback_id}

    payload = {
        "cmd": "aibot_respond_msg",
        "headers": {"req_id": callback_req_id},
        "body": {
            "msgtype": "stream",
            "stream": stream_body,
        },
    }

    last_resp: dict = {}
    for attempt in range(max_retries + 1):
        last_resp = await send_and_wait_response(ws, payload)

        err = last_resp.get("errcode", 0)
        if err == 0:
            return last_resp
        if err == 6000 and attempt < max_retries:
            delay = base_delay * (2**attempt)
            logger.warning(
                f"stream 版本冲突(6000), {delay:.1f}s 后重试 "
                f"attempt={attempt + 1}/{max_retries} stream_id={stream_id}"
            )
            await asyncio.sleep(delay)
            continue
        return last_resp

    return last_resp


async def respond_template_card(ws, callback_req_id: str, card: dict) -> dict:
    """
    被动回复模板卡片（消息回调同一 req_id）
    Args:
        ws: websocket连接
        callback_req_id(str): 消息回调 req_id
        card(dict): template_card
    Returns:
        企微应答
    """
    payload = {
        "cmd": "aibot_respond_msg",
        "headers": {"req_id": callback_req_id},
        "body": {
            "msgtype": "template_card",
            "template_card": card,
        },
    }
    resp = await send_and_wait_response(ws, payload, timeout=15.0)
    logger.info(
        f"respond_template_card task_id={card.get('task_id')} "
        f"errcode={resp.get('errcode')} errmsg={resp.get('errmsg')}"
    )
    return resp


async def respond_update_template_card(
    ws,
    callback_req_id: str,
    card: dict,
    userids: list[str] | None = None,
) -> dict:
    """
    模板卡片事件下更新卡片
    Args:
        ws: websocket连接
        callback_req_id(str): 事件回调 req_id
        card(dict): template_card（task_id 须一致）
        userids(list): 可选替换用户列表, default=None
    Returns:
        企微应答
    """
    body: dict = {
        "response_type": "update_template_card",
        "template_card": card,
    }
    if userids:
        body["userids"] = userids
    payload = {
        "cmd": "aibot_respond_update_msg",
        "headers": {"req_id": callback_req_id},
        "body": body,
    }
    resp = await send_and_wait_response(ws, payload, timeout=15.0)
    logger.info(
        f"respond_update_template_card task_id={card.get('task_id')} "
        f"errcode={resp.get('errcode')} errmsg={resp.get('errmsg')}"
    )
    return resp


async def send_template_card(ws, userid: str, card: dict) -> dict:
    """
    主动推送模板卡片
    Args:
        ws: websocket连接
        userid(str): 单聊 userid（作 chatid）
        card(dict): template_card
    Returns:
        企微应答
    """
    payload = {
        "cmd": "aibot_send_msg",
        "headers": {"req_id": new_req_id()},
        "body": {
            "chatid": userid,
            "chat_type": 1,
            "msgtype": "template_card",
            "template_card": card,
        },
    }
    resp = await send_and_wait_response(ws, payload, timeout=15.0)
    logger.info(
        f"send_template_card userid={userid} task_id={card.get('task_id')} "
        f"errcode={resp.get('errcode')} errmsg={resp.get('errmsg')}"
    )
    return resp


async def send_markdown(ws, userid: str, content: str) -> dict:
    """
    主动推送 markdown 消息
    Args:
        ws: websocket连接
        userid(str): 单聊 userid
        content(str): markdown 正文
    Returns:
        企微应答
    """
    payload = {
        "cmd": "aibot_send_msg",
        "headers": {"req_id": new_req_id()},
        "body": {
            "chatid": userid,
            "chat_type": 1,
            "msgtype": "markdown",
            "markdown": {"content": content},
        },
    }
    resp = await send_and_wait_response(ws, payload, timeout=15.0)
    logger.info(
        f"send_markdown userid={userid} "
        f"errcode={resp.get('errcode')} errmsg={resp.get('errmsg')}"
    )
    return resp


async def heartbeat_loop(ws, interval: float = 30.0) -> None:
    """
    定时发送心跳包
    Args:
        ws: websocket连接
        interval(float): 心跳间隔秒数, default=30.0
    """
    while True:
        await asyncio.sleep(interval)
        try:
            await send_and_wait_response(
                ws,
                {"cmd": "ping", "headers": {"req_id": new_req_id()}},
                timeout=15.0,
            )
        except Exception as e:
            logger.warning(f"heartbeat 失败: {e}")
