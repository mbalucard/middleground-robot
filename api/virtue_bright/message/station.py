"""
消息站内信相关接口
    - station_message_personal_list 站内信个人列表
"""


from httpx import AsyncClient
from typing import Optional, List

from configs.api_config import deming_env
from api.virtue_bright.general_tools import timestamp, get_current_date, get_date_start_and_end_time
from utils.logger_manager import LoggerManager
from api.virtue_bright.bi.report_args import report_field_args
logger = LoggerManager.get_logger(name="bi_report")

yaoud_env = deming_env
base_url = f"{yaoud_env['url']}/message/stationMessage"
TTL = yaoud_env["timeout"]


async def station_message_personal_list(
    authorization: str,
    tenant_id: Optional[int] = None,
    current: int = 1,
    size: int = 20,
    keyword: Optional[str] = None,
    is_current_enterprise: int = 0,
    message_channels: List[str] = ["msg_channel_one"],
    message_sources: List[int] = [1],
    message_types: List[str] = [],
    read_status: Optional[int] = None,
):
    """
    站内信个人列表
    Args:
        authorization (str): 授权token
        tenant_id (Optional[int]): 租户ID
        current (int): 当前页码
        size (int): 每页大小
        keyword (Optional[str]): 关键字 
            - 标题，内容搜索
        is_current_enterprise (int): 是否当前企业 
            - 0-否 1-是
        message_channels (List[str]): 消息渠道
            - 参数未知
        message_sources (List[int]): 消息来源
            - 参数未知
        message_types (List[str]): 消息类型
            - 可在 query_sys_dict_items_by_dict_code 中查询
        read_status (Optional[int]): 阅读状态 
            - 0-未读 1-已读 None-全部
    """
    url = f"{base_url}/personalList"
    headers = {
        "Authorization": authorization,
        "client-tom": "Y",
        "tenant-id": str(tenant_id) if tenant_id else "",
    }
    payload = {
        "current": current,
        "size": size,
        "keyword":keyword,
        "isCurrentEnterprise": is_current_enterprise,
        "messageChannels": message_channels,
        "messageSources": message_sources,
        "messageTypes": message_types,
        "readStatus": read_status,
    }
    async with AsyncClient(timeout=TTL) as client:
        response = await client.post(url, json=payload, headers=headers,timeout=TTL)
        return response.json()