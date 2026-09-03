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
    value = interrupt_info.value
    action_requests = value["action_requests"]
    review_configs = value["review_configs"]
    config_map = {cfg["action_name"]: cfg for cfg in review_configs}
    
    interrupt_list = []
    for action in action_requests:
        review_config = config_map[action["name"]]
        interrupt_list.append({
            "action_name": action["name"],
            "args": action["args"],
            "description": (
                f"工具执行需要批准, 工具名称: {action['name']}, "
                f"工具参数: {action['args']}"
            ),
            "allowed_decisions": review_config["allowed_decisions"],
        })
    return interrupt_list
