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
logger = LoggerManager.get_logger(name=__name__)


def run_agent(
        agent: CompiledStateGraph,
        query: str,
        thread_id: str = "1001",
        model_name: Literal["deepseek", "minimax"] = "deepseek",
        api_key: Optional[str] = None,):
    """
    运行智能体
    Args:
        agent: 智能体
        query(str): 查询字符串
        thread_id(str): 线程ID, default="1001"
        model_name(str): 模型名称, default="deepseek"
            - deepseek minimax
        api_key(str): 通行密匙 default=None
    Returns:
        智能体响应
    """
    human_message = HumanMessage(content=query)

    config = invoke_config(thread_id)
    result = agent.invoke(
        {"messages": [human_message]},
        config=config,
        context=Context(model=model_name, api_key=api_key, thread_id=thread_id),
        version="v2")

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
            logger.info(f"Tool Name: {action['name']} -- Args: {action['args']} -- Allowed Decisions: {review_config['allowed_decisions']}")
            print(f"Tool Name: {action['name']}")
            print(f"参数: {action['args']}")
            print(f"允许的决策: {review_config['allowed_decisions']}")
            print("-"*50)

    return result


def interrypts_judge(
        ai_interrupts: Tuple[Any],
        agent: CompiledStateGraph,
        thread_id: str = "1001",
        judge_type: Optional[Literal["approve", "reject"]] = None,
        judge_list: Optional[List(Dict[str, Any])] = None,
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
        config = invoke_config(thread_id)
        logger.critical(f"Decisions: {decisions}")

        result_decisions = agent.invoke(
            Command(resume={"decisions": decisions}),
            config=config,
            context=Context(model=model_name, api_key=api_key, thread_id=thread_id),
            version="v2",
        )
        return result_decisions
    else:
        return None



async def stream_agent(
    agent:CompiledStateGraph,
    question:str,
    thread_id:str,
    user_id:str,
    model_name: Literal["deepseek", "minimax"] = "deepseek",
    api_key: Optional[str] = None,
):
    """
    流式运行智能体
    Args:
        agent: 智能体
        question: 问题
        thread_id: 线程ID
        user_id: 用户ID
        model_name: 模型名称
        api_key: 通行密匙
    """
    config = invoke_config(thread_id=thread_id, user_id=user_id)
    # logger.info(f"config: {config}")
    human_message = HumanMessage(content=question)
    async for chunk in agent.astream(
        {"messages": [human_message]},
        config=config,
        context=Context(model=model_name, api_key=api_key, thread_id=thread_id, user_id=user_id),
        stream_mode="updates",
        subgraphs=True,
        version='v2',
    ):
        data = chunk['data'] or {}
        if data.get("model"):
            msg = data["model"]["messages"][0]
            content = msg.content
            # 纯字符串：直接当回答
            if isinstance(content, str):
                if content:
                    yield f"回答：{content}"
                continue
            # 内容块列表：text 优先于 thinking
            if isinstance(content, list):
                texts = [
                    b.get("text")
                    for b in content
                    if isinstance(b, dict) and b.get("type") == "text" and b.get("text")
                ]
                thinkings = [
                    b.get("thinking")
                    for b in content
                    if isinstance(b, dict) and b.get("type") == "thinking" and b.get("thinking")
                ]
                if texts:
                    for t in texts:
                        yield f"回答：{t}"
                elif thinkings:
                    for t in thinkings:
                        yield f"思考中：{t}"
                # 如需额外提示工具调用，可保留；不要影响 text/thinking 优先级
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        yield f"使用工具：{b.get('name')}"
        elif data.get("tools"):
            tool_msg = data["tools"]["messages"][0]
            yield f"工具结果：{tool_msg.content}"


if __name__ == "__main__":
    from robot.agents.main_agent import build_agent
    import asyncio
    from robot.tools.memory_device import postgres_resources
    question = "现在几点了"
    thread_id = 'test01'
    user_id = "test01"
    async def main():
        async with postgres_resources() as pg:
            agent = build_agent(checkpointer=pg.checkpointer, store=pg.store)
            async for text in stream_agent(agent, question, thread_id, user_id="test01"):
                print(text, flush=True)
    asyncio.run(main())