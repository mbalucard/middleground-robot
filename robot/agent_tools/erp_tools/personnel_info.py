"""
人员信息工具
"""

from langchain.tools import tool, ToolRuntime
from typing import Optional, List
from robot.agents.model_context import Context

from utils.virtue_bright_erp.data_process import employee_data_process
from api.virtue_bright.infra.external import get_employee_list


@tool('get_brief_employee_list', description='获取员工简易信息列表')
async def get_brief_employee_list(
    keyword: Optional[str] = None,
    tenant_id: Optional[int] = None,
    runtime: ToolRuntime[Context] = None
):
    """
    获取员工简易信息列表
    Args:
        keyword: 关键字
            - 可搜索内容：姓名，工号，电话
        tenant_id: 租户ID
    Returns:
        List[dict]: 员工简易信息列表
    """
    authorization = runtime.context.api_key if runtime and runtime.context else None
    if not authorization:
        return {"status": "error", "message": "未授权"}
    result = await get_employee_list(
        authorization=authorization,
        tenant_id=tenant_id,
        keyword=keyword,
    )
    data = result['data']
    if data and isinstance(data, list):
        data_list = employee_data_process(data)
        return {
            "status": "success",
            "data": data_list,
            "page_info": {"total": len(data_list)}
        }
    elif isinstance(data, str):
        return {"status": "error", "message": f"{result.get('msg')},{data}"}
    else:
        return {"status": "error", "message": "获取员工简易信息列表失败"}
