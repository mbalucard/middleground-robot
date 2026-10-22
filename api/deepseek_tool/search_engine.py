"""
搜索引擎
    - search: 搜索接口
"""


from httpx import AsyncClient
from typing import Optional
from configs.model_config import DeepSeekToolsConfig
from utils.logger_manager import LoggerManager


logger = LoggerManager.get_logger("search_engine")


class DeepSeekSearchEngine:
    def __init__(self):
        self.base_url = DeepSeekToolsConfig.BASE_URL
        self.headers = {
            "Authorization": DeepSeekToolsConfig.API_KEY,
            "Content-Type": "application/json",
            'Accept': 'application/json',
        }
        self.TTL = DeepSeekToolsConfig.TIMEOUT

    async def search(
        self,
        query: str,
        count: int = 3,
        need_content: bool = False,
        ori_question: Optional[str] = None,
        localization: str = ""
    ):
        """
        网页搜索接口
        Args:
            query: 搜索关键词,必填
                - 取值范围: 必须为 1-128 个 Unicode 字符
            count: 搜索结果数量
                - 取值范围：[1, 50]
            need_content: 是否返回网页正文 content
            ori_question: 用户的原始问题，帮引擎理解意图
                - 取值范围: 不超过 128个 Unicode 字符
            localization: 用于优先返回本地化结果的 IP 地址
        """
        url = f"{self.base_url}/search"
        payload = {
            "query": query,
            "count": count,
            "need_content": need_content,
            "ori_question": ori_question,
            "localization": localization,
        }
        async with AsyncClient() as client:
            response = await client.post(url, headers=self.headers, json=payload, timeout=self.TTL)
        return response.json()

    async def fetch(self, import_url: str):
        """
        抓取网页，返回页面标题与 Markdown 格式的内容
        Args:
            import_url: 网页 URL,必填
                - 取值范围: 长度不超过 8192
                - 必须为含 host 的 HTTP/HTTPS URL, 且不能携带用户名或密码。
        """
        url = f"{self.base_url}/fetch"
        payload = {
            "url": import_url,
        }
        async with AsyncClient() as client:
            response = await client.post(url, headers=self.headers, json=payload, timeout=self.TTL)
        return response.json()
