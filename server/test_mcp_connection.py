import asyncio
import sys
import os

# 将 server 目录添加到 sys.path
# 这确保了无论从哪里运行脚本，都能正确找到 src 模块
# 特别是对于 mcp 子进程的启动
current_dir = os.path.dirname(__file__)
server_dir = os.path.abspath(current_dir)
if server_dir not in sys.path:
    sys.path.insert(0, server_dir)

# 现在可以安全地导入 src 下的模块了
from src.agents.mcp_client import MCPClient

async def test_mcp_connection():
    mcp_client = MCPClient.get_instance()
    tools = await mcp_client.get_mcp_tools()
    print(f"获取到的MCP工具数量: {len(tools)}")
    for tool in tools:
        print(f"工具名: {getattr(tool, 'name', str(tool))}, 描述: {getattr(tool, 'description', '')}")

if __name__ == "__main__":
    asyncio.run(test_mcp_connection())