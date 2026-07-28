"""
模型配置
    - MiniMax模型配置: MiniMaxModelConfig
    - DeepSeek模型配置: DeepSeekModelConfig
"""

import os
import dotenv

dotenv.load_dotenv()

def _read_env(name: str) -> str:
    """读取并清洗环境变量，缺失时抛出明确错误。"""
    value = os.getenv(name)
    if value is None:
        raise ValueError(f"缺少环境变量: {name}")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"环境变量为空: {name}")
    return cleaned


# 模型配置

class DeepSeekModelConfig:
    """DeepSeek模型配置"""
    BASE_URL = _read_env("DEEPSEEK_BASE_URL")
    API_KEY = _read_env("DEEPSEEK_API_KEY")
    MODEL_NAME = "deepseek-v4-flash"

class MiniMaxModelConfig:
    BASE_URL = _read_env("MINIMAX_ANTHROPIC_URL")
    API_KEY = _read_env("MINIMAX_KEY")
    MODEL_NAME = "anthropic:MiniMax-M2.7"

class Tavily:
    API_KEY = _read_env("TAVILY_API_KEY")

if __name__ == "__main__":
    print(DeepSeekModelConfig.BASE_URL)
    print(MiniMaxModelConfig.BASE_URL)
    