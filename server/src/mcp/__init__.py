"""
MCP (Model Context Protocol) 集成模块

这个模块提供了与MCP服务器集成的功能，允许智能体使用MCP技能。

MCP是一个标准协议，用于AI应用与外部工具和数据源的集成。
更多信息请参考: https://modelcontextprotocol.io/

主要组件:
- MCPClient: MCP客户端，用于连接MCP服务器
- MCPSkillRegistry: MCP技能注册表，管理可用的MCP技能
- MCPToolAdapter: MCP工具适配器，将MCP技能转换为LangChain工具
"""

from .client import MCPClient
from .registry import MCPSkillRegistry
from .adapter import MCPToolAdapter

__all__ = [
    "MCPClient",
    "MCPSkillRegistry", 
    "MCPToolAdapter"
]

# 全局MCP技能注册表实例
mcp_registry = MCPSkillRegistry()

def get_mcp_registry():
    """获取全局MCP技能注册表"""
    return mcp_registry 