"""
企微机器人主程序（HTTP API 版）
    - main: 主程序
"""

import asyncio
import json

import websockets

from api.qw_api_robot.general_tools import (
    dispatch_ws_response,
    new_req_id,
    send_json,
)
from api.qw_api_robot.message_processing import (
    handle_msg_callback,
    handle_template_card_event,
    heartbeat_loop,
)
from configs.api_config import QywxBotConfig
from utils.logger_manager import LoggerManager

WS_URL = QywxBotConfig.URL
BOT_ID = QywxBotConfig.ID
SECRET = QywxBotConfig.SECRET

logger = LoggerManager.get_logger(name="qw_main")


def _log_task_exception(task: asyncio.Task) -> None:
    """
    记录后台任务异常
    Args:
        task: asyncio.Task
    """
    try:
        exc = task.exception()
    except asyncio.CancelledError:
        return
    if exc:
        logger.exception(f"后台任务异常: {exc}")


async def main() -> None:
    async with websockets.connect(WS_URL, ping_interval=None) as ws:
        await send_json(
            ws,
            {
                "cmd": "aibot_subscribe",
                "headers": {"req_id": new_req_id()},
                "body": {"bot_id": BOT_ID, "secret": SECRET},
            },
        )
        sub_resp = json.loads(await ws.recv())
        logger.info(f"subscribe: {sub_resp}")
        print("subscribe:", sub_resp)
        if sub_resp.get("errcode") != 0:
            return

        hb = asyncio.create_task(heartbeat_loop(ws))
        try:
            while True:
                raw = await ws.recv()
                msg = json.loads(raw)
                cmd = msg.get("cmd")

                if dispatch_ws_response(msg):
                    continue

                if "errcode" in msg and cmd is None:
                    continue

                if cmd == "aibot_msg_callback":
                    task = asyncio.create_task(handle_msg_callback(ws, msg))
                    task.add_done_callback(_log_task_exception)

                elif cmd == "aibot_event_callback":
                    event = (msg.get("body") or {}).get("event") or {}
                    eventtype = event.get("eventtype")
                    req_id = msg["headers"]["req_id"]

                    if eventtype == "enter_chat":
                        await send_json(
                            ws,
                            {
                                "cmd": "aibot_respond_welcome_msg",
                                "headers": {"req_id": req_id},
                                "body": {
                                    "msgtype": "text",
                                    "text": {"content": "您好！我是智能助手。"},
                                },
                            },
                        )
                    elif eventtype == "template_card_event":
                        task = asyncio.create_task(
                            handle_template_card_event(ws, msg)
                        )
                        task.add_done_callback(_log_task_exception)
                    elif eventtype == "disconnected_event":
                        logger.warning("连接被踢下线，需要重连")
                        print("连接被踢下线，需要重连")
                        break
                    else:
                        logger.info(f"event: {eventtype} {msg}")
                        print("event:", eventtype, msg)

                else:
                    logger.info(f"other: {msg}")
                    print("other:", msg)
        finally:
            hb.cancel()


if __name__ == "__main__":
    asyncio.run(main())


# uv run src/qw_main.py