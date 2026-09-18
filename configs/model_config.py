"""
模型配置
    - MiniMax模型配置: MiniMaxModelConfig
    - AIHubMix_MiniMax_M27模型配置: AIHubMixModelConfig
    - DeepSeek模型配置: DeepSeekModelConfig
    - DashScope Embedding模型配置: DashScopeEmbeddingModelConfig
    - Tavily模型配置: Tavily
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
    BASE_URL_OPENAI = _read_env("DEEPSEEK_BASE_URL_OPENAI")
    BASE_URL_ANTHROPIC = _read_env("DEEPSEEK_BASE_URL_ANTHROPIC")
    API_KEY = _read_env("DEEPSEEK_API_KEY")
    MODEL_NAME = "deepseek-flash"


class MiniMaxModelConfig:
    BASE_URL_ANTHROPIC = _read_env("MINIMAX_ANTHROPIC_URL")
    API_KEY = _read_env("MINIMAX_KEY")
    MODEL_NAME_M27 = "MiniMax-M2.7"
    MODEL_NAME_M3 = "MiniMax-M3"


class AIHubMixModelConfig:
    BASE_URL = _read_env("AIHUBMIX_BASE_URL")
    API_KEY = _read_env("AIHUBMIX_API_KEY")
    MINIMAX_MODEL_M27 = "minimax-m2.7"
    MINIMAX_MODEL_M3 = "minimax-m3"



class DashScopeEmbeddingModelConfig:
    BASE_URL = f'https://{_read_env("DASHSCOPE_WORKSPACE_ID")}.cn-beijing.maas.aliyuncs.com/compatible-mode/v1'
    API_KEY = _read_env("DASHSCOPE_API_KEY")
    MODEL_NAME = "qwen3.7-text-embedding"
    DIMENSIONS = 1024  # 可选：2560、2048、1536、1024（默认）、768、512、256


class Tavily:
    API_KEY = _read_env("TAVILY_API_KEY")


if __name__ == "__main__":
    print(DeepSeekModelConfig.BASE_URL_OPENAI)
    print(DeepSeekModelConfig.BASE_URL_ANTHROPIC)
    print(MiniMaxModelConfig.BASE_URL_ANTHROPIC)
