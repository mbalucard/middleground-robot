"""
Agent模型
    - DeepSeekAgent
    - MiniMaxAgent
"""

from langchain.chat_models import init_chat_model

from configs.model_config import DeepSeekModelConfig,MiniMaxModelConfig


deepseek_model = init_chat_model(
    model=DeepSeekModelConfig.MODEL_NAME,
    api_key=DeepSeekModelConfig.API_KEY,
    base_url=DeepSeekModelConfig.BASE_URL,
    temperature=0,  # 温度，0为最确定，1为最不确定
    # disabled enabled
    extra_body={"thinking":{"type": "disabled"}},  # 思考类型，disabled为不思考，enabled为思考
    model_provider="openai",  # 模型提供者，openai为openai，anthropic为anthropic
)

minimax_model = init_chat_model(
    model=MiniMaxModelConfig.MODEL_NAME,
    api_key=MiniMaxModelConfig.API_KEY,
    base_url=MiniMaxModelConfig.BASE_URL,
)


if __name__ == "__main__":
    print(deepseek_model.model_name)
    print(minimax_model.model_dump)