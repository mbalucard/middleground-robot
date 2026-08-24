from langchain_mcp_adapters.client import MultiServerMCPClient
from configs.mcp_configs import mcp_server_configs


class QwMcp:
    def __init__(self):
        self.client = MultiServerMCPClient(mcp_server_configs)

    async def get_tools(self):
        return await self.client.get_tools()


if __name__ == "__main__":
    import asyncio
    qw_mcp = QwMcp()
    tools = asyncio.run(qw_mcp.get_tools())
    num = 0
    for tool in tools:
        print(f"{num}：{tool.name}")
        print(tool.description)
        # print(tool.args)
        num += 1
        print("="*60)
