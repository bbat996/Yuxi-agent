"""
MCP工具管理路由
提供MCP工具的查询、分类、搜索等功能，以及技能管理功能
"""

import traceback
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query, HTTPException, Depends, Body
from utils.auth_middleware import get_admin_user, get_required_user
from models.user_model import User

from src.mcp_server.tools_config import (
    get_tool_categories,
    get_tool_details,
    get_tools_by_category,
    get_all_tools,
    get_tool_info,
    search_tools,
    get_servers,
    get_enabled_servers,
    get_server_config,
    get_server_tools
)
from src.mcp_server.mcp_config_manager import get_mcp_config_manager
from src.utils.logging_config import logger

mcp_router = APIRouter()

# =============================================================================
# MCP工具相关接口
# =============================================================================

@mcp_router.get("/mcp/tools/categories")
async def get_mcp_tool_categories(
    current_user: User = Depends(get_admin_user)
):
    """
    获取MCP工具分类列表
    
    Returns:
        工具分类信息
    """
    try:
        categories = get_tool_categories()
        return {
            "success": True,
            "data": categories
        }
    except Exception as e:
        logger.error(f"获取MCP工具分类失败: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取MCP工具分类失败: {str(e)}")


@mcp_router.get("/mcp/tools/list")
async def get_mcp_tools_list(
    category: Optional[str] = Query(None, description="工具分类（服务器名称）"),
    server: Optional[str] = Query(None, description="服务器名称"),
    current_user: User = Depends(get_admin_user)
):
    """
    获取MCP工具列表
    
    Args:
        category: 工具分类（服务器名称），可选
        server: 服务器名称，可选
        
    Returns:
        工具列表
    """
    try:
        if category:
            tools = get_tools_by_category(category)
        elif server:
            tools = get_server_tools(server)
        else:
            tools = get_all_tools()
        
        # 获取工具的详细信息
        tools_info = []
        for tool_name in tools:
            tool_info = get_tool_info(tool_name)
            if tool_info:
                tools_info.append({
                    "name": tool_name,
                    **tool_info
                })
        
        return {
            "success": True,
            "data": {
                "tools": tools_info,
                "total": len(tools_info),
                "category": category,
                "server": server
            }
        }
    except Exception as e:
        logger.error(f"获取MCP工具列表失败: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取MCP工具列表失败: {str(e)}")


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
    try:
        matching_tools = search_tools(keyword)
        
        # 获取工具的详细信息
        tools_info = []
        for tool_name in matching_tools:
            tool_info = get_tool_info(tool_name)
            if tool_info:
                tools_info.append({
                    "name": tool_name,
                    **tool_info
                })
        
        return {
            "success": True,
            "data": {
                "tools": tools_info,
                "total": len(tools_info),
                "keyword": keyword
            }
        }
    except Exception as e:
        logger.error(f"搜索MCP工具失败: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"搜索MCP工具失败: {str(e)}")


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
    try:
        tool_info = get_tool_info(tool_name)
        if not tool_info:
            raise HTTPException(status_code=404, detail=f"找不到工具 '{tool_name}'")
        
        return {
            "success": True,
            "data": {
                "name": tool_name,
                **tool_info
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取MCP工具详情失败: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取MCP工具详情失败: {str(e)}")


@mcp_router.get("/mcp/tools/overview")
async def get_mcp_tools_overview(
    current_user: User = Depends(get_admin_user)
):
    """
    获取MCP工具概览信息
    
    Returns:
        工具概览信息
    """
    try:
        config_manager = get_mcp_config_manager()
        summary = config_manager.get_config_summary()
        
        return {
            "success": True,
            "data": summary
        }
    except Exception as e:
        logger.error(f"获取MCP工具概览失败: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取MCP工具概览失败: {str(e)}")


@mcp_router.get("/mcp/tools/category/{category_name}")
async def get_mcp_tools_by_category(
    category_name: str,
    current_user: User = Depends(get_admin_user)
):
    """
    获取指定分类的MCP工具列表
    
    Args:
        category_name: 分类名称（服务器名称）
        
    Returns:
        该分类下的工具列表
    """
    try:
        categories = get_tool_categories()
        if category_name not in categories:
            raise HTTPException(status_code=404, detail=f"找不到分类 '{category_name}'")
        
        category_info = categories[category_name]
        tools = category_info["tools"]
        
        # 获取工具的详细信息
        tools_info = []
        for tool_name in tools:
            tool_info = get_tool_info(tool_name)
            if tool_info:
                tools_info.append({
                    "name": tool_name,
                    **tool_info
                })
        
        return {
            "success": True,
            "data": {
                "category": category_name,
                "description": category_info["description"],
                "tools": tools_info,
                "total": len(tools_info)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分类工具列表失败: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取分类工具列表失败: {str(e)}")


@mcp_router.get("/mcp/tools/random")
async def get_random_mcp_tools(
    count: int = Query(5, description="返回的工具数量", ge=1, le=20),
    category: Optional[str] = Query(None, description="限制在指定分类内"),
    current_user: User = Depends(get_admin_user)
):
    """
    获取随机的MCP工具列表（用于展示或测试）
    
    Args:
        count: 返回的工具数量
        category: 限制在指定分类内，可选
        
    Returns:
        随机工具列表
    """
    try:
        import random
        
        if category:
            tools = get_tools_by_category(category)
        else:
            tools = get_all_tools()
        
        if not tools:
            raise HTTPException(status_code=404, detail="没有可用的工具")
        
        # 随机选择工具
        selected_tools = random.sample(tools, min(count, len(tools)))
        
        # 获取工具的详细信息
        tools_info = []
        for tool_name in selected_tools:
            tool_info = get_tool_info(tool_name)
            if tool_info:
                tools_info.append({
                    "name": tool_name,
                    **tool_info
                })
        
        return {
            "success": True,
            "data": {
                "tools": tools_info,
                "total": len(tools_info),
                "category": category,
                "requested_count": count
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取随机MCP工具失败: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取随机MCP工具失败: {str(e)}")


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
    try:
        config_manager = get_mcp_config_manager()
        summary = config_manager.get_config_summary()
        
        return {
            "success": True,
            "data": summary
        }
    except Exception as e:
        logger.error(f"获取MCP配置摘要失败: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取MCP配置摘要失败: {str(e)}")


@mcp_router.get("/mcp/config/servers")
async def get_mcp_servers(
    enabled_only: bool = Query(False, description="是否只返回已启用的服务器"),
    current_user: User = Depends(get_admin_user)
):
    """
    获取MCP服务器列表
    
    Args:
        enabled_only: 是否只返回已启用的服务器
        
    Returns:
        MCP服务器列表
    """
    try:
        if enabled_only:
            server_names = get_enabled_servers()
            servers = {}
            for server_name in server_names:
                server_config = get_server_config(server_name)
                if server_config:
                    servers[server_name] = server_config
        else:
            servers = get_servers()
        
        return {
            "success": True,
            "data": {
                "servers": servers,
                "total": len(servers),
                "enabled_only": enabled_only
            }
        }
    except Exception as e:
        logger.error(f"获取MCP服务器列表失败: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取MCP服务器列表失败: {str(e)}")


@mcp_router.get("/mcp/config/servers/{server_name}")
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
    try:
        server_config = get_server_config(server_name)
        
        if not server_config:
            raise HTTPException(status_code=404, detail=f"找不到服务器 '{server_name}'")
        
        # 获取服务器的工具信息
        tools = get_server_tools(server_name)
        tools_info = []
        for tool_name in tools:
            tool_info = get_tool_info(tool_name)
            if tool_info:
                tools_info.append(tool_info)
        
        return {
            "success": True,
            "data": {
                "name": server_name,
                **server_config,
                "tools": tools_info,
                "tool_count": len(tools_info)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取MCP服务器详情失败: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取MCP服务器详情失败: {str(e)}")


@mcp_router.post("/mcp/config/reload")
async def reload_mcp_configuration(
    current_user: User = Depends(get_admin_user)
):
    """
    重新加载MCP配置
    
    Returns:
        重新加载结果
    """
    try:
        config_manager = get_mcp_config_manager()
        config_manager.reload_config()
        
        # 验证配置
        errors = config_manager.validate_config()
        
        return {
            "success": True,
            "data": {
                "message": "MCP配置重新加载成功",
                "config_valid": len(errors) == 0,
                "errors": errors
            }
        }
    except Exception as e:
        logger.error(f"重新加载MCP配置失败: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"重新加载MCP配置失败: {str(e)}")


@mcp_router.get("/mcp/config/validate")
async def validate_mcp_configuration(
    current_user: User = Depends(get_admin_user)
):
    """
    验证MCP配置
    
    Returns:
        配置验证结果
    """
    try:
        config_manager = get_mcp_config_manager()
        errors = config_manager.validate_config()
        
        return {
            "success": True,
            "data": {
                "valid": len(errors) == 0,
                "errors": errors,
                "error_count": len(errors)
            }
        }
    except Exception as e:
        logger.error(f"验证MCP配置失败: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"验证MCP配置失败: {str(e)}")


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
    try:
        categories = get_tool_categories()
        
        # 转换为技能分类格式
        skill_categories = []
        for category_name, category_info in categories.items():
            skill_categories.append({
                "name": category_name,
                "description": category_info.get("description", ""),
                "tool_count": len(category_info.get("tools", [])),
                "servers": category_info.get("servers", [])
            })
        
        return {
            "success": True,
            "data": {
                "categories": skill_categories,
                "total": len(skill_categories)
            }
        }
    except Exception as e:
        logger.error(f"获取技能分类失败: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取技能分类失败: {str(e)}")


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
    try:
        if category:
            # 按分类获取工具
            tools = get_tools_by_category(category)
        elif server:
            # 按服务器获取工具
            tools = get_server_tools(server)
        else:
            # 获取所有工具
            tools = get_all_tools()
        
        # 获取工具的详细信息
        skills_info = []
        for tool_name in tools:
            tool_info = get_tool_info(tool_name)
            if tool_info:
                skills_info.append({
                    "skill_id": f"skill_{tool_name}",
                    "name": tool_info.get("name", tool_name),
                    "description": tool_info.get("description", ""),
                    "category": tool_info.get("server", ""),  # 使用服务器名称作为分类
                    "server": tool_info.get("server", ""),
                    "parameters": tool_info.get("parameters", {}),
                    "return_type": "string",  # 新配置格式中默认为string
                    "is_active": True,
                    "is_verified": True,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                })
        
        return {
            "success": True,
            "data": {
                "skills": skills_info,
                "total": len(skills_info),
                "category": category,
                "server": server
            }
        }
    except Exception as e:
        logger.error(f"获取技能列表失败: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取技能列表失败: {str(e)}")


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
    try:
        matching_tools = search_tools(keyword)
        
        # 获取工具的详细信息
        skills_info = []
        for tool_name in matching_tools:
            tool_info = get_tool_info(tool_name)
            if tool_info:
                skills_info.append({
                    "skill_id": f"skill_{tool_name}",
                    "name": tool_info.get("name", tool_name),
                    "description": tool_info.get("description", ""),
                    "category": tool_info.get("server", ""),  # 使用服务器名称作为分类
                    "server": tool_info.get("server", ""),
                    "parameters": tool_info.get("parameters", {}),
                    "return_type": "string",  # 新配置格式中默认为string
                    "is_active": True,
                    "is_verified": True,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                })
        
        return {
            "success": True,
            "data": {
                "skills": skills_info,
                "total": len(skills_info),
                "keyword": keyword
            }
        }
    except Exception as e:
        logger.error(f"搜索技能失败: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"搜索技能失败: {str(e)}")


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
    try:
        # 从skill_id中提取工具名
        if not skill_id.startswith("skill_"):
            raise HTTPException(status_code=400, detail="无效的技能ID格式")
        
        tool_name = skill_id[6:]  # 移除"skill_"前缀
        tool_info = get_tool_info(tool_name)
        
        if not tool_info:
            raise HTTPException(status_code=404, detail=f"找不到技能 '{skill_id}'")
        
        return {
            "success": True,
            "data": {
                "skill_id": skill_id,
                "name": tool_info.get("name", tool_name),
                "description": tool_info.get("description", ""),
                "category": tool_info.get("server", ""),  # 使用服务器名称作为分类
                "server": tool_info.get("server", ""),
                "parameters": tool_info.get("parameters", {}),
                "return_type": "string",  # 新配置格式中默认为string
                "is_active": True,
                "is_verified": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取技能详情失败: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取技能详情失败: {str(e)}")


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
    try:
        # 从skill_id中提取工具名
        if not skill_id.startswith("skill_"):
            raise HTTPException(status_code=400, detail="无效的技能ID格式")
        
        tool_name = skill_id[6:]  # 移除"skill_"前缀
        tool_info = get_tool_info(tool_name)
        
        if not tool_info:
            raise HTTPException(status_code=404, detail=f"找不到技能 '{skill_id}'")
        
        # TODO: 实现实际的技能测试逻辑
        # 这里应该调用对应的MCP工具进行测试
        
        test_result = {
            "success": True,
            "skill_id": skill_id,
            "tool_name": tool_name,
            "test_params": test_params,
            "result": "测试成功（模拟结果）",
            "execution_time": 150,  # ms
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        logger.info(f"用户 {current_user.username} 测试了技能: {tool_name}")
        
        return {
            "success": True,
            "data": test_result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试技能失败: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"测试技能失败: {str(e)}")


@mcp_router.get("/skills/stats")
async def get_skills_stats(
    current_user: User = Depends(get_required_user)
):
    """
    获取技能统计信息
    
    Returns:
        技能统计信息
    """
    try:
        config_manager = get_mcp_config_manager()
        categories = config_manager.get_tool_categories()
        all_tools = config_manager.get_all_tools()
        
        # 统计每个分类的技能数量
        category_stats = {}
        for category_name, category_info in categories.items():
            category_stats[category_name] = {
                "description": category_info.get("description", ""),
                "skill_count": len(category_info.get("tools", []))
            }
        
        # 统计每个服务器的技能数量
        server_stats = {}
        for server_name in config_manager.get_enabled_servers():
            tools = config_manager.get_enabled_tools(server_name)
            server_stats[server_name] = len(tools)
        
        return {
            "success": True,
            "data": {
                "total_skills": len(all_tools),
                "total_categories": len(categories),
                "total_servers": len(config_manager.get_enabled_servers()),
                "categories": category_stats,
                "servers": server_stats
            }
        }
    except Exception as e:
        logger.error(f"获取技能统计失败: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取技能统计失败: {str(e)}") 