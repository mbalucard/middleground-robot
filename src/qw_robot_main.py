import asyncio
import json
import websockets

from api.qw_robot.general_tools import send_json, new_req_id
from api.qw_robot.message_processing import handle_msg_callback, heartbeat_loop
from configs.api_config import QywxBotConfig
from utils.logger_manager import LoggerManager

from robot.agents.main_agent import build_agent
from robot.tools.memory_device import postgres_resources

WS_URL = QywxBotConfig.URL
BOT_ID = QywxBotConfig.ID
SECRET = QywxBotConfig.SECRET

logger = LoggerManager.get_logger(name='qw_robot_main')


async def main() -> None:  # 主函数
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
            agent = build_agent(checkpointer=pg.checkpointer, store=pg.store)
            try:
                while True:
                    raw = await ws.recv()
                    msg = json.loads(raw)
                    cmd = msg.get("cmd")

                    # ping 的响应没有 cmd，只有 errcode
                    if "errcode" in msg and cmd is None:
                        continue

                    logger.info(f"msg: {msg}")  # 打印接收到的消息

                    if cmd == "aibot_msg_callback":
                        # 不要阻塞收包太久；复杂 LLM 可 create_task
                        await handle_msg_callback(ws, msg, agent)

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
