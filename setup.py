# 初始化项目
from setuptools import setup, find_packages

setup(
    name="middleground-robot",
    version="0.1.0",
    packages=find_packages(),
)

# 最终在终端执行以下代码
# uv pip install -e .
# source source .venv/bin/activate