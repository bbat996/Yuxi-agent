"""
MCP模块路由
提供MCP服务器管理、MCP工具查询、分类、搜索等功能
"""

import os
import json
import time
import random
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Query, HTTPException, Depends, Body, status
from server.dependencies.auth import get_admin_user, get_required_user
from server.models.user_model import User
from server.logger.base_logger import logger
from server.models.mcp_model import (
    MCPServer, MCPServerList, MCPTool, MCPToolParameter, 
    MCPToolRequest, MCPToolResponse, MCPServerListResponse,
    MCPServerCreateRequest, MCPServerUpdateRequest
)
from server.src.services.mcp_service import MCPService

# 创建MCPService实例
mcp_router = APIRouter()
mcp_service = MCPService()

# 定义日志类型常量
LOG_TYPES = {
    "info": "信息",
    "error": "错误",
    "warning": "警告",
    "debug": "调试"
}

# =============================================================================
# MCP工具相关接口
# =============================================================================

@mcp_router.get("/mcp/tools/categories")
async def get_mcp_tool_categories(
    current_user: User = Depends(get_admin_user)
):
    """
    获取MCP工具分类
    
    Returns:
        工具分类列表
    """
    categories = mcp_service.get_tool_categories()
    
    return {
        "success": True,
        "data": categories
    }


@mcp_router.get("/mcp/tools/list")
async def get_mcp_tools(
    category: Optional[str] = Query(None, description="分类名称"),
    server_name: Optional[str] = Query(None, description="服务器名称"),
    current_user: User = Depends(get_admin_user)
):
    """
    获取MCP工具列表
    
    Args:
        category: 分类名称，可选
        server_name: 服务器名称，可选
        
    Returns:
        工具列表
    """
    tools_info = mcp_service.get_tools(category=category, server_name=server_name)
    
    return {
        "success": True,
        "data": {
            "tools": tools_info,
            "total": len(tools_info),
            "category": category,
            "server": server_name
        }
    }


@mcp_router.get("/mcp/tools/search")
async def search_mcp_tools(
    keyword: str = Query(..., description="搜索关键词"),
    current_user: User = Depends(get_admin_user)
):
    """
    搜索MCP工具
    
    Args:
        keyword: 搜索关键词
        
    Returns:
        匹配的工具列表
    """
    tools_info = mcp_service.search_tools(keyword)
    
    return {
        "success": True,
        "data": {
            "tools": tools_info,
            "total": len(tools_info),
            "keyword": keyword
        }
    }


@mcp_router.get("/mcp/tools/{tool_name}")
async def get_mcp_tool_detail(
    tool_name: str,
    current_user: User = Depends(get_admin_user)
):
    """
    获取指定MCP工具的详细信息
    
    Args:
        tool_name: 工具名称
        
    Returns:
        工具详细信息
    """
    tool_info = mcp_service.get_tool_by_name(tool_name)
    
    if not tool_info:
        raise HTTPException(status_code=404, detail=f"找不到工具 '{tool_name}'")
    
    return {
        "success": True,
        "data": tool_info
    }


@mcp_router.get("/mcp/tools/overview")
async def get_mcp_tools_overview(
    current_user: User = Depends(get_admin_user)
):
    """
    获取MCP工具概览信息
    
    Returns:
        工具概览信息
    """
    overview = mcp_service.get_tools_overview()
    
    return {
        "success": True,
        "data": overview
    }


@mcp_router.get("/mcp/tools/random")
async def get_random_tools(
    count: int = Query(5, description="返回的工具数量", ge=1, le=20),
    current_user: User = Depends(get_admin_user)
):
    """
    获取随机工具
    
    Args:
        count: 返回的工具数量
        
    Returns:
        随机工具列表
    """
    random_tools = mcp_service.get_random_tools(count)
    
    return {
        "success": True,
        "data": {
            "tools": random_tools,
            "total": len(random_tools)
        }
    }


# =============================================================================
# MCP配置相关接口
# =============================================================================

@mcp_router.get("/mcp/config/summary")
async def get_mcp_config_summary(
    current_user: User = Depends(get_admin_user)
):
    """
    获取MCP配置摘要信息
    
    Returns:
        MCP配置摘要
    """
    summary = mcp_service.get_config_summary()
    
    return {
        "success": True,
        "data": summary
    }


@mcp_router.get("/mcp/servers")
async def get_mcp_servers(
    enabled_only: bool = Query(False, description="是否只返回已启用的服务器"),
    category: Optional[str] = Query(None, description="按分类筛选"),
    current_user: User = Depends(get_admin_user)
):
    """
    获取MCP服务器列表
    
    Args:
        enabled_only: 是否只返回已启用的服务器
        category: 分类名称，可选
        
    Returns:
        服务器列表
    """
    servers = mcp_service.get_servers(enabled_only=enabled_only, category=category)
    
    return {
        "success": True,
        "data": {
            "servers": servers,
            "total": len(servers),
            "enabled_only": enabled_only,
            "category": category
        }
    }


@mcp_router.get("/mcp/servers/{server_name}")
async def get_mcp_server_detail(
    server_name: str,
    current_user: User = Depends(get_admin_user)
):
    """
    获取指定MCP服务器的详细信息
    
    Args:
        server_name: 服务器名称
        
    Returns:
        服务器详细信息
    """
    server = mcp_service.get_server_by_name(server_name)
    
    if not server:
        raise HTTPException(status_code=404, detail=f"找不到服务器 '{server_name}'")
    
    return {
        "success": True,
        "data": server.dict()
    }


@mcp_router.post("/mcp/config/reload")
async def reload_mcp_configuration(
    current_user: User = Depends(get_admin_user)
):
    """
    重新加载MCP配置
    
    Returns:
        重新加载结果
    """
    summary = mcp_service.reload_configuration()
    
    return {
        "success": True,
        "data": summary
    }


@mcp_router.get("/mcp/config/validate")
async def validate_mcp_configuration(
    current_user: User = Depends(get_admin_user)
):
    """
    验证MCP配置
    
    Returns:
        配置验证结果
    """
    validation_result = mcp_service.validate_configuration()
    
    return {
        "success": validation_result["valid"],
        "data": validation_result
    }


@mcp_router.post("/mcp/servers", status_code=status.HTTP_201_CREATED)
async def create_mcp_server(
    server_request: MCPServerCreateRequest,
    current_user: User = Depends(get_admin_user)
):
    """
    创建新的MCP服务器
    
    Args:
        server_request: 服务器创建请求
        
    Returns:
        创建的服务器
    """
    server = mcp_service.create_server(server_request)
    
    return {
        "success": True,
        "data": server.dict()
    }

@mcp_router.put("/mcp/servers/{server_name}")
async def update_mcp_server(
    server_name: str,
    update_request: MCPServerUpdateRequest,
    current_user: User = Depends(get_admin_user)
):
    """
    更新MCP服务器
    
    Args:
        server_name: 服务器名称
        update_request: 更新请求
        
    Returns:
        更新后的服务器
    """
    server = mcp_service.update_server(server_name, update_request)
    
    return {
        "success": True,
        "data": server.dict()
    }

@mcp_router.delete("/mcp/servers/{server_name}")
async def delete_mcp_server(
    server_name: str,
    current_user: User = Depends(get_admin_user)
):
    """
    删除MCP服务器
    
    Args:
        server_name: 服务器名称
        
    Returns:
        删除结果
    """
    success = mcp_service.delete_server(server_name)
    
    return {
        "success": success,
        "data": {
            "server_name": server_name
        }
    }

@mcp_router.post("/mcp/servers/{server_name}/toggle")
async def toggle_mcp_server(
    server_name: str,
    body: Dict[str, Any] = Body(..., example={"enabled": True}),
    current_user: User = Depends(get_admin_user)
):
    """
    启用/禁用MCP服务器
    
    Args:
        server_name: 服务器名称
        body: 请求体，包含enabled字段
        
    Returns:
        更新后的服务器
    """
    enabled = body.get("enabled", False)
    server = mcp_service.toggle_server_status(server_name, enabled)
    
    return {
        "success": True,
        "data": server.dict()
    }


# =============================================================================
# MCP日志相关接口
# =============================================================================

@mcp_router.get("/mcp/servers/{server_name}/logs")
async def get_server_logs(
    server_name: str,
    log_type: Optional[str] = Query(None, description="日志类型，例如: info, error, warning, debug"),
    limit: int = Query(100, description="返回的日志条数限制"),
    skip: int = Query(0, description="跳过的日志条数"),
    start_time: Optional[str] = Query(None, description="开始时间，格式：YYYY-MM-DD HH:MM:SS"),
    end_time: Optional[str] = Query(None, description="结束时间，格式：YYYY-MM-DD HH:MM:SS"),
    current_user: User = Depends(get_admin_user)
):
    """获取指定MCP服务器的日志"""
    logs = mcp_service.get_server_logs(
        server_name=server_name,
        log_type=log_type,
        limit=limit,
        skip=skip,
        start_time=start_time,
        end_time=end_time
    )
    
    return {
        "success": True,
        "data": {
            "logs": logs,
            "total": len(logs),
            "server_name": server_name,
            "log_type": log_type,
            "available_log_types": ["info", "error", "warning", "debug"]
        }
    }

@mcp_router.delete("/mcp/servers/{server_name}/logs")
async def clear_server_logs(
    server_name: str,
    log_type: Optional[str] = Query(None, description="日志类型，例如: info, error, warning, debug"),
    current_user: User = Depends(get_admin_user)
):
    """清除指定MCP服务器的日志"""
    result = mcp_service.clear_server_logs(
        server_name=server_name,
        log_type=log_type
    )
    
    return {
        "success": True,
        "data": {
            "server_name": server_name,
            "log_type": log_type,
            "cleared_count": result.get("cleared_count", 0)
        }
    }

# =============================================================================
# 技能管理相关接口（基于配置文件）
# =============================================================================

@mcp_router.get("/skills/categories")
async def get_skill_categories(
    current_user: User = Depends(get_required_user)
):
    """
    获取技能分类列表
    
    Returns:
        技能分类信息
    """
    categories = mcp_service.get_skill_categories()
    
    return {
        "success": True,
        "data": {
            "categories": categories,
            "total": len(categories)
        }
    }


@mcp_router.get("/skills/list")
async def get_skills_list(
    category: Optional[str] = Query(None, description="技能分类"),
    server: Optional[str] = Query(None, description="服务器名称"),
    current_user: User = Depends(get_required_user)
):
    """
    获取技能列表
    
    Args:
        category: 技能分类，可选
        server: 服务器名称，可选
        
    Returns:
        技能列表
    """
    skills = mcp_service.get_skills(category=category, server_name=server)
    
    return {
        "success": True,
        "data": {
            "skills": skills,
            "total": len(skills),
            "category": category,
            "server": server
        }
    }


@mcp_router.get("/skills/search")
async def search_skills(
    keyword: str = Query(..., description="搜索关键词"),
    current_user: User = Depends(get_required_user)
):
    """
    搜索技能
    
    Args:
        keyword: 搜索关键词
        
    Returns:
        匹配的技能列表
    """
    skills = mcp_service.search_skills(keyword)
    
    return {
        "success": True,
        "data": {
            "skills": skills,
            "total": len(skills),
            "keyword": keyword
        }
    }


@mcp_router.get("/skills/{skill_id}")
async def get_skill_detail(
    skill_id: str,
    current_user: User = Depends(get_required_user)
):
    """
    获取指定技能的详细信息
    
    Args:
        skill_id: 技能ID（格式：skill_工具名）
        
    Returns:
        技能详细信息
    """
    if not skill_id.startswith("skill_"):
        raise HTTPException(status_code=400, detail="无效的技能ID格式")
    
    tool_name = skill_id[6:]  # 移除"skill_"前缀
    skill = mcp_service.get_skill_by_id(skill_id, tool_name)
    
    if not skill:
        raise HTTPException(status_code=404, detail=f"找不到技能 '{skill_id}'")
    
    return {
        "success": True,
        "data": skill
    }


@mcp_router.post("/skills/{skill_id}/test")
async def test_skill(
    skill_id: str,
    test_params: Dict[str, Any] = Body(..., description="测试参数"),
    current_user: User = Depends(get_required_user)
):
    """
    测试技能功能
    
    Args:
        skill_id: 技能ID
        test_params: 测试参数
        
    Returns:
        测试结果
    """
    if not skill_id.startswith("skill_"):
        raise HTTPException(status_code=400, detail="无效的技能ID格式")
    
    tool_name = skill_id[6:]  # 移除"skill_"前缀
    test_result = mcp_service.test_skill(skill_id, tool_name, test_params, current_user.username)
    
    return {
        "success": True,
        "data": test_result
    }


@mcp_router.get("/skills/stats")
async def get_skills_stats(
    current_user: User = Depends(get_required_user)
):
    """
    获取技能统计信息
    
    Returns:
        技能统计信息
    """
    stats = mcp_service.get_skills_stats()
    
    return {
        "success": True,
        "data": stats
    } 

@mcp_router.get("/mcp/categories")
async def get_mcp_categories(
    current_user: User = Depends(get_admin_user)
):
    """
    获取所有MCP分类
    
    Returns:
        分类列表
    """
    categories = mcp_service.get_all_categories()
    
    return {
        "success": True,
        "data": categories
    } 