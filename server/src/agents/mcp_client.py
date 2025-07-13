"""
MCP技能集成模块（基于 langchain-mcp-adapters 正确用法重写）
"""
from typing import List, Dict, Any, Optional
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from server.src.utils import logger

# 你可以在这里配置 MCP 服务器连接参数
MCP_CONNECTIONS = {
    # 示例：
    # "math": {
    #     "command": "python",
    #     "args": ["/path/to/math_server.py"],
    #     "transport": "stdio",
    # },
    # "weather": {
    #     "url": "http://localhost:8000/mcp",
    #     "transport": "streamable_http",
    # },
}

class MCPClient:
    """MCP技能集成类（langchain-mcp-adapters 版，推荐用法）"""
    def __init__(self, connections: Optional[dict] = None):
        self.connections = connections or MCP_CONNECTIONS
        self.client = MultiServerMCPClient(self.connections)
        self._initialized = False

    async def initialize(self):
        self._initialized = True
        logger.info("MCP集成初始化完成（MultiServerMCPClient）")

    async def get_mcp_tools(self, server_name: str = None) -> List[BaseTool]:
        if not self._initialized:
            await self.initialize()
        tools = await self.client.get_tools(server_name=server_name)
        logger.debug(f"获取MCP工具: {len(tools)} 个工具")
        return tools

    async def get_available_mcp_tools(self) -> Dict[str, Any]:
        """获取所有可用的MCP工具信息（按服务器分组）"""
        if not self._initialized:
            await self.initialize()
        all_tools = await self.client.get_tools()
        grouped = {}
        for tool in all_tools:
            server = getattr(tool, "server_name", "default")
            grouped.setdefault(server, []).append({
                "name": tool.name,
                "description": getattr(tool, "description", ""),
                "args_schema": getattr(tool, "args_schema", None),
            })
        return grouped

    async def refresh_skills(self):
        # 目前 MultiServerMCPClient 没有刷新方法，重建 client 即可
        self.client = MultiServerMCPClient(self.connections)
        logger.info("MCP技能列表已刷新（MultiServerMCPClient）")

    async def shutdown(self):
        self._initialized = False
        logger.info("MCP集成已关闭（MultiServerMCPClient）")

# 全局MCP集成实例
_mcp_integration = None

def get_mcp_integration() -> MCPClient:
    global _mcp_integration
    if _mcp_integration is None:
        _mcp_integration = MCPClient()
    return _mcp_integration

async def initialize_mcp_integration():
    integration = get_mcp_integration()
    await integration.initialize()

async def get_mcp_tools_for_agent(server_name: str = None) -> List[BaseTool]:
    integration = get_mcp_integration()
    return await integration.get_mcp_tools(server_name=server_name)
