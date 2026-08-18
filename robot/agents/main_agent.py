"""
主智能体
    - build_agent: 构建代理
"""

from deepagents import create_deep_agent
from deepagents.backends import StateBackend
from deepagents.middleware.summarization import create_summarization_tool_middleware
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres import AsyncPostgresStore

from robot.agents.agent_backend import make_backend
from robot.agents.models import deepseek_model
from robot.agents.model_middleware import get_model_middleware
from robot.agents.model_context import Context

from robot.tools.ordinary_tool import internet_search, get_current_date
from robot.tools.sale_tools import get_shop_sale_data, list_shops_with_sales
from robot.tools.shop_info_tools import get_shop_info


def build_agent(*, checkpointer: AsyncPostgresSaver, store: AsyncPostgresStore):
    """
    构建代理
    """
    backend = make_backend()
    skills = ["skills"]
    memory = ["AGENTS.md"]

    model_type = "manual"
    model_middleware = get_model_middleware(model_type)
    tool_backend = StateBackend()
    middleware = [
        create_summarization_tool_middleware(
            deepseek_model, tool_backend)  # 工具摘要中间件
    ]
    if model_middleware:
        middleware.append(model_middleware)

    tools = [internet_search, get_current_date,
             get_shop_sale_data, get_shop_info, list_shops_with_sales]

    sys_message = """
                    你的名字叫Dawn,你是一位乐于助人的AI助手。
                    你会使用工具来帮助用户解决问题。
                    你有跨会话长期记忆目录 /memories/。
                    用户告诉你名字、偏好、长期事实时，写入 /memories/user_profile.md。
                    新对话开始时先读取该文件,并使用工具获取当前日期。
                """
    system_prompt = SystemMessage(content=sys_message)

    agent = create_deep_agent(
        model=deepseek_model,
        backend=backend,
        skills=skills,
        memory=memory,
        checkpointer=checkpointer,
        store=store,
        system_prompt=system_prompt,
        tools=tools,
        middleware=middleware,
        context_schema=Context,
    )
    return agent


if __name__ == "__main__":
    from robot.agents.agent_invoke import run_agent
    from robot.tools.message_tool import parse_messages
    from robot.tools.memory_device import postgres_resources
    import asyncio

    async def main():
        async with postgres_resources() as pg:
            agent = build_agent(checkpointer=pg.checkpointer, store=pg.store)
            result = run_agent(agent, "现在几点了？")
            print(parse_messages(result.value["messages"]))
    asyncio.run(main())
