"""
企微消息按类型处理
    - handle_text_msg: 文本（可带挂起图）
    - handle_image_msg: 纯图挂起
    - handle_mixed_msg: 图文混排
"""

from __future__ import annotations

from api.qw_api_robot.agent_reply import (
    handle_vision_flow,
    prepare_payloads_from_refs,
    run_agent_stream,
)
from api.qw_api_robot.interrupt_flow import cancel_pending_interrupt_if_any
from api.qw_api_robot.media_handler import MediaError, prepare_image_for_model
from api.qw_api_robot.mes_busy import (
    BUSY_REPLY,
    release_busy,
    try_acquire_busy,
)
from api.qw_api_robot.pending_images import (
    PendingFullError,
    append_pending_image,
    take_pending_images,
)
from api.qw_api_robot.qw_respond import respond_stream
from robot.tools.message_content import DEFAULT_MULTI_IMAGE_PROMPT
from utils.logger_manager import LoggerManager

logger = LoggerManager.get_logger(name="msg_handlers")


def parse_mixed_items(body: dict) -> tuple[str, list[dict]]:
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


def pending_ready_message(count: int) -> str:
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


def should_use_busy(chattype: str) -> bool:
    """
    是否启用单聊消息忙锁
    Args:
        chattype(str): 会话类型
    Returns:
        非群聊时为 True
    """
    return chattype != "group"


async def handle_text_msg(
    ws,
    *,
    r_client,
    callback_req_id: str,
    stream_id: str,
    userid: str,
    thread_id: str,
    body: dict,
    chattype: str,
) -> None:
    """
    处理文本消息（可合并挂起图）
    Args:
        ws: websocket连接
        r_client: Redis 客户端
        callback_req_id(str): 回调请求ID
        stream_id(str): 流式消息ID
        userid(str): 用户ID
        thread_id(str): API 会话ID
        body(dict): 企微回调 body
        chattype(str): 会话类型
    """
    question = (body.get("text") or {}).get("content") or ""
    busy_token: str | None = None
    if should_use_busy(chattype):
        busy_token = await try_acquire_busy(r_client, userid, thread_id)
        if busy_token is None:
            await respond_stream(
                ws,
                callback_req_id,
                stream_id,
                content=BUSY_REPLY,
                finish=True,
            )
            return
    try:
        if chattype != "group":
            await cancel_pending_interrupt_if_any(
                ws, userid=userid, thread_id=thread_id
            )
        pending = await take_pending_images(r_client, userid, thread_id)
        if pending:
            await handle_vision_flow(
                ws,
                callback_req_id=callback_req_id,
                stream_id=stream_id,
                userid=userid,
                thread_id=thread_id,
                text_prompt=question or DEFAULT_MULTI_IMAGE_PROMPT,
                image_payloads=pending,
                chattype=chattype,
            )
            return

        await run_agent_stream(
            ws,
            callback_req_id=callback_req_id,
            stream_id=stream_id,
            question=question,
            thread_id=thread_id,
            userid=userid,
            model_name="deepseek",
            placeholder="正在思考...",
            chattype=chattype,
        )
    finally:
        if busy_token is not None:
            await release_busy(r_client, userid, thread_id, busy_token)


async def handle_image_msg(
    ws,
    *,
    r_client,
    callback_req_id: str,
    stream_id: str,
    userid: str,
    thread_id: str,
    body: dict,
    chattype: str,
) -> None:
    """
    处理纯图片：挂起，不即时调模型
    Args:
        ws: websocket连接
        r_client: Redis 客户端
        callback_req_id(str): 回调请求ID
        stream_id(str): 流式消息ID
        userid(str): 用户ID
        thread_id(str): API 会话ID
        body(dict): 企微回调 body
        chattype(str): 会话类型
    """
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
        count = await append_pending_image(r_client, userid, thread_id, payload)
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

    await respond_stream(
        ws,
        callback_req_id,
        stream_id,
        content=pending_ready_message(count),
        finish=True,
        feedback_id=f"fb-{stream_id}",
    )


async def handle_mixed_msg(
    ws,
    *,
    r_client,
    callback_req_id: str,
    stream_id: str,
    userid: str,
    thread_id: str,
    body: dict,
    chattype: str,
) -> None:
    """
    处理图文混排：合并挂起图 + 本次图文后作答
    Args:
        ws: websocket连接
        r_client: Redis 客户端
        callback_req_id(str): 回调请求ID
        stream_id(str): 流式消息ID
        userid(str): 用户ID
        thread_id(str): API 会话ID
        body(dict): 企微回调 body
        chattype(str): 会话类型
    """
    text_part, image_refs = parse_mixed_items(body)

    busy_token: str | None = None
    if should_use_busy(chattype):
        busy_token = await try_acquire_busy(r_client, userid, thread_id)
        if busy_token is None:
            await respond_stream(
                ws,
                callback_req_id,
                stream_id,
                content=BUSY_REPLY,
                finish=True,
            )
            return
    try:
        if chattype != "group":
            await cancel_pending_interrupt_if_any(
                ws, userid=userid, thread_id=thread_id
            )
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
                await run_agent_stream(
                    ws,
                    callback_req_id=callback_req_id,
                    stream_id=stream_id,
                    question=text_part,
                    thread_id=thread_id,
                    userid=userid,
                    model_name="deepseek",
                    placeholder="正在思考...",
                    chattype=chattype,
                )
                return
            await handle_vision_flow(
                ws,
                callback_req_id=callback_req_id,
                stream_id=stream_id,
                userid=userid,
                thread_id=thread_id,
                text_prompt=text_part or DEFAULT_MULTI_IMAGE_PROMPT,
                image_payloads=pending,
                chattype=chattype,
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
            mixed_payloads = await prepare_payloads_from_refs(image_refs)
        except MediaError as e:
            logger.warning(
                f"mixed 图片准备失败: {e.user_message} cause={e.cause}"
            )
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
            await run_agent_stream(
                ws,
                callback_req_id=callback_req_id,
                stream_id=stream_id,
                question=text_part or DEFAULT_MULTI_IMAGE_PROMPT,
                thread_id=thread_id,
                userid=userid,
                model_name="deepseek",
                placeholder="正在思考...",
                chattype=chattype,
            )
            return

        await handle_vision_flow(
            ws,
            callback_req_id=callback_req_id,
            stream_id=stream_id,
            userid=userid,
            thread_id=thread_id,
            text_prompt=text_part or DEFAULT_MULTI_IMAGE_PROMPT,
            image_payloads=all_payloads,
            skip_initial_placeholder=True,
            chattype=chattype,
        )
    finally:
        if busy_token is not None:
            await release_busy(r_client, userid, thread_id, busy_token)
