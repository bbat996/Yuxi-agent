"""
MCP工具配置文件
用于管理和分类所有可用的MCP工具
"""

from typing import Dict, List, Any, Optional
import os
import yaml
from typing import Dict, List, Any, Optional
from pathlib import Path
from src.utils.logging_config import logger
from config import PROJECT_DIR

CATEGORIES_PATH = Path(__file__).parent / "mcp_server" / "categories.yaml"

CONFIG_PATH = Path(__file__).parent / "mcp_server" / "mcp_server.yaml"

class MCPConfigManager:
    """MCP配置管理器"""

    _instance: Optional["MCPConfigManager"] = None

    def __new__(cls, *args, **kwargs) -> "MCPConfigManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径，默认为config/mcp_server.yaml
        """
        if hasattr(self, "config"):  # a more robust check for initialization
            return

        self.config_path = CONFIG_PATH
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        with open(self.config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        logger.info(f"成功加载MCP配置文件: {self.config_path}")
        return config

    def _load_categories(self) -> list:
        """加载分类配置文件"""
        if not CATEGORIES_PATH.exists():
            logger.warning(f"未找到分类配置文件: {CATEGORIES_PATH}")
            return []
        with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("categories", [])

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
        servers = self.get_enabled_servers()
        # 获取项目根目录，以便构建绝对路径
        project_root = str(PROJECT_DIR.resolve())
        server_root = os.path.join(project_root, "server")

        # 确保当前Python路径包含server目录
        current_pythonpath = os.environ.get("PYTHONPATH", "")
        if server_root not in current_pythonpath:
            if current_pythonpath:
                os.environ["PYTHONPATH"] = f"{server_root}{os.pathsep}{current_pythonpath}"
            else:
                os.environ["PYTHONPATH"] = server_root

        logger.info(f"Project root: {project_root}")
        logger.info(f"Server root: {server_root}")
        logger.info(f"Current PYTHONPATH: {os.environ['PYTHONPATH']}")

        for server_name in servers:
            server_config = self.get_server_config(server_name)
            if server_config:
                # 构建环境变量
                env = dict(os.environ)  # 复制当前环境变量
                custom_env = server_config.get("env", {})
                env.update(custom_env)  # 更新自定义环境变量

                # 确保PYTHONPATH包含server目录
                if "PYTHONPATH" not in env:
                    env["PYTHONPATH"] = server_root
                elif server_root not in env["PYTHONPATH"]:
                    env["PYTHONPATH"] = f"{server_root}{os.pathsep}{env['PYTHONPATH']}"

                logger.info(f"Setting up MCP server '{server_name}':")
                logger.info(f"  - Module path: {server_config.get('module_path')}")
                logger.info(f"  - PYTHONPATH: {env['PYTHONPATH']}")

                connections[server_name] = {"transport": "stdio", "command": "python", "args": ["-m", server_config.get("module_path")], "env": env}
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
        servers = self.get_enabled_servers()

        for server_name in servers:
            server_config = self.get_server_config(server_name)
            if server_config:
                server_tools = server_config.get("tools", [])
                for tool in server_tools:
                    if isinstance(tool, dict) and "name" in tool:
                        tools.append(tool["name"])

        return tools

    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取指定工具的详细信息"""
        servers = self.get_enabled_servers()

        for server_name in servers:
            server_config = self.get_server_config(server_name)
            if server_config:
                server_tools = server_config.get("tools", [])
                for tool in server_tools:
                    if isinstance(tool, dict) and tool.get("name") == tool_name:
                        return {
                            "name": tool["name"],
                            "description": tool.get("description", ""),
                            "server": server_name,
                            "parameters": tool.get("parameters", {}),
                            "enabled": True,
                        }

        return None

    def search_tools(self, keyword: str) -> List[str]:
        """搜索工具"""
        matching_tools = []
        servers = self.get_enabled_servers()

        for server_name in servers:
            server_config = self.get_server_config(server_name)
            if server_config:
                server_tools = server_config.get("tools", [])
                for tool in server_tools:
                    if isinstance(tool, dict) and "name" in tool:
                        tool_name = tool["name"]
                        description = tool.get("description", "")

                        # 搜索工具名称和描述
                        if keyword.lower() in tool_name.lower() or keyword.lower() in description.lower():
                            matching_tools.append(tool_name)

        return matching_tools

    def get_tools_by_server(self, server_name: str) -> List[Dict[str, Any]]:
        """获取指定服务器的工具列表"""
        server_config = self.get_server_config(server_name)
        if not server_config:
            return []

        tools = server_config.get("tools", [])
        return [tool for tool in tools if isinstance(tool, dict)]

    def get_server_tools_by_category(self, server_name: str) -> Dict[str, List[Dict[str, Any]]]:
        """获取服务器的工具分类（兼容旧接口）"""
        tools = self.get_tools_by_server(server_name)
        return {"all": tools}

    def get_tool_categories(self) -> Dict[str, Any]:
        """获取工具分类配置（兼容旧接口）"""
        # 根据服务器名称生成分类
        categories = {}
        servers = self.get_servers()

        for server_name, server_config in servers.items():
            if isinstance(server_config, dict) and server_config.get("enabled", False):
                tools = server_config.get("tools", [])
                tool_names = [tool["name"] for tool in tools if isinstance(tool, dict) and "name" in tool]

                categories[server_name] = {"description": f"{server_name} 工具集", "tools": tool_names, "servers": [server_name]}

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

    def validate_config(self) -> List[str]:
        """验证配置"""
        errors = []
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
            "all_server_names": list(servers.keys()),
        }

    def save_config(self):
        """保存当前配置到文件"""
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(self.config, f, allow_unicode=True, sort_keys=False)

    def add_server(self, server_key: str, server_data: dict):
        servers = self.config.setdefault("servers", {})
        if server_key in servers:
            raise ValueError(f"服务器 '{server_key}' 已存在")
        servers[server_key] = server_data
        self.save_config()

    def update_server(self, server_key: str, server_data: dict):
        servers = self.config.setdefault("servers", {})
        if server_key not in servers:
            raise ValueError(f"服务器 '{server_key}' 不存在")
        servers[server_key].update(server_data)
        self.save_config()

    def delete_server(self, server_key: str):
        servers = self.config.setdefault("servers", {})
        if server_key not in servers:
            raise ValueError(f"服务器 '{server_key}' 不存在")
        del servers[server_key]
        self.save_config()

    def toggle_server(self, server_key: str, enabled: bool):
        servers = self.config.setdefault("servers", {})
        if server_key not in servers:
            raise ValueError(f"服务器 '{server_key}' 不存在")
        servers[server_key]["enabled"] = enabled
        self.save_config()


    @classmethod  
    def reload_config(cls):
        """重新加载MCP配置（类方法）"""
        cls._instance = None
        instance = cls.get_instance()
        instance.config = instance._load_config()
        logger.info("MCP配置已重新加载")

    @classmethod
    def get_instance(cls) -> "MCPConfigManager":
        return cls()

    @classmethod
    def get_tool_categories(cls) -> Dict[str, Any]:
        return cls.get_instance().get_tool_categories()

    @classmethod
    def get_tools_by_category(cls, category_name: str) -> List[str]:
        return cls.get_instance().get_tools_by_category(category_name)

    @classmethod
    def get_all_tools(cls) -> List[str]:
        return cls.get_instance().get_all_tools()

    @classmethod
    def get_tool_info(cls, tool_name: str) -> Optional[Dict[str, Any]]:
        return cls.get_instance().get_tool_info(tool_name)

    @classmethod
    def search_tools(cls, keyword: str) -> List[str]:
        return cls.get_instance().search_tools(keyword)

    @classmethod
    def get_tools_overview(cls) -> Dict[str, Any]:
        return cls.get_instance().get_config_summary()

    @classmethod
    def get_enabled_tools(cls) -> List[Dict[str, Any]]:
        instance = cls.get_instance()
        all_tools = instance.get_all_tools()
        tools_info = []
        for tool_name in all_tools:
            tool_info = instance.get_tool_info(tool_name)
            if tool_info:
                tools_info.append(tool_info)
        return tools_info

    @classmethod
    def get_tools_by_server(cls, server_name: str) -> List[Dict[str, Any]]:
        return cls.get_instance().get_tools_by_server(server_name)

    @classmethod
    def get_servers(cls) -> Dict[str, Any]:
        instance = cls.get_instance()
        if instance.config is None:
            return {}
        servers = instance.config.get("servers", {})
        return servers if isinstance(servers, dict) else {}

    @classmethod
    def get_enabled_servers(cls) -> List[str]:
        instance = cls.get_instance()
        servers = cls.get_servers()  # 使用类方法避免递归
        enabled_servers = []
        for server_name, server_config in servers.items():
            if isinstance(server_config, dict) and server_config.get("enabled", False):
                enabled_servers.append(server_name)
        return enabled_servers

    @classmethod
    def get_server_config(cls, server_name: str) -> Optional[Dict[str, Any]]:
        servers = cls.get_servers()
        return servers.get(server_name)

    @classmethod
    def get_server_tools(cls, server_name: str) -> List[str]:
        return cls.get_instance().get_enabled_tools(server_name)

    @classmethod
    def get_all_categories(cls) -> list:
        """获取所有分类列表"""
        instance = cls.get_instance()
        return instance._load_categories()
