"""
MCP技能集成模块（基于 langchain-mcp-adapters 正确用法重写）
"""
from typing import List, Dict, Any, Optional
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
import traceback
from src.utils import logger
from src.mcp_server.config_manager import get_mcp_config_manager, reload_mcp_config

# 默认MCP连接配置
DEFAULT_MCP_CONNECTIONS = {
    # 配置将从配置文件中读取，这里保持为空
}

class MCPClient:
    """MCP技能集成类（langchain-mcp-adapters 版，推荐用法）"""
    def __init__(self):
        # 从配置文件加载连接配置
        config_manager = get_mcp_config_manager()
        self.connections = config_manager.get_server_connections()
        print(self.connections)
        self.client = MultiServerMCPClient(self.connections)
        self._initialized = False

    def update_connections(self, connections: dict):
        """更新MCP连接配置"""
        self.connections = connections
        # 重新创建客户端
        self.client = MultiServerMCPClient(self.connections)
        self._initialized = False
        logger.info(f"MCP连接配置已更新: {list(connections.keys())}")
    
    def reload_from_config(self):
        """从配置文件重新加载连接配置"""
        config_manager = get_mcp_config_manager()
        self.connections = config_manager.get_server_connections()
        self.client = MultiServerMCPClient(self.connections)
        self._initialized = False
        logger.info(f"从配置文件重新加载MCP连接配置: {list(self.connections.keys())}")

    async def initialize(self):
        """初始化MCP客户端"""
        if not self._initialized:
            self._initialized = True
            logger.info("MCP集成初始化完成（MultiServerMCPClient）")

    async def get_mcp_tools(self, server_name: str = None) -> List[BaseTool]:
        """获取MCP工具"""
        if not self._initialized:
            await self.initialize()
        # 检查是否有可用的连接
        if not self.connections:
            logger.warning("没有配置MCP连接，无法获取工具")
            return []
        # 如果指定了服务器名称，检查该服务器是否存在
        if server_name and server_name not in self.connections:
            available_servers = list(self.connections.keys())
            logger.error(f"找不到名为 '{server_name}' 的MCP服务器，可用的服务器: {available_servers}")
            return []
        try:
            tools = await self.client.get_tools(server_name=server_name)
            return tools
        except Exception as e:
            logger.error(f"获取MCP工具失败: {e}")
            logger.error(traceback.format_exc())
            # 递归打印 ExceptionGroup 的所有子异常
            if hasattr(e, 'exceptions'):
                for idx, sub_exc in enumerate(e.exceptions):
                    logger.error(''.join(traceback.format_exception(type(sub_exc), sub_exc, sub_exc.__traceback__)))
            return []

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
        """刷新MCP技能列表"""
        # 从配置文件重新加载
        self.reload_from_config()
        logger.info("MCP技能列表已刷新（从配置文件重新加载）")

    async def shutdown(self):
        """关闭MCP集成"""
        self._initialized = False
        logger.info("MCP集成已关闭（MultiServerMCPClient）")

# 全局MCP集成实例
_mcp_integration = None

def get_mcp_client() -> MCPClient:
    global _mcp_integration
    if _mcp_integration is None:
        _mcp_integration = MCPClient()
    return _mcp_integration

async def initialize_mcp_integration():
    """初始化MCP集成"""
    integration = get_mcp_client()
    await integration.initialize()

async def get_mcp_tools_for_agent(mcp_skills: List[str] = None) -> List[BaseTool]:
    """为智能体获取MCP工具"""
    mcp_client = get_mcp_client()
    
    # 如果指定了特定的MCP技能，只返回这些技能的工具
    if mcp_skills:
        all_tools = []
        for skill_name in mcp_skills:
            tools = await mcp_client.get_mcp_tools(server_name=skill_name)
            if tools:
                all_tools.extend(tools)
                logger.info(f"成功加载MCP技能 '{skill_name}' 的 {len(tools)} 个工具，可用工具: {', '.join([getattr(tool, 'name', str(tool)) for tool in tools])}")
            else:
                logger.warning(f"无法加载MCP技能 '{skill_name}' 的工具")
        return all_tools
    
    # 否则返回所有可用的MCP工具
    return await mcp_client.get_mcp_tools()

def load_mcp_connections_from_config(mcp_config: dict) -> dict:
    """从配置文件加载MCP连接配置（兼容旧版本）"""
    # 现在使用新的配置管理器
    config_manager = get_mcp_config_manager()
    return config_manager.get_server_connections()
