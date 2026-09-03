"""
运行智能体
    - run_agent: 运行智能体
    - interrypts_judge: AI中断后,人工判断是否继续执行
"""
from typing import Optional, Tuple, Any, Literal, Dict, List
from langchain_core.messages import HumanMessage
from robot.agents.model_context import Context, invoke_config
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command

from utils.logger_manager import LoggerManager

logger = LoggerManager.get_logger(name="agent_invoke")

# 可选模型名称
ModelLabel = Literal["deepseek", "minimax", "minimax_m3", "deepseek_vision"]


async def run_agent(
        agent: CompiledStateGraph,
        query: str,
        thread_id: str = "1001",
        user_id: str = "1001",
        model_name: ModelLabel = "deepseek",
        api_key: Optional[str] = None,):
    """
    运行智能体
    Args:
        agent: 智能体
        query(str): 查询字符串
        thread_id(str): 线程ID, default="1001"
        user_id(str): 用户ID, default="1001"
        model_name(str): 模型名称, default="deepseek"
            - deepseek / minimax / minimax_m3 / deepseek_vision
        api_key(str): 通行密匙 default=None
    Returns:
        智能体响应
    """
    human_message = HumanMessage(content=query)
    config = invoke_config(thread_id, user_id=user_id)
    context = Context(model=model_name, api_key=api_key, thread_id=thread_id, user_id=user_id)
    try:
        result = await agent.ainvoke(
            {"messages": [human_message]},
            config=config,
            context=context,
            version="v2")
    except Exception as e:
        logger.error(f"运行智能体失败: {e}")
        raise e

    # 检查执行是否被中断
    if result.interrupts:
        # 提取中断信息
        interrupt_value = result.interrupts[0].value
        action_requests = interrupt_value["action_requests"]
        review_configs = interrupt_value["review_configs"]
        # 创建一个从工具名称到审查配置的查找映射
        config_map = {cfg["action_name"]: cfg for cfg in review_configs}
        # 向用户展示待处理操作
        print("="*20+"工具中断信息"+"="*20)
        for action in action_requests:
            review_config = config_map[action["name"]]
            logger.info(
                f"Tool Name: {action['name']} -- Args: {action['args']} -- Allowed Decisions: {review_config['allowed_decisions']}")
            print(f"Tool Name: {action['name']}")
            print(f"参数: {action['args']}")
            print(f"允许的决策: {review_config['allowed_decisions']}")
            print("-"*50)

    return result


async def interrypts_judge(
        ai_interrupts: Tuple[Any],
        agent: CompiledStateGraph,
        user_id: str = "1001",
        thread_id: str = "1001",
        judge_type: Optional[Literal["approve", "reject"]] = None,
        judge_list: Optional[List[Dict[str, Any]]] = None,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,):
    """
    AI中断后,人工判断是否继续执行
    Args:
        ai_interrupts(Tuple[Any]): 中断信息
        agent(CompiledStateGraph): 智能体
        config(Dict[str, Any]): AI调用配置,必须与中断前AI调用配置相同
        judge_type(Optional[Literal["approve", "reject"]]): 决策类型 default=None
            - approve: 继续执行
            - reject: 拒绝执行
        judge_list(Optional[List(Dict[str, Any])]): 决策列表 default=None
            - judge_list = [{"type": "approve"}, {"type": "reject"}]
            - 当judge_list 不为空 judge_type 无效
            - 当参数为“edit”时, edited_action 参考中断信息中action_requests的name和args
        model_name(Optional[str]): 模型名称 default=None
        api_key(Optional[str]): 通行密匙 default=None
    Returns:
        Optional[Result]: 决策结果,如果中断信息为空,则返回None
    """
    if ai_interrupts:
        interrupt_value = ai_interrupts[0].value
        action_requests = interrupt_value["action_requests"]
        if judge_list:
            decisions = judge_list
        else:
            decisions = [{"type": judge_type} for _ in action_requests]
        config = invoke_config(thread_id, user_id=user_id)
        context = Context(model=model_name, api_key=api_key, thread_id=thread_id, user_id=user_id)
        logger.critical(f"Decisions: {decisions}")
        try:
            result_decisions = await agent.ainvoke(
                Command(resume={"decisions": decisions}),
                config=config,
                context=context,
                version="v2",
            )
            return result_decisions
        except Exception as e:
            logger.error(f"人工判断是否继续执行失败: {e}")
            raise e
    else:
        return None


async def run_agent_astream(
    agent: CompiledStateGraph,
    query: str,
    thread_id: str = "1001",
    user_id: str = "1001",
    model_name: ModelLabel = "deepseek",
    api_key: Optional[str] = None,):
    """
    运行智能体
    Args:
        agent: 智能体
        query: 查询字符串
        thread_id: 线程ID
        user_id: 用户ID
        model_name: 模型标签
        api_key: 通行密匙
    Returns:
        Optional[Result]: 决策结果,如果中断信息为空,则返回None
    """
    human_message = HumanMessage(content=query)
    config = invoke_config(thread_id, user_id=user_id)
    context = Context(model=model_name, api_key=api_key, thread_id=thread_id, user_id=user_id)
    try:
        async for chunk in agent.astream(
            {"messages": [human_message]},
            config=config,
            context=context,
            stream_mode="updates",
            subgraphs=True,
            version='v2',
        ):
            data = chunk['data'] or {}
            if data.get("model"):
                yield data

            if data.get('tools'):
                yield data

            if data.get('__interrupt__'):
                yield data
    except Exception as e:
        logger.error(f"流式运行智能体失败: {e}")
        raise e