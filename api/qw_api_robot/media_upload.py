"""
企微长连接临时素材上传
    - upload_local_file: 分片上传本地文件，返回 media_id
    - resolve_export_abs_path: 相对导出路径转绝对路径
    - send_exported_files: 上传并被动回复文件，成功后删本地
"""

from __future__ import annotations

import base64
import hashlib
import math
import os
from pathlib import Path
from typing import Any

from api.qw_api_robot.general_tools import new_req_id, send_and_wait_response
from api.qw_api_robot.qw_respond import respond_file, respond_markdown
from configs.general_config import FilePath
from utils.logger_manager import LoggerManager

logger = LoggerManager.get_logger(name="media_upload")

# 单分片 Base64 编码前上限 512KB；普通文件不超过 20MB
CHUNK_SIZE = 512 * 1024
MAX_FILE_SIZE = 20 * 1024 * 1024
MAX_CHUNKS = 100


class MediaUploadError(Exception):
    """上传或发送文件业务异常，message 可展示给用户。"""

    def __init__(self, user_message: str, *, cause: Exception | None = None):
        super().__init__(user_message)
        self.user_message = user_message
        self.cause = cause


def resolve_export_abs_path(file_path: str) -> str:
    """
    将工具返回的相对路径转为绝对路径
    Args:
        file_path(str): 相对路径，如 /temp/xxx.csv
    Returns:
        str: 绝对路径
    """
    rel = (file_path or "").strip().lstrip("/")
    return os.path.join(FilePath.ROOT_PATH, rel)


def _file_md5(abs_path: str) -> str:
    h = hashlib.md5()
    with open(abs_path, "rb") as f:
        while True:
            block = f.read(1024 * 1024)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


async def upload_local_file(
    ws,
    abs_path: str,
    *,
    media_type: str = "file",
) -> str:
    """
    分片上传本地文件，返回 media_id
    Args:
        ws: websocket连接
        abs_path(str): 本地绝对路径
        media_type(str): 素材类型, default="file"
            - file / image / voice / video
    Returns:
        str: media_id
    """
    path = Path(abs_path)
    if not path.is_file():
        raise MediaUploadError(f"文件不存在：{path.name}")

    total_size = path.stat().st_size
    if total_size < 5:
        raise MediaUploadError(f"文件过小，无法发送：{path.name}")
    if total_size > MAX_FILE_SIZE:
        raise MediaUploadError(f"文件超过 20MB，无法发送：{path.name}")

    total_chunks = max(1, math.ceil(total_size / CHUNK_SIZE))
    if total_chunks > MAX_CHUNKS:
        raise MediaUploadError(f"文件分片过多，无法发送：{path.name}")

    filename = path.name
    md5 = _file_md5(abs_path)

    init_payload = {
        "cmd": "aibot_upload_media_init",
        "headers": {"req_id": new_req_id()},
        "body": {
            "type": media_type,
            "filename": filename,
            "total_size": total_size,
            "total_chunks": total_chunks,
            "md5": md5,
        },
    }
    init_resp = await send_and_wait_response(ws, init_payload, timeout=30.0)
    if init_resp.get("errcode", 0) != 0:
        logger.error(f"upload init 失败: {init_resp}")
        raise MediaUploadError(f"文件上传失败：{filename}")
    upload_id = (init_resp.get("body") or {}).get("upload_id")
    if not upload_id:
        raise MediaUploadError(f"文件上传失败：{filename}")

    with open(abs_path, "rb") as f:
        for chunk_index in range(total_chunks):
            raw = f.read(CHUNK_SIZE)
            if not raw:
                break
            chunk_payload = {
                "cmd": "aibot_upload_media_chunk",
                "headers": {"req_id": new_req_id()},
                "body": {
                    "upload_id": upload_id,
                    "chunk_index": str(chunk_index),
                    "base64_data": base64.b64encode(raw).decode("ascii"),
                },
            }
            chunk_resp = await send_and_wait_response(
                ws, chunk_payload, timeout=60.0
            )
            if chunk_resp.get("errcode", 0) != 0:
                logger.error(
                    f"upload chunk 失败 index={chunk_index}: {chunk_resp}"
                )
                raise MediaUploadError(f"文件上传失败：{filename}")

    finish_payload = {
        "cmd": "aibot_upload_media_finish",
        "headers": {"req_id": new_req_id()},
        "body": {"upload_id": upload_id},
    }
    finish_resp = await send_and_wait_response(ws, finish_payload, timeout=60.0)
    if finish_resp.get("errcode", 0) != 0:
        logger.error(f"upload finish 失败: {finish_resp}")
        raise MediaUploadError(f"文件上传失败：{filename}")

    media_id = (finish_resp.get("body") or {}).get("media_id")
    if not media_id:
        raise MediaUploadError(f"文件上传失败：{filename}")
    logger.info(f"upload ok filename={filename} media_id={media_id}")
    return str(media_id)


async def send_exported_files(
    ws,
    callback_req_id: str,
    pending_files: list[dict[str, Any]],
) -> None:
    """
    上传并被动回复导出文件；成功后删除本地；失败补文字
    Args:
        ws: websocket连接
        callback_req_id(str): 消息回调 req_id
        pending_files(list): [{file_path, file_name?}, ...]
            - file_path: 工具返回的相对路径
    """
    for item in pending_files:
        rel = str(item.get("file_path") or "").strip()
        display_name = str(item.get("file_name") or Path(rel).name or "文件")
        if not rel:
            await respond_markdown(
                ws,
                callback_req_id,
                f"文件发送失败：{display_name}（路径无效）",
            )
            continue

        abs_path = resolve_export_abs_path(rel)
        try:
            media_id = await upload_local_file(ws, abs_path, media_type="file")
            resp = await respond_file(ws, callback_req_id, media_id)
            if resp.get("errcode", 0) != 0:
                logger.error(
                    f"respond_file 失败 name={display_name} resp={resp}"
                )
                await respond_markdown(
                    ws,
                    callback_req_id,
                    f"文件发送失败：{display_name}，请稍后重试",
                )
                continue
            try:
                os.remove(abs_path)
            except OSError as e:
                logger.warning(f"删除本地文件失败 path={abs_path}: {e}")
        except MediaUploadError as e:
            logger.warning(
                f"发送导出文件失败 name={display_name}: {e.user_message}"
            )
            await respond_markdown(ws, callback_req_id, e.user_message)
        except Exception as e:
            logger.exception(f"发送导出文件异常 name={display_name}: {e}")
            await respond_markdown(
                ws,
                callback_req_id,
                f"文件发送失败：{display_name}，请稍后重试",
            )
