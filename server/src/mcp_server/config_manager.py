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
            "builtin_servers": {
                "math": {
                    "enabled": True,
                    "name": "Math Tools Server",
                    "description": "数学计算工具服务器",
                    "server_type": "builtin",
                    "module_path": "src.mcp_server.math_tools",
                    "class_name": "mcp"
                },
                "time": {
                    "enabled": True,
                    "name": "Time Tools Server",
                    "description": "时间日期处理工具服务器",
                    "server_type": "builtin",
                    "module_path": "src.mcp_server.time_tools",
                    "class_name": "mcp"
                },
                "network": {
                    "enabled": True,
                    "name": "Network Tools Server",
                    "description": "网络工具服务器",
                    "server_type": "builtin",
                    "module_path": "src.mcp_server.network_tools",
                    "class_name": "mcp"
                },
                "file": {
                    "enabled": True,
                    "name": "File Tools Server",
                    "description": "文件操作工具服务器",
                    "server_type": "builtin",
                    "module_path": "src.mcp_server.file_tools",
                    "class_name": "mcp"
                },
                "text": {
                    "enabled": True,
                    "name": "Text Tools Server",
                    "description": "文本处理工具服务器",
                    "server_type": "builtin",
                    "module_path": "src.mcp_server.text_tools",
                    "class_name": "mcp"
                },
                "system": {
                    "enabled": True,
                    "name": "System Tools Server",
                    "description": "系统信息工具服务器",
                    "server_type": "builtin",
                    "module_path": "src.mcp_server.system_tools",
                    "class_name": "mcp"
                }
            },
            "external_servers": {},
            "global_config": {
                "default_servers": ["math", "time", "network", "file", "text", "system"],
                "connection_timeout": 30,
                "max_connections": 10,
                "log_level": "INFO"
            }
        }
    
    def get_builtin_servers(self) -> Dict[str, Any]:
        """获取内置服务器配置"""
        if self.config is None:
            return {}
        return self.config.get("builtin_servers", {})
    
    def get_external_servers(self) -> Dict[str, Any]:
        """获取外部服务器配置"""
        if self.config is None:
            return {}
        return self.config.get("external_servers", {})
    
    def get_global_config(self) -> Dict[str, Any]:
        """获取全局配置"""
        if self.config is None:
            return {}
        return self.config.get("global_config", {})
    
    def get_enabled_servers(self) -> List[str]:
        """获取已启用的服务器列表"""
        enabled_servers = []
        
        try:
            # 检查内置服务器
            builtin_servers = self.get_builtin_servers()
            if builtin_servers:
                for server_name, server_config in builtin_servers.items():
                    if isinstance(server_config, dict) and server_config.get("enabled", False):
                        enabled_servers.append(server_name)
            
            # 检查外部服务器
            external_servers = self.get_external_servers()
            if external_servers:
                for server_name, server_config in external_servers.items():
                    if isinstance(server_config, dict) and server_config.get("enabled", False):
                        enabled_servers.append(server_name)
        except Exception as e:
            logger.error(f"获取已启用服务器列表时出错: {e}")
            # 返回空列表而不是抛出异常
        
        return enabled_servers
    
    def get_server_config(self, server_name: str) -> Optional[Dict[str, Any]]:
        """获取指定服务器的配置"""
        # 先检查内置服务器
        builtin_servers = self.get_builtin_servers()
        if server_name in builtin_servers:
            return builtin_servers[server_name]
        
        # 再检查外部服务器
        external_servers = self.get_external_servers()
        if server_name in external_servers:
            return external_servers[server_name]
        
        return None
    
    def get_server_connections(self) -> Dict[str, Any]:
        """获取服务器连接配置（用于langchain-mcp-adapters）"""
        connections = {}
        
        try:
            # 处理内置服务器
            builtin_servers = self.get_builtin_servers()
            if builtin_servers:
                for server_name, server_config in builtin_servers.items():
                    if isinstance(server_config, dict) and server_config.get("enabled", False):
                        # 内置服务器使用stdio传输
                        connections[server_name] = {
                            "transport": "stdio",
                            "command": "python",
                            "args": ["-m", server_config["module_path"]]
                        }
            
            # 处理外部服务器
            external_servers = self.get_external_servers()
            if external_servers:
                for server_name, server_config in external_servers.items():
                    if isinstance(server_config, dict) and server_config.get("enabled", False):
                        connections[server_name] = {
                            "transport": server_config.get("transport", "stdio"),
                            "command": server_config.get("command"),
                            "args": server_config.get("args", []),
                            "env": server_config.get("env", {})
                        }
        except Exception as e:
            logger.error(f"获取服务器连接配置时出错: {e}")
            # 返回空字典而不是抛出异常
        
        return connections
    
    def get_tool_categories(self) -> Dict[str, Any]:
        """获取工具分类配置"""
        if self.config is None:
            return {}
        return self.config.get("tool_categories", {})
    
    def get_tool_limits(self) -> Dict[str, Any]:
        """获取工具调用限制配置"""
        global_config = self.get_global_config()
        return global_config.get("tool_limits", {})
    
    def get_security_config(self) -> Dict[str, Any]:
        """获取安全配置"""
        global_config = self.get_global_config()
        return global_config.get("security", {})
    
    def get_environment_variables(self) -> Dict[str, str]:
        """获取环境变量配置"""
        if self.config is None:
            return {}
        env_config = self.config.get("environment_variables", {})
        
        # 处理环境变量替换
        processed_env = {}
        for key, value in env_config.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                # 从环境变量中获取值
                env_key = value[2:-1]
                processed_env[key] = os.getenv(env_key, "")
            else:
                processed_env[key] = value
        
        return processed_env
    
    def is_server_enabled(self, server_name: str) -> bool:
        """检查服务器是否启用"""
        server_config = self.get_server_config(server_name)
        return server_config is not None and server_config.get("enabled", False)
    
    def get_enabled_tools(self, server_name: str) -> List[str]:
        """获取指定服务器启用的工具列表"""
        server_config = self.get_server_config(server_name)
        if not server_config:
            return []
        
        tools = []
        tools_config = server_config.get("tools", {})
        
        for category_name, category_config in tools_config.items():
            if category_config.get("enabled", True):
                tools.extend(category_config.get("tools", []))
        
        return tools
    
    def get_server_tools_by_category(self, server_name: str) -> Dict[str, List[str]]:
        """获取指定服务器按分类组织的工具"""
        server_config = self.get_server_config(server_name)
        if not server_config:
            return {}
        
        tools_by_category = {}
        tools_config = server_config.get("tools", {})
        
        for category_name, category_config in tools_config.items():
            if category_config.get("enabled", True):
                tools_by_category[category_name] = category_config.get("tools", [])
        
        return tools_by_category
    
    def get_all_tools(self) -> List[str]:
        """获取所有启用的工具列表"""
        all_tools = []
        
        for server_name in self.get_enabled_servers():
            tools = self.get_enabled_tools(server_name)
            all_tools.extend(tools)
        
        return all_tools
    
    def get_tools_by_category(self, category_name: str) -> List[str]:
        """根据分类获取工具列表"""
        tool_categories = self.get_tool_categories()
        if category_name in tool_categories:
            return tool_categories[category_name].get("tools", [])
        return []
    
    def search_tools(self, keyword: str) -> List[str]:
        """搜索工具"""
        all_tools = self.get_all_tools()
        matching_tools = []
        
        for tool in all_tools:
            if keyword.lower() in tool.lower():
                matching_tools.append(tool)
        
        return matching_tools
    
    def validate_config(self) -> List[str]:
        """验证配置文件的正确性"""
        errors = []
        
        # 检查配置是否为None
        if self.config is None:
            errors.append("配置为空，无法验证")
            return errors
        
        # 检查必要的配置项
        if "builtin_servers" not in self.config:
            errors.append("缺少 builtin_servers 配置项")
        
        if "external_servers" not in self.config:
            errors.append("缺少 external_servers 配置项")
        
        if "global_config" not in self.config:
            errors.append("缺少 global_config 配置项")
        
        # 检查内置服务器配置
        builtin_servers = self.get_builtin_servers()
        for server_name, server_config in builtin_servers.items():
            if not isinstance(server_config, dict):
                errors.append(f"服务器 {server_name} 配置格式错误")
                continue
            
            required_fields = ["enabled", "name", "description", "module_path", "class_name"]
            for field in required_fields:
                if field not in server_config:
                    errors.append(f"服务器 {server_name} 缺少必要字段: {field}")
        
        # 检查外部服务器配置
        external_servers = self.get_external_servers()
        for server_name, server_config in external_servers.items():
            if not isinstance(server_config, dict):
                errors.append(f"外部服务器 {server_name} 配置格式错误")
                continue
            
            required_fields = ["enabled", "name", "description", "transport", "command"]
            for field in required_fields:
                if field not in server_config:
                    errors.append(f"外部服务器 {server_name} 缺少必要字段: {field}")
        
        return errors
    
    def reload_config(self):
        """重新加载配置"""
        logger.info("重新加载MCP配置...")
        self.config = self._load_config()
        
        # 确保config不为None
        if self.config is None:
            logger.warning("配置重新加载失败，使用默认配置")
            self.config = self._get_default_config()
        
        logger.info("MCP配置重新加载完成")
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要信息"""
        enabled_servers = self.get_enabled_servers()
        builtin_servers = self.get_builtin_servers()
        external_servers = self.get_external_servers()
        
        summary = {
            "total_servers": len(builtin_servers) + len(external_servers),
            "enabled_servers": len(enabled_servers),
            "builtin_servers": len(builtin_servers),
            "external_servers": len(external_servers),
            "enabled_server_names": enabled_servers,
            "config_path": str(self.config_path),
            "config_valid": len(self.validate_config()) == 0
        }
        
        # 统计工具数量
        total_tools = 0
        tools_by_server = {}
        for server_name in enabled_servers:
            tools = self.get_enabled_tools(server_name)
            tools_by_server[server_name] = len(tools)
            total_tools += len(tools)
        
        summary["total_tools"] = total_tools
        summary["tools_by_server"] = tools_by_server
        
        return summary


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
    config_manager = get_mcp_config_manager()
    config_manager.reload_config() 