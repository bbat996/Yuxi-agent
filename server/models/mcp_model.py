from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field


class MCPToolParameter(BaseModel):
    """MCP工具参数模型"""
    name: str = Field(..., description="参数名称")
    type: str = Field(..., description="参数类型，例如string, integer, boolean等")
    required: bool = Field(False, description="是否为必填参数")
    description: str = Field("", description="参数描述")
    default: Optional[Any] = Field(None, description="参数默认值")


class MCPTool(BaseModel):
    """MCP工具模型"""
    name: str = Field(..., description="工具名称")
    description: str = Field("", description="工具描述")
    parameters: List[MCPToolParameter] = Field(default_factory=list, description="工具参数列表")
    return_schema: Dict[str, Any] = Field(default_factory=dict, description="返回值模式定义")
    examples: List[Dict[str, Any]] = Field(default_factory=list, description="使用示例")


class MCPServer(BaseModel):
    """MCP服务器模型"""
    id: str = Field(..., description="服务器唯一标识")
    name: str = Field(..., description="服务器名称")
    type: str = Field(..., description="服务器类型，内置或外部")
    version: str = Field("1.0.0", description="服务器版本")
    status: str = Field("offline", description="服务器状态，online或offline")
    description: str = Field("", description="服务器描述")
    endpoint: str = Field(..., description="服务器API端点")
    auth_type: Optional[str] = Field(None, description="认证类型，例如none, basic, token等")
    auth_config: Dict[str, Any] = Field(default_factory=dict, description="认证配置")
    tools: List[MCPTool] = Field(default_factory=list, description="工具列表")
    created_at: int = Field(0, description="创建时间")
    updated_at: int = Field(0, description="更新时间")


class MCPServerList(BaseModel):
    """MCP服务器列表模型"""
    servers: List[MCPServer] = Field(default_factory=list, description="MCP服务器列表")


class MCPToolRequest(BaseModel):
    """MCP工具调用请求模型"""
    server_id: str = Field(..., description="服务器ID")
    tool_name: str = Field(..., description="工具名称")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="调用参数")


class MCPToolResponse(BaseModel):
    """MCP工具调用响应模型"""
    success: bool = Field(..., description="是否调用成功")
    result: Any = Field(None, description="调用结果")
    error: Optional[str] = Field(None, description="错误信息")


class MCPServerCreateRequest(BaseModel):
    """创建MCP服务器请求模型"""
    name: str = Field(..., description="服务器名称")
    type: str = Field(..., description="服务器类型，内置或外部")
    description: str = Field("", description="服务器描述")
    endpoint: str = Field(..., description="服务器API端点")
    auth_type: Optional[str] = Field(None, description="认证类型，例如none, basic, token等")
    auth_config: Dict[str, Any] = Field(default_factory=dict, description="认证配置")


class MCPServerUpdateRequest(BaseModel):
    """更新MCP服务器请求模型"""
    name: Optional[str] = Field(None, description="服务器名称")
    description: Optional[str] = Field(None, description="服务器描述")
    endpoint: Optional[str] = Field(None, description="服务器API端点")
    auth_type: Optional[str] = Field(None, description="认证类型，例如none, basic, token等")
    auth_config: Optional[Dict[str, Any]] = Field(None, description="认证配置")
    status: Optional[str] = Field(None, description="服务器状态，online或offline")
