"""
MCP服务层
负责处理MCP服务器的业务逻辑，包括服务器管理、工具调用等
"""

import time
import uuid
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import yaml
from pathlib import Path

from models.mcp_model import (
    MCPServer, MCPServerList, MCPTool, MCPToolParameter, 
    MCPToolRequest, MCPToolResponse, 
    MCPServerCreateRequest, MCPServerUpdateRequest
)
from config.mcp_server_config import MCPConfigManager
from src.utils.logging_config import logger


class MCPService:
    """MCP服务管理类"""
    
    def __init__(self):
        self.config_manager = MCPConfigManager()
    
    def get_server_list(self, enabled_only: bool = False) -> MCPServerList:
        """
        获取MCP服务器列表
        
        Args:
            enabled_only: 是否只返回已启用的服务器
            
        Returns:
            服务器列表
        """
        servers = []
        
        if enabled_only:
            server_names = MCPConfigManager.get_enabled_servers()
        else:
            server_names = list(MCPConfigManager.get_servers().keys())
            
        for server_name in server_names:
            server_config = MCPConfigManager.get_server_config(server_name)
            if server_config:
                # 将配置转换为MCPServer模型
                server_id = server_config.get("id", str(uuid.uuid4()))
                tools = []
                
                # 处理工具列表
                for tool_config in server_config.get("tools", []):
                    # 构建工具参数
                    parameters = []
                    for param_config in tool_config.get("parameters", []):
                        parameters.append(MCPToolParameter(
                            name=param_config.get("name", ""),
                            type=param_config.get("type", "string"),
                            required=param_config.get("required", False),
                            description=param_config.get("description", ""),
                            default=param_config.get("default")
                        ))
                    
                    # 构建工具
                    tools.append(MCPTool(
                        name=tool_config.get("name", ""),
                        description=tool_config.get("description", ""),
                        parameters=parameters,
                        return_schema=tool_config.get("return_schema", {}),
                        examples=tool_config.get("examples", [])
                    ))
                
                # 构建服务器
                server = MCPServer(
                    id=server_id,
                    name=server_name,
                    type=server_config.get("type", "internal"),
                    version=server_config.get("version", "1.0.0"),
                    status="online" if server_config.get("enabled", False) else "offline",
                    description=server_config.get("description", ""),
                    endpoint=server_config.get("endpoint", ""),
                    auth_type=server_config.get("auth_type"),
                    auth_config=server_config.get("auth_config", {}),
                    tools=tools,
                    created_at=server_config.get("created_at", 0),
                    updated_at=server_config.get("updated_at", 0)
                )
                
                servers.append(server)
        
        return MCPServerList(servers=servers)
    
    def get_server_by_id(self, server_id: str) -> Optional[MCPServer]:
        """
        根据ID获取服务器
        
        Args:
            server_id: 服务器ID
            
        Returns:
            服务器信息，如果不存在则返回None
        """
        server_list = self.get_server_list()
        for server in server_list.servers:
            if server.id == server_id:
                return server
        return None
    
    def get_server_by_name(self, server_name: str) -> Optional[MCPServer]:
        """
        根据名称获取服务器
        
        Args:
            server_name: 服务器名称
            
        Returns:
            服务器信息，如果不存在则返回None
        """
        server_config = MCPConfigManager.get_server_config(server_name)
        if not server_config:
            return None
            
        # 将配置转换为MCPServer模型
        server_id = server_config.get("id", str(uuid.uuid4()))
        tools = []
        
        # 处理工具列表
        for tool_config in server_config.get("tools", []):
            # 构建工具参数
            parameters = []
            for param_config in tool_config.get("parameters", []):
                parameters.append(MCPToolParameter(
                    name=param_config.get("name", ""),
                    type=param_config.get("type", "string"),
                    required=param_config.get("required", False),
                    description=param_config.get("description", ""),
                    default=param_config.get("default")
                ))
            
            # 构建工具
            tools.append(MCPTool(
                name=tool_config.get("name", ""),
                description=tool_config.get("description", ""),
                parameters=parameters,
                return_schema=tool_config.get("return_schema", {}),
                examples=tool_config.get("examples", [])
            ))
        
        # 构建服务器
        return MCPServer(
            id=server_id,
            name=server_name,
            type=server_config.get("type", "internal"),
            version=server_config.get("version", "1.0.0"),
            status="online" if server_config.get("enabled", False) else "offline",
            description=server_config.get("description", ""),
            endpoint=server_config.get("endpoint", ""),
            auth_type=server_config.get("auth_type"),
            auth_config=server_config.get("auth_config", {}),
            tools=tools,
            created_at=server_config.get("created_at", 0),
            updated_at=server_config.get("updated_at", 0)
        )
    
    def create_server(self, server_request: MCPServerCreateRequest) -> MCPServer:
        """
        创建新的MCP服务器
        
        Args:
            server_request: 服务器创建请求
            
        Returns:
            创建的服务器
        """
        # 生成唯一ID
        server_id = str(uuid.uuid4())
        
        # 准备服务器配置
        server_config = {
            "id": server_id,
            "type": server_request.type,
            "description": server_request.description,
            "endpoint": server_request.endpoint,
            "auth_type": server_request.auth_type,
            "auth_config": server_request.auth_config,
            "enabled": False,  # 默认禁用
            "created_at": int(time.time()),
            "updated_at": int(time.time()),
            "tools": []  # 初始为空工具列表
        }
        
        # 生成服务器名称
        server_name = f"{server_request.name.lower().replace(' ', '_')}"
        
        # 添加到配置
        self.config_manager.add_server(server_name, server_config)
        
        # 返回创建的服务器
        return self.get_server_by_name(server_name)
    
    def update_server(self, server_name: str, update_request: MCPServerUpdateRequest) -> MCPServer:
        """
        更新服务器配置
        
        Args:
            server_name: 服务器名称
            update_request: 更新请求
            
        Returns:
            更新后的服务器
        """
        server_config = {}
        
        # 只更新提供的字段
        if update_request.name is not None:
            server_config["name"] = update_request.name
        
        if update_request.description is not None:
            server_config["description"] = update_request.description
        
        if update_request.endpoint is not None:
            server_config["endpoint"] = update_request.endpoint
        
        if update_request.auth_type is not None:
            server_config["auth_type"] = update_request.auth_type
        
        if update_request.auth_config is not None:
            server_config["auth_config"] = update_request.auth_config
        
        if update_request.status is not None:
            server_config["enabled"] = (update_request.status == "online")
        
        # 更新时间
        server_config["updated_at"] = int(time.time())
        
        # 更新配置
        self.config_manager.update_server(server_name, server_config)
        
        # 返回更新后的服务器
        return self.get_server_by_name(server_name)
    
    def delete_server(self, server_name: str) -> bool:
        """
        删除服务器
        
        Args:
            server_name: 服务器名称
            
        Returns:
            是否删除成功
        """
        self.config_manager.delete_server(server_name)
        return True
    
    def toggle_server_status(self, server_name: str, enabled: bool) -> MCPServer:
        """
        切换服务器状态
        
        Args:
            server_name: 服务器名称
            enabled: 是否启用
            
        Returns:
            更新后的服务器
        """
        self.config_manager.toggle_server(server_name, enabled)
        return self.get_server_by_name(server_name)
    
    def invoke_tool(self, request: MCPToolRequest) -> MCPToolResponse:
        """
        调用MCP工具
        
        Args:
            request: 工具调用请求
            
        Returns:
            调用响应
        """
        # 这里需要实际实现调用逻辑，可能涉及到与其他服务的交互
        # 目前只返回一个模拟结果
        return MCPToolResponse(
            success=True,
            result={"message": f"调用工具 {request.tool_name} 成功", "parameters": request.parameters},
            error=None
        )
    
    def reload_configuration(self) -> Dict[str, Any]:
        """
        重新加载MCP配置
        
        Returns:
        
        def delete_server(self, server_name: str) -> bool:
            """
            删除服务器
            
            Args:
                server_name: 服务器名称
                
            Returns:
                是否删除成功
            """
            self.config_manager.delete_server(server_name)
            return True
        
        def toggle_server_status(self, server_name: str, enabled: bool) -> MCPServer:
            """
            切换服务器状态
            
            Args:
                server_name: 服务器名称
                enabled: 是否启用
                
            Returns:
                更新后的服务器
            """
            self.config_manager.toggle_server(server_name, enabled)
            return self.get_server_by_name(server_name)
        
        def invoke_tool(self, request: MCPToolRequest) -> MCPToolResponse:
            """
            调用MCP工具
            
            Args:
                request: 工具调用请求
                
            Returns:
                调用响应
            """
            # 这里需要实际实现调用逻辑，可能涉及到与其他服务的交互
            # 目前只返回一个模拟结果
            return MCPToolResponse(
                success=True,
                result={"message": f"调用工具 {request.tool_name} 成功", "parameters": request.parameters},
                error=None
            )
        
        def reload_configuration(self) -> Dict[str, Any]:
            """
            重新加载MCP配置
            
            Returns:
                配置摘要
            """
            MCPConfigManager.reload_config()
            return MCPConfigManager.get_instance().get_config_summary()
        
        def validate_configuration(self) -> Dict[str, Any]:
            """
            验证MCP配置
            
            Returns:
                验证结果
            """
            errors = MCPConfigManager.get_instance().validate_config()
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "config_path": str(MCPConfigManager.get_instance().config_path)
            }
        
        def get_server_logs(self, server_name: str, log_type: Optional[str] = None, 
                          limit: int = 100, skip: int = 0,
                          start_time: Optional[str] = None, end_time: Optional[str] = None) -> List[Dict[str, Any]]:
            """
            获取MCP服务器日志
            
            Args:
                server_name: 服务器名称
                log_type: 日志类型 (info, error, warning, debug)
                limit: 返回的日志条数限制
                skip: 跳过的日志条数
                start_time: 开始时间，格式：YYYY-MM-DD HH:MM:SS
                end_time: 结束时间，格式：YYYY-MM-DD HH:MM:SS
                
            Returns:
                日志列表
            """
            # 获取服务器配置以验证服务器是否存在
            server = self.get_server_by_name(server_name)
            if not server:
                return []
            
            # 这里实现日志检索逻辑
            # 在实际应用中，日志可能存储在文件、数据库或通过API从远程服务器获取
            # 这里使用模拟数据进行演示
            
            # 模拟日志数据 - 在实际项目中替换为真实日志读取逻辑
            mock_logs = self._generate_mock_logs(server_name, 500)
            
            # 根据日志类型过滤
            if log_type:
                mock_logs = [log for log in mock_logs if log.get("level") == log_type]
            
            # 根据时间过滤
            if start_time:
                mock_logs = [log for log in mock_logs if log.get("timestamp") >= start_time]
            if end_time:
                mock_logs = [log for log in mock_logs if log.get("timestamp") <= end_time]
            
            # 排序 - 默认按时间逆序排序
            mock_logs = sorted(mock_logs, key=lambda x: x.get("timestamp"), reverse=True)
            
            # 应用分页
            return mock_logs[skip:skip+limit]
        
        def clear_server_logs(self, server_name: str, log_type: Optional[str] = None) -> Dict[str, Any]:
            """
            清除MCP服务器日志
            
            Args:
                server_name: 服务器名称
                log_type: 日志类型，如果为None则清除所有类型的日志
                
            Returns:
                清除结果
            """
            # 获取服务器配置以验证服务器是否存在
            server = self.get_server_by_name(server_name)
            if not server:
                return {"cleared_count": 0}
            
            # 这里实现日志清除逻辑
            # 在实际应用中，可能需要删除文件、清除数据库表或调用远程API
            
            # 模拟清除过程
            return {"cleared_count": 50}  # 模拟清除50条日志
        
        def _generate_mock_logs(self, server_name: str, count: int = 100) -> List[Dict[str, Any]]:
            """
            生成模拟日志数据（仅用于演示）
            
            Args:
                server_name: 服务器名称
                count: 日志条数
                
            Returns:
                模拟日志列表
            """
            import random
            from datetime import datetime, timedelta
            
            log_levels = ["info", "warning", "error", "debug"]
            log_messages = [
                "服务启动成功",
                "连接到远程资源",
                "资源请求超时",
                "授权失败",
                "API调用成功",
                "处理请求中",
                "内存使用率达到警戒值",
                "CPU负载过高",
                "数据同步完成",
                "配置更新成功",
                "服务重启",
                "服务停止",
                "发生未知异常"
            ]
            
            logs = []
            now = datetime.now()
            
            for i in range(count):
                # 生成随机时间，最近的日志在前面
                log_time = now - timedelta(minutes=i*5)
                timestamp = log_time.strftime("%Y-%m-%d %H:%M:%S")
                
                level = random.choice(log_levels)
                message = random.choice(log_messages)
                
                # 为错误和警告添加更详细的信息
                details = None
                if level == "error":
                    details = f"错误代码: {random.randint(400, 599)}, 位置: {random.choice(['API服务', '配置管理', '资源处理', '连接池'])}"
                elif level == "warning":
                    details = f"警告级别: {random.randint(1, 5)}, 建议操作: {random.choice(['重试', '检查配置', '增加超时时间', '减少并发请求'])}"
                
                log_entry = {
                    "id": str(uuid.uuid4()),
                    "timestamp": timestamp,
                    "level": level,
                    "server": server_name,
                    "message": message,
                    "details": details
                }
                
                logs.append(log_entry)
                
            return logs
