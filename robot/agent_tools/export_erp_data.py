"""
ERP数据导出工具
    - 导出ERP数据至表格,支持Excel和CSV格式
"""

from utils.virtue_bright_erp.get_data import fetch_all_pages

from typing import Literal
import pandas as pd
from robot.agents.model_context import Context
from langchain.tools import ToolRuntime, tool

from configs.general_config import FilePath
from robot.agent_tools.erp_tools import *


Tools_Dict = {
    'get_goods_info': get_goods_info,
    'get_warehouse_info': get_warehouse_info,
    'get_inventory_data': get_inventory_data,
    'get_inventory_audit_summary_data': get_inventory_audit_summary_data,
    'get_shop_available_info': get_shop_available_info,
    'get_shop_retail_info': get_shop_retail_info,
    'get_region_tree_info': get_region_tree_info,
    'get_store_goods_retail_info': get_store_goods_retail_info,
}
Tools_Name = list(Tools_Dict.keys())


@tool('export_erp_data_to_excel', description='导出ERP数据至表格,支持Excel和CSV格式')
async def export_erp_data_to_excel(
    tool_name: str,
    tool_args: dict,
    file_name: str,
    file_type: Literal['xlsx', 'csv'] = 'csv',
    runtime: ToolRuntime[Context] = None):
    """
    导出ERP数据至表格
    Args:
        tool_name: 工具名称
            - 工具名称，与原工具名称一致
        tool_args: 工具参数
            - 调用工具所需的参数，与原工具一致
        file_name: 文件名
            - 文件名，不包含文件类型
        file_type: 文件类型
            - xlsx: Excel文件
            - csv: CSV文件
    Returns:
        dict: {status, message}
    """
    base_path = "/temp"
    export_path = f"{FilePath.ROOT_PATH}/{base_path}"
    if tool_name in Tools_Name:
        function_tool = Tools_Dict.get(tool_name)
        args = {**tool_args, "runtime": runtime}
        result = await fetch_all_pages(function_tool, args)
        data = result.get('data')
        if data:
            df = pd.DataFrame(data)
            if file_type == 'xlsx':
                df.to_excel(f"{export_path}/{file_name}.xlsx", index=False)
            else:
                df.to_csv(f"{export_path}/{file_name}.csv", index=False)
            return {"status": "success", "message": f"数据已导出,文件名为{file_name}.{file_type}","file_path": f"{base_path}/{file_name}.{file_type}"}
        else:
            return {"status": "error", "message": "未找到数据","file_path": ""}

    else:
        return {"status": "error", "message": f"工具名称错误: 支持以下工具: {Tools_Name}","file_path": ""}
