"""
模型中间件
    - 手动选择模型: configurable_model
    - 自动选择模型: dynamic_model_selection
    - get_model_middleware: 获取模型中间件
    - 非 vision 调用前剥掉历史图片块（A+2）
"""

from collections.abc import Awaitable, Callable, Sequence
from typing import Any, Literal

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain_core.messages import BaseMessage

from robot.agents.models import (
    deepseek_model,
    deepseek_model_vision,
    minimax_model,
    minimax_model_M3,
)

_IMAGE_STRIP_HINT = "（用户曾附带图片；具体内容见后续助手对该图的描述）"


def _is_vision_model(model: Any) -> bool:
    """是否为支持图片输入的模型实例。"""
    return model is deepseek_model_vision or model is minimax_model_M3


def _is_image_content_block(block: Any) -> bool:
    """识别 OpenAI / Anthropic 风格的图片 content 块。"""
    if not isinstance(block, dict):
        return False
    block_type = block.get("type")
    if block_type in ("image", "image_url"):
        return True
    # OpenAI file 块携带 inline 图或 file_id 时一并剥掉，避免非 vision 400
    if block_type == "file" and (
        block.get("file_id") or block.get("file_data")
    ):
        return True
    return False


def _strip_images_from_content(content: Any) -> Any:
    """
    从单条消息 content 中去掉图片块。
    若曾含图：保留 text，并追加提示句；无文字则仅保留提示句。
    str content 原样返回。
    """
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return content

    had_image = False
    kept: list[Any] = []
    for block in content:
        if _is_image_content_block(block):
            had_image = True
            continue
        kept.append(block)

    if not had_image:
        return content

    texts = [
        b.get("text", "")
        for b in kept
        if isinstance(b, dict) and b.get("type") == "text" and b.get("text")
    ]
    # 非 text 的保留块（如 thinking）一并留下，再追加提示
    non_text = [
        b
        for b in kept
        if not (isinstance(b, dict) and b.get("type") == "text")
    ]
    hint_block = {"type": "text", "text": _IMAGE_STRIP_HINT}
    text_blocks = [{"type": "text", "text": t} for t in texts]
    text_blocks.append(hint_block)
    result = text_blocks + non_text
    if len(result) == 1 and result[0].get("type") == "text":
        return result[0]["text"]
    return result


def _strip_images_from_messages(
    messages: Sequence[BaseMessage],
) -> list[BaseMessage]:
    """复制消息列表并替换 content；不修改原对象 / checkpoint。"""
    out: list[BaseMessage] = []
    for msg in messages:
        new_content = _strip_images_from_content(msg.content)
        if new_content is msg.content:
            out.append(msg)
        else:
            out.append(msg.model_copy(update={"content": new_content}))
    return out


def _prepare_request(request: ModelRequest, model: Any) -> ModelRequest:
    """选中模型后：非 vision 则剥图再 override。"""
    if _is_vision_model(model):
        return request.override(model=model)
    return request.override(
        model=model,
        messages=_strip_images_from_messages(request.messages),
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
