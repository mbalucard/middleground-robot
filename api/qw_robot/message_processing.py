"""
消息处理
    - respond_stream: 发送流式消息
    - heartbeat_loop: 心跳包
    - handle_msg_callback: 处理消息回调
"""

from api.qw_robot.general_tools import (
    send_and_wait_response,
    new_req_id,
    get_redis_id,
)
from api.qw_robot.session_manager import session_hset
from api.qw_robot.media_handler import MediaError, prepare_image_for_model
from api.qw_robot.pending_images import (
    PendingFullError,
    append_pending_image,
    take_pending_images,
)
from robot.agents.agent_invoke import stream_agent
from robot.agents.message_content import (
    DEFAULT_MULTI_IMAGE_PROMPT,
    VisionProvider,
    build_vision_user_content,
    vision_model_name,
)

from langgraph.graph.state import CompiledStateGraph
from utils.logger_manager import LoggerManager
from utils.redis_link import RedisManager

from typing import Any, Optional
import asyncio

logger = LoggerManager.get_logger(name='message_processing')
r_link = RedisManager()


def _parse_mixed_items(body: dict) -> tuple[str, list[dict]]:
    """
    解析 mixed.msg_item
    Args:
        body(dict): 企微回调 body
    Returns:
        (合并后的文本, [{url, aeskey}, ...])
    """
    items = ((body.get("mixed") or {}).get("msg_item")) or []
    texts: list[str] = []
    images: list[dict] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        item_type = item.get("msgtype")
        if item_type == "text":
            content = ((item.get("text") or {}).get("content") or "").strip()
            if content:
                texts.append(content)
        elif item_type == "image":
            image = item.get("image") or {}
            url = image.get("url")
            aeskey = image.get("aeskey")
            if url and aeskey:
                images.append({"url": url, "aeskey": aeskey})
    return "\n".join(texts).strip(), images


def _pending_ready_message(count: int) -> str:
    """
    纯图挂起成功后的回复文案
    Args:
        count(int): 当前挂起张数
    Returns:
        回复文案
    """
    if count <= 1:
        return "图片已就绪。请问你需要我做什么？"
    return f"又收到 1 张图片，当前共 {count} 张待处理。请问你需要我做什么？"


async def respond_stream(
    ws,
    callback_req_id: str,
    stream_id: str,
    content: str,
    *,
    finish: bool = True,
    feedback_id: Optional[str] = None,
    max_retries: int = 2,
    base_delay: float = 0.3,) -> dict:
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
            delay = base_delay * (2 ** attempt)
            logger.warning(
                f"stream 版本冲突(6000), {delay:.1f}s 后重试 "
                f"attempt={attempt + 1}/{max_retries} stream_id={stream_id}"
            )
            await asyncio.sleep(delay)
            continue
        return last_resp

    return last_resp


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


async def _run_agent_stream(
    ws,
    *,
    agent: CompiledStateGraph,
    callback_req_id: str,
    stream_id: str,
    question: str,
    thread_id: str,
    userid: str,
    r_client,
    model_name: str = "deepseek",
    user_content: Any = None,
    placeholder: str = "正在思考...",) -> None:
    """
    占位流式气泡后调用智能体并刷新回复
    Args:
        ws: websocket连接
        agent: 智能体
        callback_req_id(str): 回调请求ID
        stream_id(str): 流式消息ID
        question(str): 用户问题
        thread_id(str): 会话ID
        userid(str): 用户ID
        r_client: Redis连接
        model_name(str): 模型名称, default="deepseek"
        user_content: 多模态用户内容, default=None
        placeholder(str): 占位文案, default="正在思考..."
    """
    await respond_stream(
        ws,
        callback_req_id,
        stream_id,
        content=placeholder,
        finish=False,
        feedback_id=f"fb-{stream_id}",
    )

    last = ""
    try:
        async for partial in stream_agent(
            agent=agent,
            question=question,
            thread_id=thread_id,
            user_id=userid,
            message_id=stream_id,
            redis_client=r_client,
            model_name=model_name,
            user_content=user_content,
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
                logger.error(f"流式刷新失败: {resp}")
                return
    except Exception as e:
        logger.exception(f"Agent 调用失败: {e}")
        last = "图片理解失败，请稍后重试" if user_content is not None else "处理失败，请稍后重试"
        await respond_stream(
            ws,
            callback_req_id,
            stream_id,
            content=last,
            finish=True,
            feedback_id=f"fb-{stream_id}",
        )
        return

    await respond_stream(
        ws,
        callback_req_id,
        stream_id,
        content=last or "（无内容）",
        finish=True,
        feedback_id=f"fb-{stream_id}",
    )


async def _prepare_payloads_from_refs(image_refs: list[dict]) -> list[dict]:
    """
    从企微 url+aeskey 下载解密为模型 payload
    Args:
        image_refs(list): [{url, aeskey}, ...]
    Returns:
        图片 payload 列表
    """
    payloads: list[dict] = []
    for ref in image_refs:
        payloads.append(await prepare_image_for_model(ref["url"], ref["aeskey"]))
    return payloads


async def _handle_vision_flow(
    ws,
    *,
    agent: CompiledStateGraph,
    callback_req_id: str,
    stream_id: str,
    userid: str,
    thread_id: str,
    chattype: str,
    aibot_id: str,
    r_client,
    text_prompt: str,
    image_refs: Optional[list[dict]] = None,
    image_payloads: Optional[list[dict]] = None,
    question_prefix: str = "[图片]",
    skip_initial_placeholder: bool = False,
    provider: VisionProvider = "openai",) -> None:
    """
    多模态理解并流式文字回复
    Args:
        ws: websocket连接
        agent: 智能体
        callback_req_id(str): 回调请求ID
        stream_id(str): 流式消息ID
        userid(str): 用户ID
        thread_id(str): 会话ID
        chattype(str): 会话类型
        aibot_id(str): 机器人ID
        r_client: Redis连接
        text_prompt(str): 用户文本或默认提示
        image_refs(list): 需下载的图片引用, default=None
            - [{url, aeskey}, ...]
        image_payloads(list): 已缓存的图片 payload, default=None
        question_prefix(str): 会话记录前缀, default="[图片]"
        skip_initial_placeholder(bool): 是否跳过「正在识别图片...」, default=False
        provider: 视觉模型提供方, default="openai"
            - openai → DeepSeek Vision
            - anthropic → MiniMax-M3
    """
    question_for_db = f"{question_prefix} {text_prompt}"
    await session_hset(
        redis_client=r_client,
        message_id=stream_id,
        user_id=userid,
        aibot_id=aibot_id,
        chat_type=chattype,
        thread_id=thread_id,
        question=question_for_db,
    )

    if not skip_initial_placeholder:
        await respond_stream(
            ws,
            callback_req_id,
            stream_id,
            content="正在识别图片...",
            finish=False,
            feedback_id=f"fb-{stream_id}",
        )

    payloads: list[dict] = list(image_payloads or [])
    try:
        if image_refs:
            payloads.extend(await _prepare_payloads_from_refs(image_refs))
    except MediaError as e:
        logger.warning(f"图片准备失败: {e.user_message} cause={e.cause}")
        await respond_stream(
            ws,
            callback_req_id,
            stream_id,
            content=e.user_message,
            finish=True,
            feedback_id=f"fb-{stream_id}",
        )
        return
    except Exception as e:
        logger.exception(f"图片准备异常: {e}")
        await respond_stream(
            ws,
            callback_req_id,
            stream_id,
            content="图片解析失败，请重试",
            finish=True,
            feedback_id=f"fb-{stream_id}",
        )
        return

    if not payloads:
        await respond_stream(
            ws,
            callback_req_id,
            stream_id,
            content="图片下载失败，请重新发送",
            finish=True,
            feedback_id=f"fb-{stream_id}",
        )
        return

    user_content = build_vision_user_content(
        text_prompt, payloads, provider=provider
    )
    last = ""
    try:
        async for partial in stream_agent(
            agent=agent,
            question=question_for_db,
            thread_id=thread_id,
            user_id=userid,
            message_id=stream_id,
            redis_client=r_client,
            model_name=vision_model_name(provider),
            user_content=user_content,
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
                logger.error(f"流式刷新失败: {resp}")
                return
    except Exception as e:
        logger.exception(f"图片理解 Agent 失败: {e}")
        last = "图片理解失败，请稍后重试"

    await respond_stream(
        ws,
        callback_req_id,
        stream_id,
        content=last or "（无内容）",
        finish=True,
        feedback_id=f"fb-{stream_id}",
    )


async def handle_msg_callback(
    ws,
    msg: dict,
    agent: CompiledStateGraph,) -> None:
    """
    处理企微消息回调
    Args:
        ws: websocket连接
        msg(dict): 回调消息
        agent: 智能体
    """
    headers = msg.get("headers") or {}
    body = msg.get("body") or {}
    callback_req_id = headers["req_id"]
    msgtype = body.get("msgtype")
    chattype = body.get("chattype", "")
    stream_id = new_req_id()
    logger.info(
        f"stream_id: {stream_id} msgtype={msgtype} chattype={chattype}")

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

    thread_id = await get_redis_id(key=userid, id_type="thread_id")
    logger.info(f"msg_body_from: {from_info} - thread_id: {thread_id}")
    r_client = await r_link.get_client()
    aibot_id = body.get("aibotid", "")

    # --- 文本 ---
    if msgtype == "text":
        question = (body.get("text") or {}).get("content") or ""
        pending = await take_pending_images(r_client, userid, thread_id)
        if pending:
            await _handle_vision_flow(
                ws,
                agent=agent,
                callback_req_id=callback_req_id,
                stream_id=stream_id,
                userid=userid,
                thread_id=thread_id,
                chattype=chattype,
                aibot_id=aibot_id,
                r_client=r_client,
                text_prompt=question or DEFAULT_MULTI_IMAGE_PROMPT,
                image_payloads=pending,
                question_prefix=f"[图片追问]（{len(pending)}张）",
            )
            return

        await session_hset(
            redis_client=r_client,
            message_id=stream_id,
            user_id=userid,
            aibot_id=aibot_id,
            chat_type=chattype,
            thread_id=thread_id,
            question=question,
        )
        await _run_agent_stream(
            ws,
            agent=agent,
            callback_req_id=callback_req_id,
            stream_id=stream_id,
            question=question,
            thread_id=thread_id,
            userid=userid,
            r_client=r_client,
            model_name="deepseek",
            placeholder="正在思考...",
        )
        return

    # --- 纯图片：挂起，不即时调模型 ---
    if msgtype == "image":
        if chattype == "group":
            await respond_stream(
                ws,
                callback_req_id,
                stream_id,
                content="群聊请 @机器人 并发送图文消息；纯图片请在单聊中发送",
                finish=True,
            )
            return

        image = body.get("image") or {}
        url = image.get("url")
        aeskey = image.get("aeskey")
        if not url or not aeskey:
            await respond_stream(
                ws,
                callback_req_id,
                stream_id,
                content="图片下载失败，请重新发送",
                finish=True,
            )
            return

        await respond_stream(
            ws,
            callback_req_id,
            stream_id,
            content="正在准备图片...",
            finish=False,
            feedback_id=f"fb-{stream_id}",
        )

        try:
            payload = await prepare_image_for_model(url, aeskey)
            count = await append_pending_image(
                r_client, userid, thread_id, payload
            )
        except PendingFullError as e:
            await respond_stream(
                ws,
                callback_req_id,
                stream_id,
                content=e.user_message,
                finish=True,
                feedback_id=f"fb-{stream_id}",
            )
            return
        except MediaError as e:
            logger.warning(f"图片准备失败: {e.user_message} cause={e.cause}")
            await respond_stream(
                ws,
                callback_req_id,
                stream_id,
                content=e.user_message,
                finish=True,
                feedback_id=f"fb-{stream_id}",
            )
            return
        except Exception as e:
            logger.exception(f"图片挂起异常: {e}")
            await respond_stream(
                ws,
                callback_req_id,
                stream_id,
                content="图片解析失败，请重试",
                finish=True,
                feedback_id=f"fb-{stream_id}",
            )
            return

        await session_hset(
            redis_client=r_client,
            message_id=stream_id,
            user_id=userid,
            aibot_id=aibot_id,
            chat_type=chattype,
            thread_id=thread_id,
            question=f"[图片挂起] 第{count}张",
        )
        await respond_stream(
            ws,
            callback_req_id,
            stream_id,
            content=_pending_ready_message(count),
            finish=True,
            feedback_id=f"fb-{stream_id}",
        )
        return

    # --- 图文混排：合并挂起图 + 本次图文后作答 ---
    if msgtype == "mixed":
        text_part, image_refs = _parse_mixed_items(body)

        if not image_refs:
            pending = await take_pending_images(r_client, userid, thread_id)
            if not text_part and not pending:
                await respond_stream(
                    ws,
                    callback_req_id,
                    stream_id,
                    content="未识别到有效的图文内容，请重试",
                    finish=True,
                )
                return
            if text_part and not pending:
                await session_hset(
                    redis_client=r_client,
                    message_id=stream_id,
                    user_id=userid,
                    aibot_id=aibot_id,
                    chat_type=chattype,
                    thread_id=thread_id,
                    question=text_part,
                )
                await _run_agent_stream(
                    ws,
                    agent=agent,
                    callback_req_id=callback_req_id,
                    stream_id=stream_id,
                    question=text_part,
                    thread_id=thread_id,
                    userid=userid,
                    r_client=r_client,
                    model_name="deepseek",
                    placeholder="正在思考...",
                )
                return
            await _handle_vision_flow(
                ws,
                agent=agent,
                callback_req_id=callback_req_id,
                stream_id=stream_id,
                userid=userid,
                thread_id=thread_id,
                chattype=chattype,
                aibot_id=aibot_id,
                r_client=r_client,
                text_prompt=text_part or DEFAULT_MULTI_IMAGE_PROMPT,
                image_payloads=pending,
                question_prefix=f"[图文合并]（含挂起{len(pending)}张）",
            )
            return

        # 有本次图：先下载，失败则不拿走挂起图
        await respond_stream(
            ws,
            callback_req_id,
            stream_id,
            content="正在识别图片...",
            finish=False,
            feedback_id=f"fb-{stream_id}",
        )

        try:
            mixed_payloads = await _prepare_payloads_from_refs(image_refs)
        except MediaError as e:
            logger.warning(f"mixed 图片准备失败: {e.user_message} cause={e.cause}")
            await respond_stream(
                ws,
                callback_req_id,
                stream_id,
                content=e.user_message,
                finish=True,
                feedback_id=f"fb-{stream_id}",
            )
            return
        except Exception as e:
            logger.exception(f"mixed 图片准备异常: {e}")
            await respond_stream(
                ws,
                callback_req_id,
                stream_id,
                content="图片解析失败，请重试",
                finish=True,
                feedback_id=f"fb-{stream_id}",
            )
            return

        pending = await take_pending_images(r_client, userid, thread_id)
        all_payloads = list(pending) + mixed_payloads
        if not all_payloads:
            await session_hset(
                redis_client=r_client,
                message_id=stream_id,
                user_id=userid,
                aibot_id=aibot_id,
                chat_type=chattype,
                thread_id=thread_id,
                question=text_part or "",
            )
            await _run_agent_stream(
                ws,
                agent=agent,
                callback_req_id=callback_req_id,
                stream_id=stream_id,
                question=text_part or DEFAULT_MULTI_IMAGE_PROMPT,
                thread_id=thread_id,
                userid=userid,
                r_client=r_client,
                model_name="deepseek",
                placeholder="正在思考...",
            )
            return

        text_prompt = text_part or DEFAULT_MULTI_IMAGE_PROMPT
        prefix = (
            f"[图文合并]（含挂起{len(pending)}张）"
            if pending
            else "[图文]"
        )
        await _handle_vision_flow(
            ws,
            agent=agent,
            callback_req_id=callback_req_id,
            stream_id=stream_id,
            userid=userid,
            thread_id=thread_id,
            chattype=chattype,
            aibot_id=aibot_id,
            r_client=r_client,
            text_prompt=text_prompt,
            image_payloads=all_payloads,
            question_prefix=prefix,
            skip_initial_placeholder=True,
        )
        return

    # --- 其他类型 ---
    await respond_stream(
        ws,
        callback_req_id,
        stream_id,
        content=f"暂不支持消息类型：{msgtype}",
        finish=True,
    )
