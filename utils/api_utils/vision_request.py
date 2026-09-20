"""
FastAPI 图文请求校验与多模态 content 拼装
    - VisionRequestError: 图文请求校验异常
    - prepare_vision_turn: 校验 images/provider/model_label 并拼装 user_content
"""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from typing import Any, Optional, Sequence

from robot.agents.model_context import ModelLabel
from robot.tools.message_content import (
    ImageContentError,
    VisionProvider,
    build_vision_user_content,
    image_to_base64_payload,
)
from utils.api_utils.request_models import ImageInput
from utils.logger_manager import LoggerManager

logger = LoggerManager.get_logger(name="vision_request")

MAX_IMAGES_PER_REQUEST = 10
QUESTION_IMAGE_PREFIX = "[图片]"

VISION_MODEL_LABELS: frozenset[str] = frozenset(
    {"deepseek", "minimax_m3", "aihubmix_minimax_m3"}
)

PROVIDER_MODEL_WHITELIST: dict[VisionProvider, frozenset[str]] = {
    "openai": frozenset({"deepseek"}),
    "anthropic": frozenset({"minimax_m3", "aihubmix_minimax_m3"}),
}


class VisionRequestError(Exception):
    """
    图文请求校验异常
    Args:
        user_message(str): 可直接返回给客户端的错误文案
    """

    def __init__(self, user_message: str):
        super().__init__(user_message)
        self.user_message = user_message


@dataclass(frozen=True)
class PreparedVisionTurn:
    """
    校验通过后的图文回合数据
    """
    query_for_db: str
    model_label: ModelLabel
    user_content: Optional[list[dict[str, Any]]]


def _strip_data_url(data: str) -> str:
    """
    剥掉 data URL 前缀，返回纯 base64
    Args:
        data(str): base64 或 data:image/...;base64,...
    Returns:
        str: 纯 base64 字符串
    """
    text = data.strip()
    if text.startswith("data:") and "," in text:
        return text.split(",", 1)[1].strip()
    return text


def _decode_image_bytes(raw_b64: str) -> bytes:
    """
    解码 base64 为图片字节
    Args:
        raw_b64(str): 纯 base64
    Returns:
        bytes: 图片原始字节
    Raises:
        VisionRequestError: base64 非法
    """
    try:
        padded = raw_b64 + "=" * (-len(raw_b64) % 4)
        return base64.b64decode(padded)
    except (binascii.Error, ValueError) as e:
        raise VisionRequestError(
            "图片 base64 无效，请传入合法的 JPEG/PNG/GIF/WEBP base64"
        ) from e


def _payloads_from_images(images: Sequence[ImageInput]) -> list[dict[str, str]]:
    """
    将请求中的图片转为模型 payload 列表
    Args:
        images(Sequence[ImageInput]): 请求图片列表
    Returns:
        list[dict]: [{media_type, data}, ...]
    Raises:
        VisionRequestError: 解码或格式校验失败
    """
    payloads: list[dict[str, str]] = []
    for idx, item in enumerate(images):
        if not item.data or not item.data.strip():
            raise VisionRequestError(f"第 {idx + 1} 张图片 data 为空")
        raw = _decode_image_bytes(_strip_data_url(item.data))
        try:
            payload = image_to_base64_payload(raw)
        except ImageContentError as e:
            raise VisionRequestError(
                f"第 {idx + 1} 张图片：{e.user_message}"
            ) from e
        if item.media_type and item.media_type != payload["media_type"]:
            raise VisionRequestError(
                f"第 {idx + 1} 张图片 media_type 与文件内容不符"
                f"（声明={item.media_type}，实际={payload['media_type']}）"
            )
        payloads.append(payload)
    return payloads


def prepare_vision_turn(
    *,
    query: str,
    model_label: ModelLabel,
    images: Sequence[ImageInput] | None = None,
    provider: Optional[VisionProvider] = None,
) -> PreparedVisionTurn:
    """
    校验图文请求并拼装多模态 user_content
    Args:
        query(str): 用户问题
        model_label(str): 模型标签
        images(Sequence[ImageInput]): 图片列表, default=None
        provider(str): 有图时必填 openai / anthropic, default=None
    Returns:
        PreparedVisionTurn: query_for_db / model_label / user_content
    Raises:
        VisionRequestError: 校验失败
    """
    image_list = list(images or [])
    query_text = (query or "").strip()

    if not image_list:
        return PreparedVisionTurn(
            query_for_db=query if query is not None else "",
            model_label=model_label,
            user_content=None,
        )

    if not query_text:
        msg = "图文问答时 query 不能为空（不支持仅传图片）"
        logger.warning(msg)
        raise VisionRequestError(msg)

    if len(image_list) > MAX_IMAGES_PER_REQUEST:
        msg = f"单次最多上传 {MAX_IMAGES_PER_REQUEST} 张图片，当前 {len(image_list)} 张"
        logger.warning(msg)
        raise VisionRequestError(msg)

    if provider is None:
        msg = "有图时必须传入 provider（openai 或 anthropic）"
        logger.warning(
            f"{msg}: model_label={model_label}, image_count={len(image_list)}"
        )
        raise VisionRequestError(msg)

    allowed_labels = ", ".join(sorted(VISION_MODEL_LABELS))
    if model_label not in VISION_MODEL_LABELS:
        msg = (
            f"模型 {model_label} 不支持图片输入；"
            f"请使用：{allowed_labels}"
        )
        logger.warning(
            f"非 vision 模型带图被拒绝: model_label={model_label}, "
            f"provider={provider}, image_count={len(image_list)}"
        )
        raise VisionRequestError(msg)

    whitelist = PROVIDER_MODEL_WHITELIST.get(provider, frozenset())
    if model_label not in whitelist:
        allowed = ", ".join(sorted(whitelist)) or "（无）"
        msg = (
            f"provider={provider} 与 model_label={model_label} 不匹配；"
            f"该 provider 仅允许：{allowed}"
        )
        logger.warning(msg)
        raise VisionRequestError(msg)

    payloads = _payloads_from_images(image_list)
    user_content = build_vision_user_content(
        query_text, payloads, provider=provider
    )
    query_for_db = f"{QUESTION_IMAGE_PREFIX} {query_text}"
    return PreparedVisionTurn(
        query_for_db=query_for_db,
        model_label=model_label,
        user_content=user_content,
    )
