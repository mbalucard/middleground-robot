"""
中断处理工具
    - handle_interrupt_info: 处理中断信息
"""

from typing import List, Optional, Any


from langgraph.types import Interrupt


def handle_interrupt_info(interrupt_info: Interrupt) -> List[Any]:
    """
    处理中断信息
    Args:
        interrupt_info: 中断信息
    Returns:
        List[Any]: 中断信息列表
    """
    interrupt_list = []
    value = interrupt_info.value
    for i in range(len(value)):
        interrupt_dict = {
            "action_name": value['review_configs'][i]['action_name'],
            "args": value['action_requests'][i]['args'],
            "description": f"工具执行需要批准, 工具名称: {value['action_requests'][i]['name']}, 工具参数: {value['action_requests'][i]['args']}",
            "allowed_decisions": value['review_configs'][i]['allowed_decisions']
        }
        interrupt_list.append(interrupt_dict)
    return interrupt_list
