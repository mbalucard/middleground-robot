from api.qw_robot.general_tools import send_json, new_req_id,get_redis_id
from robot.agents.agent_invoke import stream_agent
from robot.agents.main_agent import agent
from utils.logger_manager import LoggerManager

from typing import Optional
import json
import asyncio

logger = LoggerManager.get_logger(name='message_processing')


async def respond_stream(
        ws,
        callback_req_id: str,
        stream_id: str,
        content: str,
        *,
        finish: bool = True,
        feedback_id: Optional[str] = None,) -> dict:
    """
    主动推送/刷新流式消息。callback_req_id 必须透传消息回调里的 req_id。
    Args:
        ws:  websocket连接
        callback_req_id: 回调请求id
        stream_id: 流式消息id
        content: 消息内容
        finish: 是否结束
        feedback_id: 反馈id
    Returns:
        dict: 响应
    """
    stream_body: dict = {
        "id": stream_id,
        "finish": finish,
        "content": content,
    }
    # feedback 可选；不为空时用户点赞/点踩会触发 feedback_event
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
    await send_json(ws, payload)
    return json.loads(await ws.recv())


async def heartbeat_loop(ws, interval: float = 30.0) -> None:
    """心跳包"""
    while True:
        await asyncio.sleep(interval)
        # 发送心跳包
        await send_json(ws, {"cmd": "ping", "headers": {"req_id": new_req_id()}})


async def handle_msg_callback(ws, msg: dict) -> None:
    """
    处理消息回调
    Args:
        ws:  websocket连接
        msg: 消息
    Returns:
        None
    """
    headers = msg.get("headers") or {}
    body = msg.get("body") or {}
    callback_req_id = headers["req_id"]  # 同一次回调的所有流式回复都必须用这个
    msgtype = body.get("msgtype")

    #! 获取用户信息
    if 'from' in body:
        userid = body.get('from').get('userid')
        thread_id = get_redis_id(key=userid,id_type='thread_id')
        logger.info(f"msg_body_from: {body.get('from')} - thread_id: {thread_id}")

    if msgtype != "text":
        #! 图片/文件等可按文档处理；这里先只回文本流式
        await respond_stream(
            ws,
            callback_req_id,
            stream_id=new_req_id(),
            content=f"暂不支持消息类型：{msgtype}",
            finish=True,
        )
        return

    question = body["text"]["content"]
    stream_id = new_req_id()  # 本条流式消息的唯一 id，后续刷新必须复用
    logger.info(f"stream_id: {stream_id}")

    # 1) 首次创建流式气泡
    await respond_stream(
        ws,
        callback_req_id,
        stream_id,
        content="正在思考...",
        finish=False,
        feedback_id=f"fb-{stream_id}",  # 可选
    )

    # 2) 主动多次刷新（长连接模式关键：没有企业微信再来轮询你）
    last = ""

    async for partial in stream_agent(
        agent=agent,
        question=question,
        thread_id=thread_id,
        user_id=userid,
    ):
        last = partial
        resp = await respond_stream(
            ws,
            callback_req_id,
            stream_id,
            content=partial,
            finish=False,
        )
        if resp.get("errcode", 0) != 0:
            print("流式刷新失败:", resp)
            return

    # 3) 10 分钟内必须 finish=true，否则服务端会自动结束
    await respond_stream(
        ws,
        callback_req_id,
        stream_id,
        content=last,
        finish=True,
        feedback_id=f"fb-{stream_id}",
    )
