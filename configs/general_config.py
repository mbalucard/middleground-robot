"""
通用配置
    - 文件路径配置: FilePath
"""
import os


class FilePath:
    """配置文件路径"""
    SYSTEM_MESSAGE_PATH = "markdown/system_massage.md"
    ROOT_PATH = os.path.dirname(os.path.dirname(__file__))
