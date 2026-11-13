"""
企微导出文件账本（Redis，无 TTL）
    - ensure_export_file_ledger: 账本不存在则建空列表
    - append_export_file: 按 file_path 去重登记
    - cleanup_export_files_for_new_thread: 新建 thread 时删旧 thread 本地文件并剔条目
"""

from __future__ import annotations

import json
import os
from typing import Any

from configs.general_config import FilePath
from utils.date_time import timestamp
from utils.logger_manager import LoggerManager
from utils.redis_link import RedisManager

r_link = RedisManager()
logger = LoggerManager.get_logger(name="export_files")


def _redis_key(userid: str) -> str:
    return f"qw_api_file:{userid}"


def _abs_export_path(file_path: str) -> str:
    """
    相对导出路径转绝对路径
    Args:
        file_path(str): 相对路径，如 temp/xxx.csv
    Returns:
        str: 绝对路径
    """
    rel = (file_path or "").strip().lstrip("/")
    return os.path.join(FilePath.ROOT_PATH, rel)


def _parse_list(raw: Any) -> list[dict[str, Any]]:
    """
    将 Redis 值解析为 list[dict]
    Args:
        raw: Redis 原始值
    Returns:
        list[dict]: 账本条目
    """
    if raw is None:
        return []
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    if not isinstance(raw, str) or not raw.strip():
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("qw_api_file 解析失败，视为空列表")
        return []
    if not isinstance(data, list):
        return []
    out: list[dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        file_path = str(item.get("file_path") or "").strip()
        thread_id = str(item.get("thread_id") or "").strip()
        if not file_path or not thread_id:
            continue
        created_at = item.get("created_at")
        try:
            created_at_int = int(created_at) if created_at is not None else 0
        except (TypeError, ValueError):
            created_at_int = 0
        out.append(
            {
                "file_path": file_path,
                "thread_id": thread_id,
                "created_at": created_at_int,
            }
        )
    return out


async def _save_list(userid: str, items: list[dict[str, Any]]) -> None:
    """
    写回账本列表（无 TTL）
    Args:
        userid(str): 企微用户ID
        items(list): list[dict]
    """
    r_client = await r_link.get_client()
    await r_client.set(_redis_key(userid), json.dumps(items, ensure_ascii=False))


async def list_export_files(userid: str) -> list[dict[str, Any]]:
    """
    读取用户导出文件账本
    Args:
        userid(str): 企微用户ID
    Returns:
        list[dict]: [{file_path, thread_id, created_at}, ...]
    """
    r_client = await r_link.get_client()
    raw = await r_client.get(_redis_key(userid))
    return _parse_list(raw)


async def ensure_export_file_ledger(userid: str) -> list[dict[str, Any]]:
    """
    账本不存在则创建空列表并返回
    Args:
        userid(str): 企微用户ID
    Returns:
        list[dict]: 当前账本
    """
    r_client = await r_link.get_client()
    key = _redis_key(userid)
    raw = await r_client.get(key)
    if raw is None:
        await r_client.set(key, "[]")
        return []
    return _parse_list(raw)


async def append_export_file(
    userid: str,
    file_path: str,
    thread_id: str,
) -> None:
    """
    登记导出/合并文件；按 file_path 去重
    Args:
        userid(str): 企微用户ID
        file_path(str): 工具返回的相对路径
        thread_id(str): 当前 API thread_id
    """
    path = (file_path or "").strip()
    tid = (thread_id or "").strip()
    if not path or not tid:
        return

    items = await ensure_export_file_ledger(userid)
    for item in items:
        if item.get("file_path") == path:
            return
    items.append(
        {
            "file_path": path,
            "thread_id": tid,
            "created_at": timestamp(),
        }
    )
    await _save_list(userid, items)


def _delete_local_file(file_path: str) -> None:
    """
    删除本地导出文件；失败只打日志
    Args:
        file_path(str): 相对路径
    """
    abs_path = _abs_export_path(file_path)
    try:
        if os.path.isfile(abs_path):
            os.remove(abs_path)
            logger.info(f"已删除过期导出文件 path={file_path}")
        else:
            logger.warning(f"过期导出文件不存在 path={file_path}")
    except OSError as e:
        logger.warning(f"删除过期导出文件失败 path={file_path}: {e}")


async def cleanup_export_files_for_new_thread(
    userid: str,
    new_thread_id: str,
) -> None:
    """
    新建 thread 时：确保账本存在；删除非本 thread 的本地文件并剔条目
    Args:
        userid(str): 企微用户ID
        new_thread_id(str): 新 API thread_id
    """
    tid = (new_thread_id or "").strip()
    items = await ensure_export_file_ledger(userid)
    if not tid:
        return

    kept: list[dict[str, Any]] = []
    for item in items:
        if item.get("thread_id") == tid:
            kept.append(item)
            continue
        _delete_local_file(str(item.get("file_path") or ""))
    await _save_list(userid, kept)
