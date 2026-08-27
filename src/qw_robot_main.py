"""
企微机器人主程序
    - main: 主程序
"""
import asyncio
import json
import websockets

from api.qw_robot.general_tools import send_json, new_req_id, dispatch_ws_response
from api.qw_robot.message_processing import handle_msg_callback, heartbeat_loop
from api.qw_robot.data_models import init_db
from configs.api_config import QywxBotConfig
from utils.logger_manager import LoggerManager

from robot.agents.main_agent import build_agent
from robot.tools.memory_device import postgres_resources

WS_URL = QywxBotConfig.URL
BOT_ID = QywxBotConfig.ID
SECRET = QywxBotConfig.SECRET

logger = LoggerManager.get_logger(name='qw_robot_main')


def _log_task_exception(task: asyncio.Task) -> None:
    """
    记录 handle_msg_callback 任务异常
    """
    try:
        exc = task.exception()
    except asyncio.CancelledError:
        return
    if exc:
        logger.exception(f"handle_msg_callback 任务异常: {exc}")


async def main() -> None:  
    await init_db() # 数据库初始化
    async with websockets.connect(WS_URL, ping_interval=None) as ws:  # 连接到企业微信服务器
        # 订阅（成功后不要反复 subscribe）
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
        async with postgres_resources() as pg:
            agent = await build_agent(checkpointer=pg.checkpointer, store=pg.store)
            try:
                while True:
                    raw = await ws.recv()
                    msg = json.loads(raw)
                    cmd = msg.get("cmd")

                    # ping / aibot_respond_msg 等应答：投递给等待方
                    if dispatch_ws_response(msg):
                        continue

                    # ping 的响应没有 cmd，只有 errcode（未被 dispatch 时跳过）
                    if "errcode" in msg and cmd is None:
                        continue

                    # logger.info(f"msg: {msg}")  # 打印接收到的消息

                    if cmd == "aibot_msg_callback":
                        # 图片下载+推理较慢，不阻塞收包
                        task = asyncio.create_task(
                            handle_msg_callback(ws, msg, agent)
                        )
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
