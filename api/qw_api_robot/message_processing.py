"""
消息处理入口（企微适配 → HTTP API）
    - handle_msg_callback: 消息回调路由（按 msgtype 分发）
    - handle_template_card_event: re-export 自 interrupt_flow
    - heartbeat_loop: re-export 自 qw_respond
"""

from __future__ import annotations

from api.qw_api_robot.api_client import ApiClientError
from api.qw_api_robot.general_tools import get_or_create_api_thread_id, new_req_id
from api.qw_api_robot.interrupt_flow import handle_template_card_event  # noqa: F401
from api.qw_api_robot.msg_handlers import (
    handle_image_msg,
    handle_mixed_msg,
    handle_text_msg,
)
from api.qw_api_robot.qw_respond import heartbeat_loop, respond_stream  # noqa: F401
from utils.logger_manager import LoggerManager
from utils.redis_link import RedisManager

logger = LoggerManager.get_logger(name="message_processing")
r_link = RedisManager()


async def handle_msg_callback(ws, msg: dict) -> None:
    """
    处理企微消息回调
    Args:
        ws: websocket连接
        msg(dict): 回调消息
    """
    headers = msg.get("headers") or {}
    body = msg.get("body") or {}
    callback_req_id = headers["req_id"]
    msgtype = body.get("msgtype")
    chattype = body.get("chattype", "")
    stream_id = new_req_id()
    logger.info(f"stream_id: {stream_id} msgtype={msgtype} chattype={chattype}")

    from_info = body.get("from") or {}
    userid = from_info.get("userid")
    if not userid:
        await respond_stream(
            ws,
            callback_req_id,
            stream_id,
            content="无法识别发送者，请重试",
            finish=True,
        )
        return

    try:
        thread_id = await get_or_create_api_thread_id(userid)
    except ApiClientError as e:
        await respond_stream(
            ws,
            callback_req_id,
            stream_id,
            content=e.user_message,
            finish=True,
        )
        return
    except Exception as e:
        logger.exception(f"获取 API thread 失败: {e}")
        await respond_stream(
            ws,
            callback_req_id,
            stream_id,
            content="创建会话失败，请稍后重试",
            finish=True,
        )
        return

    logger.info(f"msg_body_from: {from_info} - thread_id: {thread_id}")
    r_client = await r_link.get_client()

    common = dict(
        r_client=r_client,
        callback_req_id=callback_req_id,
        stream_id=stream_id,
        userid=userid,
        thread_id=thread_id,
        body=body,
        chattype=chattype,
    )

    if msgtype == "text":
        await handle_text_msg(ws, **common)
        return

    if msgtype == "image":
        await handle_image_msg(ws, **common)
        return

    if msgtype == "mixed":
        await handle_mixed_msg(ws, **common)
        return

    await respond_stream(
        ws,
        callback_req_id,
        stream_id,
        content=f"暂不支持消息类型：{msgtype}",
        finish=True,
    )
