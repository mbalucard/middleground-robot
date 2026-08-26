"""
模型中间件
    - 手动选择模型: configurable_model
    - 自动选择模型: dynamic_model_selection
    - get_model_middleware: 获取模型中间件
    - 非 vision 调用前剥掉历史图片块（A+2）
"""

from collections.abc import Awaitable, Callable
from typing import Any, Literal

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse

from robot.agents.message_content import strip_images_from_messages
from robot.agents.models import (
    deepseek_model,
    deepseek_model_vision,
    minimax_model,
    minimax_model_M3,
)


def _is_vision_model(model: Any) -> bool:
    """是否为支持图片输入的模型实例。"""
    return model is deepseek_model_vision or model is minimax_model_M3


def _prepare_request(request: ModelRequest, model: Any) -> ModelRequest:
    """选中模型后：非 vision 则剥图再 override。"""
    if _is_vision_model(model):
        return request.override(model=model)
    return request.override(
        model=model,
        messages=strip_images_from_messages(request.messages),
    )


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
        model = self._select_model(request)
        return handler(_prepare_request(request, model))

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        """异步包装模型调用"""
        model = self._select_model(request)
        return await handler(_prepare_request(request, model))


class ConfigurableModelMiddleware(AgentMiddleware):
    """根据 context.model 手动选择模型。"""

    def _select_model(self, request: ModelRequest):
        """根据context.model手动选择模型"""
        model_name = request.runtime.context.model
        if model_name == "deepseek":
            return deepseek_model
        if model_name == "minimax":
            return minimax_model
        if model_name == "minimax_m3":
            return minimax_model_M3
        if model_name == "deepseek_vision":
            return deepseek_model_vision
        return deepseek_model

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """包装模型调用"""
        model = self._select_model(request)
        return handler(_prepare_request(request, model))

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        """异步包装模型调用"""
        model = self._select_model(request)
        return await handler(_prepare_request(request, model))


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
