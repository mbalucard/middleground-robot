"""
运行智能体
    - run_agent: 运行智能体
    - interrypts_judge: AI中断后,人工判断是否继续执行
    - run_agent_astream: 流式运行智能体
    - interrypts_judge_astream: 中断恢复流式运行智能体
"""
from typing import Optional, Tuple, Any, Literal, Dict, List
from langchain_core.messages import HumanMessage
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command

from robot.tools.session_redis import SessionRedis
from robot.tools.interrupt_handling import handle_interrupt_info
from robot.agents.model_context import Context, invoke_config
from utils.logger_manager import LoggerManager
from utils.date_time import timestamp

logger = LoggerManager.get_logger(name="agent_invoke")

# 可选模型名称
ModelLabel = Literal["deepseek", "minimax", "minimax_m3", "deepseek_vision"]
AllowedDecisions = Literal['approve', 'edit', 'reject', 'respond']


async def run_agent(
        agent: CompiledStateGraph,
        query: str,
        thread_id: str = "1001",
        user_id: str = "1001",
        model_name: ModelLabel = "deepseek",
        api_key: Optional[str] = None,
        session_redis: Optional[SessionRedis] = None,):
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
        session_redis(Optional[SessionRedis]): 会话Redis default=None
    Returns:
        智能体响应
    """
    human_message = HumanMessage(content=query)
    config = invoke_config(thread_id, user_id=user_id)
    context = Context(model=model_name, api_key=api_key,
                      thread_id=thread_id, user_id=user_id)
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
        if session_redis:
            interrupt_data = result.interrupts[0]
            interrupt_list = handle_interrupt_info(interrupt_data)
            interrupt_info = {
                "query": query,
                "user_id": user_id,
                "thread_id": thread_id,
                "interrupt_list": interrupt_list,
                "model_label": model_name,
                "api_key": api_key,
                "_t": timestamp(),
                "type": "interrupt"
            }
            await session_redis.set_session(user_id=user_id, thread_id=thread_id, data=interrupt_info)

    return result


async def interrypts_judge(
    agent: CompiledStateGraph,
    user_id: str,
    thread_id: str,
    session_redis: SessionRedis,
    decides: List[AllowedDecisions],
    is_all_decides: bool = False,):
    """
    AI中断后,人工判断是否继续执行
    Args:
        agent: 智能体
        user_id: 用户ID
        thread_id: 线程ID
        session_redis: 会话Redis
        decides: 决策列表
        is_all_decides: 是否全部决策一致
    Returns:
        Optional[Result]: 决策结果,如果中断信息为空,则返回None
    """
    # 获取中断信息
    interrupt_info = await session_redis.get_session(user_id=user_id, thread_id=thread_id)
    if not interrupt_info:
        logger.warning(f"用户当前对话不存在中断信息: user_id={user_id}, thread_id={thread_id}")
        return None
    # 构建决策列表
    decisions = []
    if not is_all_decides:
        if len(decides) != len(interrupt_info.get('interrupt_list', [])):
            logger.warning(f"决策列表长度与中断信息长度不一致: decides={len(decides)}, interrupt_list={len(interrupt_info.get('interrupt_list', []))}")
            return None
        for i in range(len(decides)):
            decide = {"type": decides[i]}
            decisions.append(decide)
    else:
        if len(decides) != 1:
            logger.warning(f"is_all_decides为True时,决策列表长度必须为1,当前长度为{len(decides)}")
            return None
        if decides[0] not in ['approve', 'reject']:
            logger.warning(f"is_all_decides为True时,决策列表仅支持'approve'或'reject',当前元素为{decides[0]}")
            return None
        for i in range(len(interrupt_info.get('interrupt_list', []))):
            decide = {"type": decides[0]}
            decisions.append(decide)
    # 构建配置

    config = invoke_config(
        thread_id=interrupt_info.get('thread_id', ''),
        user_id=interrupt_info.get('user_id', '')
    )
    context = Context(
        model=interrupt_info.get('model_label', 'deepseek'),
        api_key=interrupt_info.get('api_key', '123'),
        thread_id=interrupt_info.get('thread_id'),
        user_id=interrupt_info.get('user_id')
    )
    await session_redis.delete_session(user_id=user_id, thread_id=thread_id)
    # 运行智能体
    try:
        result = await agent.ainvoke(
            Command(resume={"decisions": decisions}),
            config=config,
            context=context,
            version="v2")
        # 检查是否中断
        if result.interrupts:
            interrupt_data = result.interrupts[0]
            interrupt_list = handle_interrupt_info(interrupt_data)
            interrupt_info = {
                "query": interrupt_info.get('query', ''),
                "user_id": user_id,
                "thread_id": thread_id,
                "interrupt_list": interrupt_list,
                "model_label": interrupt_info.get('model_label', 'deepseek'),
                "api_key": interrupt_info.get('api_key', '123'),
                "_t": timestamp(),
                "type": "interrupt"
            }
            await session_redis.set_session(user_id=user_id, thread_id=thread_id, data=interrupt_info)
    except Exception as e:
        logger.error(f"中断恢复运行失败: {e}")
        raise e
    return result

async def run_agent_astream(
    agent: CompiledStateGraph,
    query: str,
    thread_id: str = "1001",
    user_id: str = "1001",
    model_name: ModelLabel = "deepseek",
    api_key: Optional[str] = None,
    session_redis: Optional[SessionRedis] = None,):
    """
    流式运行智能体
    Args:
        agent: 智能体
        query: 查询字符串
        thread_id: 线程ID
        user_id: 用户ID
        model_name: 模型标签
        api_key: 通行密匙
        session_redis: 会话Redis
    Returns:
        Optional[Result]: 决策结果,如果中断信息为空,则返回None
    """
    human_message = HumanMessage(content=query)
    config = invoke_config(thread_id, user_id=user_id)
    context = Context(model=model_name, api_key=api_key,
                      thread_id=thread_id, user_id=user_id)
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
                if session_redis:
                    interrupt_data = data['__interrupt__'][0]
                    interrupt_list = handle_interrupt_info(interrupt_data)
                    interrupt_info = {
                        "query": query,
                        "user_id": user_id,
                        "thread_id": thread_id,
                        "interrupt_list": interrupt_list,
                        "model_label": model_name,
                        "api_key": api_key,
                        "_t": timestamp(),
                        "type": "interrupt"
                    }
                    await session_redis.set_session(user_id=user_id, thread_id=thread_id, data=interrupt_info)
                yield data
    except Exception as e:
        logger.error(f"流式运行智能体失败: {e}")
        raise e


async def interrypts_judge_astream(
    agent: CompiledStateGraph,
    user_id: str,
    thread_id: str,
    session_redis: SessionRedis,
    decides: List[AllowedDecisions],
    is_all_decides: bool = False):
    """
    中断恢复流式运行智能体
    Args:
        agent: 智能体
        user_id: 用户ID
        thread_id: 线程ID
        session_redis: 会话Redis
        decides: 决策列表
        is_all_decides: 是否全部决策一致
    Returns:
        Optional[Result]: 决策结果,如果中断信息为空,则返回None
    """
    # 获取中断信息
    interrupt_info = await session_redis.get_session(user_id=user_id, thread_id=thread_id)
    if not interrupt_info:
        logger.warning(
            f"用户当前对话不存在中断信息: user_id={user_id}, thread_id={thread_id}")
        yield None
        return
    # 构建决策列表
    decisions = []
    if not is_all_decides:
        if len(decides) != len(interrupt_info.get('interrupt_list', [])):
            logger.warning(
                f"决策列表长度与中断信息长度不一致: decides={len(decides)}, interrupt_list={len(interrupt_info.get('interrupt_list', []))}")
            yield None
            return
        for i in range(len(decides)):
            decide = {"type": decides[i]}
            decisions.append(decide)
    else:
        if len(decides) != 1:
            logger.warning(f"is_all_decides为True时,决策列表长度必须为1,当前长度为{len(decides)}")
            yield None
            return
        if decides[0] not in ['approve', 'reject']:
            logger.warning(f"is_all_decides为True时,决策列表仅支持'approve'或'reject',当前元素为{decides[0]}")
            yield None
            return
        for i in range(len(interrupt_info.get('interrupt_list', []))):
            decide = {"type": decides[0]}
            decisions.append(decide)
        
    # 构建配置
    config = invoke_config(
        thread_id=interrupt_info.get('thread_id', ''),
        user_id=interrupt_info.get('user_id', '')
    )
    # 构建上下文
    context = Context(
        model=interrupt_info.get('model_label', 'deepseek'),
        api_key=interrupt_info.get('api_key', '123'),
        thread_id=interrupt_info.get('thread_id'),
        user_id=interrupt_info.get('user_id')
    )
    await session_redis.delete_session(user_id=user_id, thread_id=thread_id)
    # 流式运行智能体
    try:
        async for chunk in agent.astream(
                Command(resume={"decisions": decisions}),
                config=config,
                context=context,
                stream_mode="updates",
                subgraphs=True,
                version='v2',):
            data = chunk['data'] or {}
            if data.get("model"):
                yield data

            if data.get('tools'):
                yield data

            if data.get('__interrupt__'):
                # 更新中断信息
                if session_redis:
                    interrupt_data = data['__interrupt__'][0]
                    interrupt_list = handle_interrupt_info(interrupt_data)
                    interrupt_info = {
                        "query": interrupt_info.get('query', ''),
                        "user_id": user_id,
                        "thread_id": thread_id,
                        "interrupt_list": interrupt_list,
                        "model_label": interrupt_info.get('model_label', 'deepseek'),
                        "api_key": interrupt_info.get('api_key', '123'),
                        "_t": timestamp(),
                        "type": "interrupt"
                    }
                    await session_redis.set_session(user_id=user_id, thread_id=thread_id, data=interrupt_info)
                yield data

    except Exception as e:
        logger.error(f"中断恢复流式运行智能体失败: {e}")
        raise e
