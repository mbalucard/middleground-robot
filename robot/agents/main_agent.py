"""
主智能体
"""

from deepagents import create_deep_agent
from deepagents.backends import StateBackend
from deepagents.middleware.summarization import create_summarization_tool_middleware
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage, HumanMessage


from robot.agents.models import deepseek_model
from robot.agents.model_middleware import get_model_middleware
from robot.agents.model_context import Context

from robot.tools.ordinary_tool import internet_search, get_current_date


# 初始化内存记忆
checkpointer = MemorySaver()

# 模型选择类型 manual 手动选择模型，auto 自动选择模型
model_type = "manual"
model_middleware = get_model_middleware(model_type)
# 初始化工具后端
tool_backend = StateBackend()
# 初始化中间件
middleware = [
    create_summarization_tool_middleware(deepseek_model, tool_backend)]
if model_middleware:
    middleware.append(model_middleware)


#! 系统提示词，临时用
sys_message = """
你的名字叫Dawn,你是一位乐于助人的AI助手。
你会使用工具来帮助用户解决问题。
"""
system_prompt = SystemMessage(content=sys_message)

agent = create_deep_agent(
    model=deepseek_model,
    checkpointer=checkpointer,  # 初始化内存记忆
    system_prompt=system_prompt,  # 初始化系统提示词
    tools=[internet_search, get_current_date],
    middleware=middleware,
    context_schema=Context,  # 初始化上下文模型
)



if __name__ == "__main__":
    from robot.agents.agent_invoke import run_agent
    from robot.tools.message_tool import parse_messages
    result = run_agent(agent, "现在几点了？")
    print(parse_messages(result.value["messages"]))