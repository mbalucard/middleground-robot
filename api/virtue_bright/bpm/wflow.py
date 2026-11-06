"""
工作流
    - get_task_todo_list 获取待办任务列表
"""


from httpx import AsyncClient
from typing import Optional, List, Literal

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
    result: Optional[Literal["process-end", "in-approval",
                             "refuse-end", "cancel-end"]] = None,
    task_type: Literal["todo", "done", "initiated"] = "todo",
    show_mine: int = 1,
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
        result (Optional[Literal["process-end", "in-approval", "refuse-end", "cancel-end"]]): 结果状态
            - process-end 已审批  in-approval 审批中  refuse-end 已驳回  cancel-end 已撤回
        task_type (Literal["todo", "done", "initiated"]): 任务类型
            - todo: 待办  done: 已办  initiated: 已发起
        show_mine (int): 是否仅显示我的任务
            - 1: 仅显示我的任务 0: 显示所有任务
    """
    if task_type == "todo":
        url = f"{base_url}/process/task/todoList"
    elif task_type == "done":
        url = f"{base_url}/process/task/idoList"
    elif task_type == "initiated":
        url = f"{base_url}/process/mySubmitted"
    else:
        raise ValueError(f"Invalid task type: {task_type}")

    headers = {
        "Authorization": authorization,
        "client-tom": "Y",
        "tenant-id": str(tenant_id) if tenant_id else "",
    }
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
    # 时间处理
    if create_start_time and isinstance(create_start_time, str):
        create_start_time = f"{create_start_time} 00:00:00"
        params["createStartTime"] = create_start_time
    if create_end_time and isinstance(create_end_time, str):
        create_end_time = f"{create_end_time} 23:59:59"
        params["createEndTime"] = create_end_time

    if task_type == "done" or task_type == "initiated":
        if result:
            params["result"] = result
    if task_type == "done":
        params["showMine"] = show_mine

    
    async with AsyncClient(timeout=TTL) as client:
        response = await client.get(url, headers=headers, params=params)
        return response.json()
