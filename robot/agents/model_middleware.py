"""
模型中间件
    - 手动选择模型: configurable_model
    - 自动选择模型: dynamic_model_selection
"""

from collections.abc import Awaitable, Callable
from typing import Literal

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse

from robot.agents.models import deepseek_model, minimax_model


class DynamicModelSelectionMiddleware(AgentMiddleware):
    """根据消息数量动态选择模型。"""

    def _select_model(self, request: ModelRequest):
        """根据消息数量动态选择模型"""
        message_count = len(request.state["messages"])
        return minimax_model if message_count > 10 else deepseek_model

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """包装模型调用"""
        return handler(request.override(model=self._select_model(request)))

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        """异步包装模型调用"""
        return await handler(request.override(model=self._select_model(request)))


class ConfigurableModelMiddleware(AgentMiddleware):
    """根据 context.model 手动选择模型。"""

    def _select_model(self, request: ModelRequest):
        """根据context.model手动选择模型"""
        model_name = request.runtime.context.model
        if model_name == "deepseek":
            return deepseek_model
        if model_name == "minimax":
            return minimax_model
        return deepseek_model

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """包装模型调用"""
        return handler(request.override(model=self._select_model(request)))

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        """异步包装模型调用"""
        return await handler(request.override(model=self._select_model(request)))


def get_model_middleware(
    model_type: Literal["manual", "auto"] = "manual"
):
    """
    获取模型中间件
    Args:
        model_type(str): 模型类型, default="manual"
            - manual: 手动选择模型
            - auto: 自动选择模型
    Returns:
        AgentMiddleware: 模型中间件实例
    """
    if model_type == "manual":
        return ConfigurableModelMiddleware()
    elif model_type == "auto":
        return DynamicModelSelectionMiddleware()
