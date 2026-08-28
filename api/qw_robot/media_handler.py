"""
企微媒体处理
    - download_encrypted_media: 下载加密媒体
    - decrypt_wecom_media: AES 解密
    - prepare_image_for_model: 统一入口（下载解密后转模型 payload）
"""

from __future__ import annotations

import base64
from typing import TypedDict, cast

import httpx
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

from robot.tools.message_content import (
    ImageContentError,
    image_to_base64_payload,
)
from utils.logger_manager import LoggerManager

logger = LoggerManager.get_logger(name="media_handler")


class ImagePayload(TypedDict):
    media_type: str
    data: str


class MediaError(Exception):
    """媒体处理业务异常，message 可直接展示给用户。"""

    def __init__(self, user_message: str, *, cause: Exception | None = None):
        super().__init__(user_message)
        self.user_message = user_message
        self.cause = cause


def _parse_aeskey(aeskey: str) -> bytes:
    """解析企微 aeskey（支持 hex 或 base64）。"""
    raw = aeskey.strip()
    if len(raw) == 64 and all(c in "0123456789abcdefABCDEF" for c in raw):
        return bytes.fromhex(raw)
    padded = raw + "=" * ((4 - len(raw) % 4) % 4)
    try:
        return base64.b64decode(padded)
    except Exception as e:
        raise MediaError("图片解析失败，请重试", cause=e) from e


async def download_encrypted_media(url: str, *, timeout: float = 30.0) -> bytes:
    """下载企微加密媒体（URL 约 5 分钟有效）。"""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.content
    except Exception as e:
        logger.error(f"下载媒体失败: {e}")
        raise MediaError("图片下载失败，请重新发送", cause=e) from e


def decrypt_wecom_media(ciphertext: bytes, aeskey: str) -> bytes:
    """
    AES-256-CBC 解密企微媒体。
    IV = aeskey 前 16 字节；PKCS#7，块大小按文档取 32。
    """
    try:
        key = _parse_aeskey(aeskey)
        if len(key) < 32:
            raise ValueError(f"aeskey 长度不足: {len(key)}")
        key32 = key[:32]
        iv = key[:16]
        cipher = AES.new(key32, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(ciphertext)
        # 文档要求填充至 32 字节倍数；若失败再回退 16
        try:
            return unpad(decrypted, 32)
        except ValueError:
            return unpad(decrypted, AES.block_size)
    except MediaError:
        raise
    except Exception as e:
        logger.error(f"解密媒体失败: {e}")
        raise MediaError("图片解析失败，请重试", cause=e) from e


async def prepare_image_for_model(url: str, aeskey: str) -> ImagePayload:
    """下载、解密并封装为模型输入。"""
    encrypted = await download_encrypted_media(url)
    raw = decrypt_wecom_media(encrypted, aeskey)
    try:
        return cast(ImagePayload, image_to_base64_payload(raw))
    except ImageContentError as e:
        raise MediaError(e.user_message, cause=e) from e
