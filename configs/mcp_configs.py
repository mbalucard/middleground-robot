"""
MCP 工具配置
"""
import os
import dotenv

dotenv.load_dotenv()

mcp_server_configs = {
    "企业微信通讯录": {
        "transport": "streamable_http",
        "url": os.getenv("QYWX_MCP_TOOL_USER_URL")
    }
}
