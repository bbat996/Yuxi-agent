"""
MCP配置管理器
用于读取和管理MCP服务器配置
"""

import os
import yaml
from typing import Dict, List, Any, Optional
from pathlib import Path
from src.utils.logging_config import logger


class MCPConfigManager:
    """MCP配置管理器"""
    
    def __init__(self, config_path: str = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，默认为config/mcp_server.yaml
        """
        if config_path is None:
            # 获取项目根目录
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "mcp_server.yaml"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # 确保config不为None
        if self.config is None:
            logger.warning("配置加载失败，使用默认配置")
            self.config = self._get_default_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if not self.config_path.exists():
                logger.warning(f"MCP配置文件不存在: {self.config_path}")
                return self._get_default_config()
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 检查YAML解析结果是否为None（空文件或只有注释的情况）
            if config is None:
                logger.warning(f"MCP配置文件为空或只包含注释: {self.config_path}")
                return self._get_default_config()
            
            logger.info(f"成功加载MCP配置文件: {self.config_path}")
            return config
            
        except Exception as e:
            logger.error(f"加载MCP配置文件失败: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "global": {
                "timeout": 30,
                "max_connections": 10,
                "log_level": "INFO",
                "rate_limit": {
                    "per_minute": 100,
                    "per_hour": 1000,
                    "concurrent": 5
                }
            },
            "servers": {
                "math_tools": {
                    "enabled": True,
                    "module_path": "src.mcp_server.math_tools",
                    "class_name": "mcp",
                    "tools": [
                        {
                            "name": "add",
                            "description": "计算两个数的和",
                            "parameters": {
                                "a": {"type": "number", "description": "第一个数"},
                                "b": {"type": "number", "description": "第二个数"}
                            }
                        }
                    ]
                }
            }
        }
    
    def get_global_config(self) -> Dict[str, Any]:
        """获取全局配置"""
        if self.config is None:
            return {}
        result = self.config.get("global", {})
        return result if result is not None else {}
    
    def get_servers(self) -> Dict[str, Any]:
        """获取服务器配置"""
        if self.config is None:
            return {}
        servers = self.config.get("servers", {})
        return servers if isinstance(servers, dict) else {}
    
    def get_enabled_servers(self) -> List[str]:
        """获取已启用的服务器列表"""
        servers = self.get_servers()
        enabled_servers = []
        
        for server_name, server_config in servers.items():
            if isinstance(server_config, dict) and server_config.get("enabled", False):
                enabled_servers.append(server_name)
        
        return enabled_servers
    
    def get_server_config(self, server_name: str) -> Optional[Dict[str, Any]]:
        """获取指定服务器的配置"""
        servers = self.get_servers()
        return servers.get(server_name)
    
    def get_server_connections(self) -> Dict[str, Any]:
        """获取服务器连接配置（用于langchain-mcp-adapters）"""
        connections = {}
        
        try:
            servers = self.get_servers()
            for server_name, server_config in servers.items():
                if isinstance(server_config, dict) and server_config.get("enabled", False):
                    # 内置服务器使用stdio传输
                    connections[server_name] = {
                        "transport": "stdio",
                        "command": "python",
                        "args": ["-m", server_config.get("module_path", "src.mcp_server.math_tools")],
                        "env": {
                            "PYTHONPATH": os.environ.get("PYTHONPATH", "")
                        }
                    }
        except Exception as e:
            logger.error(f"获取服务器连接配置时出错: {e}")
        
        return connections
    
    def get_all_tools(self) -> List[str]:
        """获取所有工具名称列表"""
        tools = []
        servers = self.get_servers()
        
        for server_name, server_config in servers.items():
            if isinstance(server_config, dict) and server_config.get("enabled", False):
                server_tools = server_config.get("tools", [])
                for tool in server_tools:
                    if isinstance(tool, dict) and "name" in tool:
                        tools.append(tool["name"])
        
        return tools
    
    def get_enabled_tools(self, server_name: str = None) -> List[str]:
        """获取已启用的工具列表"""
        tools = []
        servers = self.get_servers()
        
        for s_name, server_config in servers.items():
            if server_name and s_name != server_name:
                continue
                
            if isinstance(server_config, dict) and server_config.get("enabled", False):
                server_tools = server_config.get("tools", [])
                for tool in server_tools:
                    if isinstance(tool, dict) and "name" in tool:
                        tools.append(tool["name"])
        
        return tools
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取指定工具的详细信息"""
        servers = self.get_servers()
        
        for server_name, server_config in servers.items():
            if isinstance(server_config, dict) and server_config.get("enabled", False):
                server_tools = server_config.get("tools", [])
                for tool in server_tools:
                    if isinstance(tool, dict) and tool.get("name") == tool_name:
                        return {
                            "name": tool["name"],
                            "description": tool.get("description", ""),
                            "server": server_name,
                            "parameters": tool.get("parameters", {}),
                            "enabled": True
                        }
        
        return None
    
    def search_tools(self, keyword: str) -> List[str]:
        """搜索工具"""
        matching_tools = []
        servers = self.get_servers()
        
        for server_name, server_config in servers.items():
            if isinstance(server_config, dict) and server_config.get("enabled", False):
                server_tools = server_config.get("tools", [])
                for tool in server_tools:
                    if isinstance(tool, dict) and "name" in tool:
                        tool_name = tool["name"]
                        description = tool.get("description", "")
                        
                        # 搜索工具名称和描述
                        if (keyword.lower() in tool_name.lower() or 
                            keyword.lower() in description.lower()):
                            matching_tools.append(tool_name)
        
        return matching_tools
    
    def get_tools_by_server(self, server_name: str) -> List[Dict[str, Any]]:
        """获取指定服务器的工具列表"""
        server_config = self.get_server_config(server_name)
        if not server_config or not server_config.get("enabled", False):
            return []
        
        tools = server_config.get("tools", [])
        return [tool for tool in tools if isinstance(tool, dict)]
    
    def get_server_tools_by_category(self, server_name: str) -> Dict[str, List[Dict[str, Any]]]:
        """获取服务器的工具分类（兼容旧接口）"""
        tools = self.get_tools_by_server(server_name)
        return {
            "all": tools
        }
    
    def get_tool_categories(self) -> Dict[str, Any]:
        """获取工具分类配置（兼容旧接口）"""
        # 根据服务器名称生成分类
        categories = {}
        servers = self.get_servers()
        
        for server_name, server_config in servers.items():
            if isinstance(server_config, dict) and server_config.get("enabled", False):
                tools = server_config.get("tools", [])
                tool_names = [tool["name"] for tool in tools if isinstance(tool, dict) and "name" in tool]
                
                categories[server_name] = {
                    "description": f"{server_name} 工具集",
                    "tools": tool_names,
                    "servers": [server_name]
                }
        
        return categories
    
    def get_tools_by_category(self, category_name: str) -> List[str]:
        """根据分类获取工具列表（兼容旧接口）"""
        categories = self.get_tool_categories()
        if category_name in categories:
            return categories[category_name].get("tools", [])
        return []
    
    def get_tool_by_id(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """根据ID获取工具信息（兼容旧接口）"""
        return self.get_tool_info(tool_name)
    
    def get_enabled_tools_for_server(self, server_name: str) -> List[str]:
        """获取指定服务器的已启用工具列表"""
        return self.get_enabled_tools(server_name)
    
    def is_server_enabled(self, server_name: str) -> bool:
        """检查服务器是否启用"""
        server_config = self.get_server_config(server_name)
        return server_config is not None and server_config.get("enabled", False)
    
    def validate_config(self) -> List[str]:
        """验证配置"""
        errors = []
        
        try:
            servers = self.get_servers()
            
            for server_name, server_config in servers.items():
                if not isinstance(server_config, dict):
                    errors.append(f"服务器 '{server_name}' 配置格式错误")
                    continue
                
                # 检查必需字段
                if "module_path" not in server_config:
                    errors.append(f"服务器 '{server_name}' 缺少 module_path 配置")
                
                if "class_name" not in server_config:
                    errors.append(f"服务器 '{server_name}' 缺少 class_name 配置")
                
                # 检查工具配置
                tools = server_config.get("tools", [])
                if not isinstance(tools, list):
                    errors.append(f"服务器 '{server_name}' 的 tools 配置格式错误")
                else:
                    for i, tool in enumerate(tools):
                        if not isinstance(tool, dict):
                            errors.append(f"服务器 '{server_name}' 的第 {i+1} 个工具配置格式错误")
                        elif "name" not in tool:
                            errors.append(f"服务器 '{server_name}' 的第 {i+1} 个工具缺少 name 字段")
                        elif "description" not in tool:
                            errors.append(f"服务器 '{server_name}' 的工具 '{tool['name']}' 缺少 description 字段")
        
        except Exception as e:
            errors.append(f"配置验证过程中发生错误: {str(e)}")
        
        return errors
    
    def reload_config(self):
        """重新加载配置"""
        self.config = self._load_config()
        logger.info("MCP配置已重新加载")
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        servers = self.get_servers()
        enabled_servers = self.get_enabled_servers()
        all_tools = self.get_all_tools()
        
        # 统计每个服务器的工具数量
        server_stats = {}
        for server_name in enabled_servers:
            tools = self.get_enabled_tools(server_name)
            server_stats[server_name] = len(tools)
        
        return {
            "total_servers": len(servers),
            "enabled_servers": len(enabled_servers),
            "total_tools": len(all_tools),
            "server_stats": server_stats,
            "enabled_server_names": enabled_servers,
            "all_server_names": list(servers.keys())
        }


# 全局配置管理器实例
_config_manager = None

def get_mcp_config_manager() -> MCPConfigManager:
    """获取MCP配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = MCPConfigManager()
    return _config_manager

def reload_mcp_config():
    """重新加载MCP配置"""
    global _config_manager
    if _config_manager is not None:
        _config_manager.reload_config()
    else:
        _config_manager = MCPConfigManager() 