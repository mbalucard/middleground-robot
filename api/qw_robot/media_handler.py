"""
企微媒体处理
    - download_encrypted_media: 下载加密媒体
    - decrypt_wecom_media: AES 解密
    - image_to_base64_payload: 识别格式并转 base64
    - prepare_image_for_model: 统一入口
"""

from __future__ import annotations

import base64
from typing import TypedDict

import httpx
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

from utils.logger_manager import LoggerManager

logger = LoggerManager.get_logger(name="media_handler")

MAX_IMAGE_BYTES = 10 * 1024 * 1024  # MiniMax 单图上限 10MB

_MAGIC_TYPES: list[tuple[bytes, str]] = [
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
    (b"RIFF", "image/webp"),  # WEBP 还需进一步校验
]


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


def detect_image_media_type(data: bytes) -> str:
    """根据文件头识别图片 MIME。"""
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return "image/gif"
    # WEBP: RIFF....WEBP
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    raise MediaError(
        "图片过大或格式不支持（请发 jpeg/png/gif/webp，≤10MB）"
    )


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


def image_to_base64_payload(raw_bytes: bytes) -> ImagePayload:
    """校验大小与格式，转为模型可用的 base64 payload。"""
    if len(raw_bytes) > MAX_IMAGE_BYTES:
        raise MediaError(
            "图片过大或格式不支持（请发 jpeg/png/gif/webp，≤10MB）"
        )
    if len(raw_bytes) < 5:
        raise MediaError(
            "图片过大或格式不支持（请发 jpeg/png/gif/webp，≤10MB）"
        )
    media_type = detect_image_media_type(raw_bytes)
    return {
        "media_type": media_type,
        "data": base64.b64encode(raw_bytes).decode("ascii"),
    }


async def prepare_image_for_model(url: str, aeskey: str) -> ImagePayload:
    """下载、解密并封装为模型输入。"""
    encrypted = await download_encrypted_media(url)
    raw = decrypt_wecom_media(encrypted, aeskey)
    return image_to_base64_payload(raw)
