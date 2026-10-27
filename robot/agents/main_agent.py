"""
主智能体
    - build_agent: 构建代理
"""

from pathlib import Path

from deepagents import create_deep_agent, FilesystemPermission
from deepagents.backends import StateBackend
from deepagents.middleware.summarization import create_summarization_tool_middleware

from langchain_core.messages import SystemMessage, HumanMessage
from langchain.agents.middleware import ModelFallbackMiddleware

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres import AsyncPostgresStore

from configs.general_config import FilePath
from robot.agents.agent_backend import make_backend
from robot.agents.models import deepseek_model, minimax_model_M3
from robot.agents.model_middleware import get_model_middleware
from robot.agents.model_context import Context

from robot.agent_tools.ordinary_tool import internet_search, get_current_date, fetch_internet_content
from robot.agent_tools.erp_tools import (
    get_inventory_data,
    get_warehouse_info,
    get_goods_info,
    get_shop_available_info,
    get_shop_retail_info,
    get_region_tree_info,
    get_store_goods_retail_info,
    get_inventory_audit_summary_data,
)
from robot.agent_tools.mcp_server_tools import QwMcp

_SYS_MESSAGE_PATH = Path(FilePath.ROOT_PATH) / \
    "robot" / "workspace" / "sys_message.md"


async def build_agent(*, checkpointer: AsyncPostgresSaver, store: AsyncPostgresStore):
    """
    构建代理
    Args:
        checkpointer: 检查点
        store: 存储
    Returns:
        agent: 代理
    """

    backend = make_backend()
    skills = ["skills"]
    memory = ["AGENTS.md", "me/SOUL.md", "me/IDENTITY.md", "me/MEMORY.md"]
    # 文件权限管控
    permissions = [
        FilesystemPermission(
            operations=["write"],
            paths=["/skills/**", "/sys_message.md", "/AGENTS.md"],
            mode="deny"
        )
    ]
    # 中间件列表
    model_type = "manual"  # 模型中间件参数
    model_middleware = get_model_middleware(model_type)
    tool_backend = StateBackend()  # 工具摘要中间件参数
    middleware = [
        create_summarization_tool_middleware(
            deepseek_model, tool_backend),  # 工具摘要中间件
        ModelFallbackMiddleware(minimax_model_M3),  # 模型降级中间件
    ]
    if model_middleware:
        middleware.append(model_middleware)
    # MCP工具
    qw_mcp = QwMcp()
    mcp_tools = await qw_mcp.get_tools()
    erp_tools = [
        get_inventory_data,
        get_warehouse_info,
        get_goods_info,
        get_shop_available_info,
        get_shop_retail_info,
        get_region_tree_info,
        get_store_goods_retail_info,
        get_inventory_audit_summary_data,
    ]
    tools = [internet_search, get_current_date, fetch_internet_content, *mcp_tools, *erp_tools]

    sys_message = _SYS_MESSAGE_PATH.read_text(encoding="utf-8")
    system_prompt = SystemMessage(content=sys_message)

    agent = create_deep_agent(
        model=deepseek_model,
        backend=backend,
        permissions=permissions,
        skills=skills,
        memory=memory,
        checkpointer=checkpointer,
        store=store,
        system_prompt=system_prompt,
        tools=tools,
        middleware=middleware,
        context_schema=Context,
        interrupt_on={"internet_search": True, "fetch_internet_content": True}
    )
    return agent


if __name__ == "__main__":
    from robot.agents.agent_invoke import run_agent
    from robot.tools.message_tool import parse_messages
    from robot.tools.memory_device import postgres_resources
    import asyncio

    async def main():
        async with postgres_resources() as pg:
            agent = await build_agent(checkpointer=pg.checkpointer, store=pg.store)
            result = await run_agent(agent, "现在几点了？")
            print(parse_messages(result.value["messages"]))
    asyncio.run(main())
