"""
MCP工具配置文件
用于管理和分类所有可用的MCP工具
"""

from typing import Dict, List, Any, Optional
from .config_manager import get_mcp_config_manager

def get_tool_categories() -> Dict[str, Any]:
    """获取工具分类配置"""
    config_manager = get_mcp_config_manager()
    return config_manager.get_tool_categories()

def get_tool_details() -> Dict[str, Any]:
    """获取工具详细信息"""
    config_manager = get_mcp_config_manager()
    all_tools = config_manager.get_all_tools()
    
    # 构建工具详细信息字典
    tool_details = {}
    for tool_name in all_tools:
        tool_info = config_manager.get_tool_info(tool_name)
        if tool_info:
            tool_details[tool_name] = tool_info
    
    return tool_details

def get_tools_by_category(category_name: str) -> List[str]:
    """根据分类获取工具列表"""
    config_manager = get_mcp_config_manager()
    return config_manager.get_tools_by_category(category_name)

def get_all_tools() -> List[str]:
    """获取所有工具列表"""
    config_manager = get_mcp_config_manager()
    return config_manager.get_all_tools()

def get_tool_info(tool_name: str) -> Optional[Dict[str, Any]]:
    """获取指定工具的详细信息"""
    config_manager = get_mcp_config_manager()
    return config_manager.get_tool_info(tool_name)

def search_tools(keyword: str) -> List[str]:
    """搜索工具"""
    config_manager = get_mcp_config_manager()
    return config_manager.search_tools(keyword)

def get_tools_overview() -> Dict[str, Any]:
    """获取工具概览信息"""
    config_manager = get_mcp_config_manager()
    return config_manager.get_config_summary()

def get_enabled_tools() -> List[Dict[str, Any]]:
    """获取已启用的工具列表"""
    config_manager = get_mcp_config_manager()
    all_tools = config_manager.get_all_tools()
    
    tools_info = []
    for tool_name in all_tools:
        tool_info = config_manager.get_tool_info(tool_name)
        if tool_info:
            tools_info.append(tool_info)
    
    return tools_info

def get_tools_by_server(server_name: str) -> List[Dict[str, Any]]:
    """获取指定服务器的工具列表"""
    config_manager = get_mcp_config_manager()
    return config_manager.get_tools_by_server(server_name)

def get_tool_parameters(tool_name: str) -> Dict[str, Any]:
    """获取指定工具的参数列表"""
    tool_info = get_tool_info(tool_name)
    if tool_info:
        return tool_info.get("parameters", {})
    return {}

def get_tool_return_type(tool_name: str) -> str:
    """获取指定工具的返回类型（兼容旧接口）"""
    # 新配置格式中没有明确的返回类型，默认为string
    return "string"

def is_tool_enabled(tool_name: str) -> bool:
    """检查工具是否启用"""
    tool_info = get_tool_info(tool_name)
    return tool_info is not None and tool_info.get("enabled", True)

def get_tool_category(tool_name: str) -> Optional[str]:
    """获取工具所属分类（兼容旧接口）"""
    tool_info = get_tool_info(tool_name)
    if tool_info:
        return tool_info.get("server")  # 使用服务器名称作为分类
    return None

def get_tool_server(tool_name: str) -> Optional[str]:
    """获取工具所属服务器"""
    tool_info = get_tool_info(tool_name)
    if tool_info:
        return tool_info.get("server")
    return None

def get_servers() -> Dict[str, Any]:
    """获取所有服务器配置"""
    config_manager = get_mcp_config_manager()
    return config_manager.get_servers()

def get_enabled_servers() -> List[str]:
    """获取已启用的服务器列表"""
    config_manager = get_mcp_config_manager()
    return config_manager.get_enabled_servers()

def get_server_config(server_name: str) -> Optional[Dict[str, Any]]:
    """获取指定服务器的配置"""
    config_manager = get_mcp_config_manager()
    return config_manager.get_server_config(server_name)

def get_server_tools(server_name: str) -> List[str]:
    """获取指定服务器的工具列表"""
    config_manager = get_mcp_config_manager()
    return config_manager.get_enabled_tools(server_name) 
