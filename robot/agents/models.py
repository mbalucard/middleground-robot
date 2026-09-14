"""
Agent模型
    - deepseek_model
    - deepseek_model_vision
    - minimax_model
    - minimax_model_M3
"""

from langchain.chat_models import init_chat_model
from langchain_openai import OpenAIEmbeddings

from configs.model_config import DeepSeekModelConfig, MiniMaxModelConfig, DashScopeEmbeddingModelConfig


deepseek_model = init_chat_model(
    model=DeepSeekModelConfig.MODEL_NAME,
    api_key=DeepSeekModelConfig.API_KEY,
    base_url=DeepSeekModelConfig.BASE_URL_OPENAI,
    temperature=0.01,  # 温度，0为最确定，1为最不确定
    # disabled enabled
    # 思考类型，disabled 为不思考， enabled 为思考
    extra_body={"thinking": {"type": "enabled"}},
    model_provider="openai",  # 模型提供者，openai为openai，anthropic为anthropic
    reasoning_effort="high",  # 推理力度，low为低，high为中，max为高
)

deepseek_model_vision = init_chat_model(
    model=DeepSeekModelConfig.MODEL_NAME_VISION,
    api_key=DeepSeekModelConfig.API_KEY,
    base_url=DeepSeekModelConfig.BASE_URL_OPENAI,
    model_provider="openai",
    extra_body={"thinking": {"type": "enabled"}},
    reasoning_effort="low",
)


minimax_model = init_chat_model(
    model=MiniMaxModelConfig.MODEL_NAME,
    api_key=MiniMaxModelConfig.API_KEY,
    base_url=MiniMaxModelConfig.BASE_URL_ANTHROPIC,
)

minimax_model_M3 = init_chat_model(
    model=MiniMaxModelConfig.MODEL_NAME_M3,
    api_key=MiniMaxModelConfig.API_KEY,
    base_url=MiniMaxModelConfig.BASE_URL_ANTHROPIC,
    # max_tokens=10000,
)

qwen_embedding_model = OpenAIEmbeddings(
    model=DashScopeEmbeddingModelConfig.MODEL_NAME,
    api_key=DashScopeEmbeddingModelConfig.API_KEY,
    base_url=DashScopeEmbeddingModelConfig.BASE_URL,
    dimensions=DashScopeEmbeddingModelConfig.DIMENSIONS,
    check_embedding_ctx_length=False,
)


if __name__ == "__main__":
    print(deepseek_model.model_dump())
    print(minimax_model.model_dump())
    print(minimax_model_M3.model_dump())
    print(deepseek_model_vision.model_dump())
