"""
Agent 流式回复与视觉流程
    - run_agent_stream: 占位气泡后流式刷新；遇 interrupt 发卡
    - handle_vision_flow: 多模态理解并流式文字回复
    - prepare_payloads_from_refs: 企微图片下载解密
"""

from __future__ import annotations

from typing import Any, Optional

from api.qw_api_robot.interrupt_flow import (
    GROUP_INTERRUPT_REPLY,
    INTERRUPT_STREAM_HINT,
    issue_review_card,
)
from api.qw_api_robot.media_handler import MediaError, prepare_image_for_model
from api.qw_api_robot.qw_respond import respond_stream
from api.qw_api_robot.stream_agent import agent_astream
from robot.tools.message_content import DEFAULT_MULTI_IMAGE_PROMPT
from utils.logger_manager import LoggerManager

logger = LoggerManager.get_logger(name="agent_reply")

# 与 API prepare_vision_turn 上限对齐（挂起仍最多 5）
MAX_IMAGES_PER_REQUEST = 10


def payloads_to_api_images(payloads: list[dict]) -> list[dict[str, str]]:
    """
    将本地图片 payload 转为 API images 字段
    Args:
        payloads(list): [{media_type, data}, ...]
    Returns:
        API images 列表
    """
    out: list[dict[str, str]] = []
    for p in payloads:
        if not p.get("data"):
            continue
        item: dict[str, str] = {"data": str(p["data"])}
        if p.get("media_type"):
            item["media_type"] = str(p["media_type"])
        out.append(item)
    return out


async def prepare_payloads_from_refs(image_refs: list[dict]) -> list[dict]:
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


async def run_agent_stream(
    ws,
    *,
    callback_req_id: str,
    stream_id: str,
    question: str,
    thread_id: str,
    userid: str,
    model_name: str = "deepseek",
    images: Optional[list[dict[str, Any]]] = None,
    provider: Optional[str] = None,
    placeholder: str = "正在思考...",
    has_images: bool = False,
    chattype: str = "",
) -> None:
    """
    占位流式气泡后调用 API 并刷新回复；遇 interrupt 则结束 stream 并发审批卡
    Args:
        ws: websocket连接
        callback_req_id(str): 回调请求ID
        stream_id(str): 流式消息ID
        question(str): 用户问题
        thread_id(str): API 会话ID
        userid(str): 用户ID
        model_name(str): 模型标签, default="deepseek"
        images(list): API 图片列表, default=None
        provider: 有图时必填, default=None
        placeholder(str): 占位文案, default="正在思考..."
        has_images(bool): 是否图文请求（影响失败文案）, default=False
        chattype(str): 会话类型, default=""
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
        async for event in agent_astream(
            question=question,
            thread_id=thread_id,
            user_id=userid,
            model_name=model_name,
            images=images,
            provider=provider,  # type: ignore[arg-type]
        ):
            kind = event.get("kind")
            if kind == "interrupt":
                tools = event.get("tools") or []
                message_id = str(event.get("message_id") or "")
                if chattype == "group":
                    await respond_stream(
                        ws,
                        callback_req_id,
                        stream_id,
                        content=GROUP_INTERRUPT_REPLY,
                        finish=True,
                        feedback_id=f"fb-{stream_id}",
                    )
                    return
                finish_text = last or INTERRUPT_STREAM_HINT
                if last and INTERRUPT_STREAM_HINT not in last:
                    finish_text = f"{last}\n\n{INTERRUPT_STREAM_HINT}"
                await respond_stream(
                    ws,
                    callback_req_id,
                    stream_id,
                    content=finish_text,
                    finish=True,
                    feedback_id=f"fb-{stream_id}",
                )
                await issue_review_card(
                    ws,
                    userid=userid,
                    message_id=message_id,
                    tools=tools,
                    passive_req_id=callback_req_id,
                )
                return

            partial = str(event.get("text") or "")
            if not partial:
                continue
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
        logger.exception(f"Agent API 调用失败: {e}")
        last = "图片理解失败，请稍后重试" if has_images else "处理失败，请稍后重试"
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


async def handle_vision_flow(
    ws,
    *,
    callback_req_id: str,
    stream_id: str,
    userid: str,
    thread_id: str,
    text_prompt: str,
    image_refs: Optional[list[dict]] = None,
    image_payloads: Optional[list[dict]] = None,
    skip_initial_placeholder: bool = False,
    provider: str = "openai",
    chattype: str = "",
) -> None:
    """
    多模态理解并流式文字回复（经 HTTP API）
    Args:
        ws: websocket连接
        callback_req_id(str): 回调请求ID
        stream_id(str): 流式消息ID
        userid(str): 用户ID
        thread_id(str): API 会话ID
        text_prompt(str): 用户文本或默认提示
        image_refs(list): 需下载的图片引用, default=None
        image_payloads(list): 已缓存的图片 payload, default=None
        skip_initial_placeholder(bool): 是否跳过「正在识别图片...」, default=False
        provider(str): 视觉协议, default="openai"
        chattype(str): 会话类型, default=""
    """
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
            payloads.extend(await prepare_payloads_from_refs(image_refs))
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

    if len(payloads) > MAX_IMAGES_PER_REQUEST:
        await respond_stream(
            ws,
            callback_req_id,
            stream_id,
            content=(
                f"单次最多上传 {MAX_IMAGES_PER_REQUEST} 张图片，"
                f"当前 {len(payloads)} 张，请减少后重试"
            ),
            finish=True,
            feedback_id=f"fb-{stream_id}",
        )
        return

    query = (text_prompt or "").strip() or DEFAULT_MULTI_IMAGE_PROMPT
    await run_agent_stream(
        ws,
        callback_req_id=callback_req_id,
        stream_id=stream_id,
        question=query,
        thread_id=thread_id,
        userid=userid,
        model_name="deepseek",
        images=payloads_to_api_images(payloads),
        provider=provider,
        placeholder="正在识别图片..." if skip_initial_placeholder else "正在思考...",
        has_images=True,
        chattype=chattype,
    )
