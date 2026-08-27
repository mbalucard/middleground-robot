"""
模型消息 content 拼装与多模态辅助
    - ImageContentError: 图片内容处理异常
    - vision_model_name: provider 映射为模型名称
    - build_vision_user_content: 构造多模态 HumanMessage content
    - detect_image_media_type: 根据文件头识别图片 MIME
    - image_to_base64_payload: 校验并转为模型可用的 base64 payload
    - is_image_content_block: 识别图片 content 块
    - strip_images_from_content: 从单条消息 content 中去掉图片块
    - strip_images_from_messages: 从消息列表中去掉图片块
"""

from __future__ import annotations

import base64
from collections.abc import Sequence
from typing import Any, Literal

from langchain_core.messages import BaseMessage

VisionProvider = Literal["openai", "anthropic"]

DEFAULT_IMAGE_PROMPT = "请描述这张图片的内容"
DEFAULT_MULTI_IMAGE_PROMPT = "请根据这些图片回答"

MAX_IMAGE_BYTES = 10 * 1024 * 1024  # MiniMax 单图上限 10MB

IMAGE_STRIP_HINT = "（用户曾附带图片；具体内容见后续助手对该图的描述）"


class ImageContentError(Exception):
    """
    图片内容处理异常
    Args:
        user_message(str): 可直接展示给用户的错误文案
        cause(Exception): 原始异常, default=None
    """

    def __init__(self, user_message: str, *, cause: Exception | None = None):
        super().__init__(user_message)
        self.user_message = user_message
        self.cause = cause


def vision_model_name(provider: VisionProvider) -> str:
    """
    provider 映射为模型名称
    Args:
        provider(str): 识图协议风格, openai / anthropic
    Returns:
        str: 模型名称 deepseek_vision / minimax_m3
    """
    return "deepseek_vision" if provider == "openai" else "minimax_m3"


def build_vision_user_content(
    text_prompt: str,
    image_payloads: list[dict],
    provider: VisionProvider = "openai",
) -> list[dict]:
    """
    构造多模态 HumanMessage content
    Args:
        text_prompt(str): 文本提示
        image_payloads(list[dict]): 图片 payload 列表, 每项含 media_type / data
        provider(str): 识图协议风格, default="openai"
            - openai: OpenAI Chat Completions 风格（DeepSeek Vision）
            - anthropic: Anthropic Messages 风格（MiniMax-M3）
    Returns:
        list[dict]: HumanMessage 可用的 content 块列表
    """
    blocks: list[dict] = [{"type": "text", "text": text_prompt}]
    for payload in image_payloads:
        media_type = payload["media_type"]
        data = payload["data"]
        if provider == "openai":
            blocks.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{media_type};base64,{data}",
                        "detail": "auto",
                    },
                }
            )
        else:
            blocks.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": data,
                    },
                }
            )
    return blocks


def detect_image_media_type(data: bytes) -> str:
    """
    根据文件头识别图片 MIME
    Args:
        data(bytes): 图片原始字节
    Returns:
        str: MIME 类型, 如 image/jpeg
    Raises:
        ImageContentError: 格式不支持
    """
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return "image/gif"
    # WEBP: RIFF....WEBP
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    raise ImageContentError(
        "图片过大或格式不支持（请发 jpeg/png/gif/webp，≤10MB）"
    )


def image_to_base64_payload(raw_bytes: bytes) -> dict[str, str]:
    """
    校验大小与格式, 转为模型可用的 base64 payload
    Args:
        raw_bytes(bytes): 图片原始字节
    Returns:
        dict[str, str]: 含 media_type / data 的 payload
    Raises:
        ImageContentError: 过大或格式不支持
    """
    if len(raw_bytes) > MAX_IMAGE_BYTES:
        raise ImageContentError(
            "图片过大或格式不支持（请发 jpeg/png/gif/webp，≤10MB）"
        )
    if len(raw_bytes) < 5:
        raise ImageContentError(
            "图片过大或格式不支持（请发 jpeg/png/gif/webp，≤10MB）"
        )
    media_type = detect_image_media_type(raw_bytes)
    return {
        "media_type": media_type,
        "data": base64.b64encode(raw_bytes).decode("ascii"),
    }


def is_image_content_block(block: Any) -> bool:
    """
    识别 OpenAI / Anthropic 风格的图片 content 块
    Args:
        block(Any): content 中的单个块
    Returns:
        bool: 是否为图片相关块
    """
    if not isinstance(block, dict):
        return False
    block_type = block.get("type")
    if block_type in ("image", "image_url"):
        return True
    # OpenAI file 块携带 inline 图或 file_id 时一并剥掉，避免非 vision 400
    if block_type == "file" and (
        block.get("file_id") or block.get("file_data")
    ):
        return True
    return False


def strip_images_from_content(content: Any) -> Any:
    """
    从单条消息 content 中去掉图片块
    Args:
        content(Any): 消息 content（str 或块列表）
    Returns:
        Any: 剥图后的 content；无图或为 str 时原样返回
            - 曾含图: 保留 text, 并追加提示句；无文字则仅保留提示句
    """
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return content

    had_image = False
    kept: list[Any] = []
    for block in content:
        if is_image_content_block(block):
            had_image = True
            continue
        kept.append(block)

    if not had_image:
        return content

    texts = [
        b.get("text", "")
        for b in kept
        if isinstance(b, dict) and b.get("type") == "text" and b.get("text")
    ]
    # 非 text 的保留块（如 thinking）一并留下，再追加提示
    non_text = [
        b
        for b in kept
        if not (isinstance(b, dict) and b.get("type") == "text")
    ]
    hint_block = {"type": "text", "text": IMAGE_STRIP_HINT}
    text_blocks = [{"type": "text", "text": t} for t in texts]
    text_blocks.append(hint_block)
    result = text_blocks + non_text
    if len(result) == 1 and result[0].get("type") == "text":
        return result[0]["text"]
    return result


def strip_images_from_messages(
    messages: Sequence[BaseMessage],
) -> list[BaseMessage]:
    """
    从消息列表中去掉图片块（不修改原对象 / checkpoint）
    Args:
        messages(Sequence[BaseMessage]): 原始消息列表
    Returns:
        list[BaseMessage]: 剥图后的消息副本列表
    """
    out: list[BaseMessage] = []
    for msg in messages:
        new_content = strip_images_from_content(msg.content)
        if new_content is msg.content:
            out.append(msg)
        else:
            out.append(msg.model_copy(update={"content": new_content}))
    return out
