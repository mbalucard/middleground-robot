"""
Agent模型
    - deepseek_model
    - minimax_model
"""

from langchain.chat_models import init_chat_model

from configs.model_config import DeepSeekModelConfig,MiniMaxModelConfig


deepseek_model = init_chat_model(
    model=DeepSeekModelConfig.MODEL_NAME,
    api_key=DeepSeekModelConfig.API_KEY,
    base_url=DeepSeekModelConfig.BASE_URL_OPENAI,
    temperature=0,  # 温度，0为最确定，1为最不确定
    # disabled enabled
    extra_body={"thinking":{"type": "enabled"}},  # 思考类型，disabled 为不思考， enabled 为思考
    model_provider="openai",  # 模型提供者，openai为openai，anthropic为anthropic
    reasoning_effort="high",  # 推理力度，low为低，high为中，max为高
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

if __name__ == "__main__":  
    print(deepseek_model.model_dump())
    print(minimax_model.model_dump())
    print(minimax_model_M3.model_dump())