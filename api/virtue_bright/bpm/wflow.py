"""
工作流
    - get_task_todo_list 获取待办任务列表
"""


from httpx import AsyncClient
from typing import Optional, List

from configs.api_config import deming_env
from api.virtue_bright.general_tools import timestamp
from utils.logger_manager import LoggerManager
logger = LoggerManager.get_logger(name="bi_report")

yaoud_env = deming_env
base_url = f"{yaoud_env['url']}/bpm/wflow"
TTL = yaoud_env["timeout"]



async def get_task_todo_list(
    authorization: str,
    tenant_id: Optional[int] = None,
    current: int = 1,
    size: int = 20,
    keyword: Optional[str] = None,
    order_id: Optional[str] = None,
    organ_name: Optional[str] = None,
    create_user_id: Optional[str] = None,
    create_start_time: Optional[str] = None,
    create_end_time: Optional[str] = None,
    login_enterprise: bool = False,
):
    """
    获取待办任务列表
    Args:
        authorization (str): 授权token
        tenant_id (Optional[int]): 租户ID
        current (int): 当前页码
        size (int): 每页大小
        keyword (Optional[str]): 关键字
            - 事件类型，来源系统
        order_id (Optional[str]): 业务单据号
        organ_name (Optional[str]): 发起人机构名称
        create_user_id (Optional[str]): 创建人ID
            - 可在 get_employee_list 中获取ID
        create_start_time (Optional[str]): 创建开始时间
            - 格式：yyyy-MM-dd
        create_end_time (Optional[str]): 创建结束时间
            - 格式：yyyy-MM-dd
        login_enterprise (bool): 是否当前企业
    """
    url = f"{base_url}/process/task/todoList"
    headers = {
        "Authorization": authorization,
        "client-tom": "Y",
        "tenant-id": str(tenant_id) if tenant_id else "",
    }
    if create_start_time and isinstance(create_start_time, str):
        create_start_time = f"{create_start_time} 00:00:00"
    if create_end_time and isinstance(create_end_time, str):
        create_end_time = f"{create_end_time} 23:59:59"
    params = {
        "current": current,
        "size": size,
        "keyword": keyword if keyword else "",
        "orderId": order_id if order_id else "",
        "organName": organ_name if organ_name else "",
        "createUserId": create_user_id if create_user_id else "",
        "loginEnterprise": login_enterprise,
        "_t": timestamp(),
    }
    if create_start_time:
        params["createStartTime"] = create_start_time
    if create_end_time:
        params["createEndTime"] = create_end_time
    async with AsyncClient(timeout=TTL) as client:
        response = await client.get(url, headers=headers, params=params)
        return response.json()