
from typing import List, Dict, Any
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
import traceback
import importlib
import platform
from src.utils import logger
from config.mcp_server_config import MCPConfigManager


class InProcessMCPTool(BaseTool):
    """In-process MCP tool wrapper"""
    
    def __init__(self, name: str, description: str, func, **kwargs):
        super().__init__(name=name, description=description, **kwargs)
        # 使用私有属性存储函数，避免Pydantic字段验证
        object.__setattr__(self, '_func', func)
    
    def _run(self, **kwargs) -> Any:
        return self._func(**kwargs)
    
    async def _arun(self, **kwargs) -> Any:
        return self._func(**kwargs)


class MCPClient:
    """MCP技能集成类（单例模式，支持Windows和subprocess版本）"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MCPClient, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        # 避免重复初始化
        if hasattr(self, '_init_completed'):
            return
            
        # 从配置文件加载连接配置
        config_manager = MCPConfigManager.get_instance()
        self.connections = config_manager.get_server_connections()
        logger.info(f"初始化MCP客户端，可用连接: {list(self.connections.keys())}")
        
        # 检测操作系统，在Windows上使用in-process模式
        self.use_in_process = platform.system() == "Windows"
        
        if self.use_in_process:
            logger.info("检测到Windows系统，使用in-process MCP工具模式")
            self.client = None
            self._in_process_tools = {}
        else:
            logger.info("使用subprocess MCP工具模式")
            self.client = MultiServerMCPClient(self.connections)
        
        self._initialized = False
        self._init_completed = True
    
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def update_connections(self, connections: dict):
        """更新MCP连接配置"""
        self.connections = connections
        # 重新创建客户端
        if not self.use_in_process:
            self.client = MultiServerMCPClient(self.connections)
        self._initialized = False
        logger.info(f"MCP连接配置已更新: {list(connections.keys())}")
    
    def reload_from_config(self):
        """从配置文件重新加载连接配置"""
        config_manager = MCPConfigManager.get_instance()
        self.connections = config_manager.get_server_connections()
        if not self.use_in_process:
            self.client = MultiServerMCPClient(self.connections)
        self._initialized = False
        logger.info(f"从配置文件重新加载MCP连接配置: {list(self.connections.keys())}")

    def load_connections_from_config(self, mcp_config: dict) -> dict:
        """从配置文件加载MCP连接配置，只返回请求的服务器连接"""
        # 使用新的配置管理器
        config_manager = MCPConfigManager.get_instance()
        all_connections = config_manager.get_server_connections()
        
        # 如果mcp_config为空或不是字典，返回所有连接
        if not mcp_config or not isinstance(mcp_config, dict):
            return all_connections
        
        # 只返回mcp_config中指定的服务器连接
        requested_servers = list(mcp_config.keys())
        filtered_connections = {}
        
        for server_name in requested_servers:
            if server_name in all_connections:
                filtered_connections[server_name] = all_connections[server_name]
            else:
                logger.warning(f"请求的MCP服务器 '{server_name}' 在配置中不存在或未启用")
        
        logger.info(f"根据请求过滤MCP连接: 请求 {requested_servers}, 返回 {list(filtered_connections.keys())}")
        return filtered_connections

    def _load_in_process_tools(self):
        """加载in-process工具"""
        if not self.use_in_process:
            return
        
        config_manager = MCPConfigManager.get_instance()
        
        # 只加载当前连接中指定的服务器，而不是所有启用的服务器
        for server_name in self.connections.keys():
            try:
                server_config = config_manager.get_server_config(server_name)
                if not server_config:
                    logger.warning(f"MCP服务器 '{server_name}' 在配置中不存在")
                    continue
                    
                module_path = server_config.get("module_path")
                
                logger.info(f"加载in-process MCP工具: {server_name} ({module_path})")
                
                # 动态导入模块
                module = importlib.import_module(module_path)
                
                # 获取FastMCP实例
                if hasattr(module, 'mcp'):
                    fastmcp_instance = module.mcp
                    
                    # 从FastMCP实例获取工具
                    tools = []
                    if hasattr(fastmcp_instance, '_tool_manager'):
                        tool_manager = fastmcp_instance._tool_manager
                        # 使用list_tools()方法获取工具列表
                        fastmcp_tools = tool_manager.list_tools()
                        
                        for tool in fastmcp_tools:
                            # 创建LangChain工具
                            langchain_tool = InProcessMCPTool(
                                name=tool.name,
                                description=tool.description,
                                func=tool.fn
                            )
                            tools.append(langchain_tool)
                    
                    self._in_process_tools[server_name] = tools
                    logger.info(f"成功加载 {server_name} 的 {len(tools)} 个工具: {[t.name for t in tools]}")
                
            except Exception as e:
                logger.error(f"加载in-process工具 '{server_name}' 失败: {e}")
                logger.error(traceback.format_exc())

    async def initialize(self):
        """初始化MCP客户端"""
        if not self._initialized:
            try:
                if self.use_in_process:
                    # Windows: 使用in-process模式
                    self._load_in_process_tools()
                else:
                    # 非Windows: 使用subprocess模式
                    for server_name, connection in self.connections.items():
                        try:
                            # 尝试初始化服务器连接
                            tools = await self.get_mcp_tools(server_name)
                        except Exception as e:
                            logger.error(f"初始化MCP服务器 '{server_name}' 失败: {e}")
                            logger.error(traceback.format_exc())

                self._initialized = True
                mode = "in-process" if self.use_in_process else "subprocess"
                logger.info(f"MCP集成初始化完成（{mode}模式）")
            except Exception as e:
                logger.error(f"MCP客户端初始化失败: {e}")
                logger.error(traceback.format_exc())
                raise

    async def get_mcp_tools(self, server_name: str = None) -> List[BaseTool]:
        """获取MCP工具"""
        if not self._initialized:
            await self.initialize()
        
        # 检查是否有可用的连接
        if not self.connections:
            logger.warning("没有配置MCP连接，无法获取工具")
            return []
        
        if self.use_in_process:
            # Windows: 返回in-process工具
            if server_name:
                if server_name not in self._in_process_tools:
                    available_servers = list(self._in_process_tools.keys())
                    logger.error(f"找不到名为 '{server_name}' 的MCP服务器，可用的服务器: {available_servers}")
                    return []
                return self._in_process_tools[server_name]
            else:
                # 返回所有工具
                all_tools = []
                for tools in self._in_process_tools.values():
                    all_tools.extend(tools)
                return all_tools
        else:
            # 非Windows: 使用subprocess模式
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
                return []

    async def get_mcp_tools_for_agent(self, mcp_skills: List[str] = None) -> List[BaseTool]:
        """为智能体获取MCP工具"""
        # 如果指定了特定的MCP技能，只返回这些技能的工具
        if mcp_skills:
            all_tools = []
            for skill_name in mcp_skills:
                try:
                    tools = await self.get_mcp_tools(server_name=skill_name)
                    if tools:
                        all_tools.extend(tools)
                        logger.info(f"成功加载MCP技能 '{skill_name}' 的 {len(tools)} 个工具，可用工具: {', '.join([getattr(tool, 'name', str(tool)) for tool in tools])}")
                    else:
                        logger.warning(f"无法加载MCP技能 '{skill_name}' 的工具")
                except Exception as e:
                    logger.error(f"加载MCP技能 '{skill_name}' 时出错: {e}")
                    logger.error(traceback.format_exc())
            return all_tools
        
        # 否则返回所有可用的MCP工具
        return await self.get_mcp_tools()

    async def get_available_mcp_tools(self) -> Dict[str, Any]:
        """获取所有可用的MCP工具信息（按服务器分组）"""
        if not self._initialized:
            await self.initialize()
        
        if self.use_in_process:
            # Windows: 返回in-process工具信息
            grouped = {}
            for server_name, tools in self._in_process_tools.items():
                grouped[server_name] = []
                for tool in tools:
                    grouped[server_name].append({
                        "name": tool.name,
                        "description": tool.description,
                        "args_schema": getattr(tool, "args_schema", None),
                    })
            return grouped
        else:
            # 非Windows: 使用subprocess模式
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
        if self.use_in_process:
            self._in_process_tools.clear()
            self._load_in_process_tools()
        logger.info("MCP技能列表已刷新（从配置文件重新加载）")

    async def shutdown(self):
        """关闭MCP集成"""
        self._initialized = False
        if self.use_in_process:
            self._in_process_tools.clear()
        logger.info("MCP集成已关闭")
