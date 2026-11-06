"""
审批任务工具
    - todo_approval_task: 获取待办审批任务
"""

from langchain.tools import tool, ToolRuntime
from typing import Optional, List
from robot.agents.model_context import Context

from api.virtue_bright.bpm import get_task_todo_list
from utils.virtue_bright_erp.data_process import task_brief_data_process


@tool("todo_approval_task", description="获取待办审批任务")
async def todo_approval_task(
    current: int = 1,
    size: int = 20,
    tenant_id: Optional[int] = None,
    keyword: Optional[str] = None,
    order_id: Optional[str] = None,
    organ_name: Optional[str] = None,
    create_user_id: Optional[str] = None,
    create_start_time: Optional[str] = None,
    create_end_time: Optional[str] = None,
    login_enterprise: bool = False,
    runtime: ToolRuntime[Context] = None
):
    """
    获取待办审批任务
    Args:
        current: 当前页码
        size: 每页大小
        tenant_id: 租户ID
        keyword: 关键字
            - 事件类型
        order_id: 业务单据号
        organ_name: 发起人机构名称
        create_user_id: 创建人ID
            - 可在 get_brief_employee_list 工具中获取员工ID
        create_start_time: 创建开始时间
            - 格式：yyyy-MM-dd
        create_end_time: 创建结束时间
            - 格式：yyyy-MM-dd
        login_enterprise: 是否当前企业
            - True: 当前企业  False: 所有企业
    Returns:
        List[dict]: 待办审批任务简要数据
    """
    authorization = runtime.context.api_key if runtime and runtime.context else None
    if not authorization:
        return {"status": "error", "message": "未授权"}

    result = await get_task_todo_list(
        authorization=authorization,
        current=current,
        size=size,
        keyword=keyword,
        order_id=order_id,
        organ_name=organ_name,
        create_user_id=create_user_id,
        create_start_time=create_start_time,
        create_end_time=create_end_time,
        login_enterprise=login_enterprise
    )
    data = result.get("data")
    if isinstance(data, dict):
        records = data.get("records")
        if isinstance(records, List) and records:
            data_list = task_brief_data_process(records)
            return {
                "status": "success",
                "data": data_list,
                "page_info": {
                    "current": current,
                    "size": size,
                    "pages": data.get("pages"),
                    "total": data.get("total"),
                }
            }
        else:
            return {"status": "success","data":[]} 
    elif isinstance(data, str):
        return {"status": "error", "message": f"{result.get('msg')},{data}"}
    else:
        return {"status": "error", "message": "未找到待办审批任务"}