"""
企微流式运行智能体
    - agent_astream: 流式运行智能体（含会话/工具调用落库）
"""
from typing import Optional, Any, Literal, Dict, List, Union

from langchain_core.messages import HumanMessage
from langgraph.graph.state import CompiledStateGraph
import redis.asyncio as redis

from robot.agents.model_context import Context, invoke_config
from api.qw_robot.session_manager import session_hset, tool_calls_hset
from utils.logger_manager import LoggerManager

logger = LoggerManager.get_logger(name="agent_astream")

ModelName = Literal["deepseek", "minimax", "minimax_m3", "deepseek_vision"]
UserContent = Union[str, List[Dict[str, Any]]]


async def agent_astream(
    agent: CompiledStateGraph,
    question: str,
    thread_id: str,
    user_id: str,
    model_name: ModelName = "deepseek",
    api_key: Optional[str] = None,
    message_id: Optional[str] = None,
    redis_client: Optional[redis.Redis] = None,
    user_content: Optional[UserContent] = None,):
    """
    流式运行智能体
    Args:
        agent: 智能体
        question: 问题（兼容旧调用；有 user_content 时仅作兜底）
        thread_id: 线程ID
        user_id: 用户ID
        model_name: 模型名称 deepseek / minimax / minimax_m3 / deepseek_vision
        api_key: 通行密匙
        message_id: 消息ID
        user_content: 优先使用的用户消息内容（str 或多模态 content 列表）
    """
    mes_list = []
    # 初始化消息配置
    config = invoke_config(thread_id=thread_id, user_id=user_id)
    content = user_content if user_content is not None else question
    human_message = HumanMessage(content=content)
    async for chunk in agent.astream(
        {"messages": [human_message]},
        config=config,
        context=Context(model=model_name, api_key=api_key,
                        thread_id=thread_id, user_id=user_id),
        stream_mode="updates",  # 流式更新模式
        subgraphs=True,  # 是否显示工具或子代理反馈信息
        version='v2',
    ):
        data = chunk['data'] or {}
        if data.get("model"):
            mes_list.append(data.get("model").get("messages")[-1])
            msg = data["model"]["messages"][-1]
            # 工具调用存表
            tool_calls = msg.tool_calls
            if tool_calls and redis_client:
                for tool_call in tool_calls:
                    await tool_calls_hset(
                        redis_client=redis_client,
                        message_id=message_id,
                        tool_call_id=tool_call.get("id"),
                        tool_name=tool_call.get("name"),
                        tool_input=str(tool_call.get("args")),
                    )
            # 消息处理
            content = msg.content
            # 纯字符串：直接当回答
            if isinstance(content, str):
                if content:
                    yield f"回答：{content}"
                if content and not getattr(msg, "tool_calls", None):
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
            # 工具调用及参数
            if not content:
                logger.info(f"tool_calls 调用参数列表: {tool_calls}")
                if tool_calls:
                    for tool_call in tool_calls:
                        yield f"使用工具：{tool_call.get('name')} - 参数：{tool_call.get('args')}"
        # 工具返回结果
        elif data.get("tools"):
            tool_msg = data["tools"]["messages"][-1]
            # 工具返回结果存表
            if redis_client:
                tool_call_id = tool_msg.tool_call_id
                await tool_calls_hset(
                    redis_client=redis_client,
                    message_id=message_id,
                    tool_call_id=tool_call_id,
                    tool_output=tool_msg.content,
                )
            # yield f"工具结果：{tool_msg.content}"
    # 会话存表
    if redis_client:
        mes_key = await session_hset(
            redis_client=redis_client,
            message_id=message_id,
            user_id=user_id,
            answer=mes_list[-1].content,
            model_name=mes_list[-1].response_metadata.get("model_name"),
        )


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
            async for text in agent_astream(agent, question, thread_id, user_id="test01"):
                print(text, flush=True)
    asyncio.run(main())
