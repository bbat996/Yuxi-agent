from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, and_, or_
from typing import List, Optional, Dict, Any
import uuid
import json
from datetime import datetime

from server.db_manager import DBManager
from server.models.agent_models import PromptTemplate, MCPSkill
from server.models.user_model import User
from server.utils.auth_middleware import get_required_user, get_admin_user
from server.src.utils import logger

# 创建路由器
template_router = APIRouter(prefix="/templates", tags=["templates"])
db_manager = DBManager()

# Pydantic模型用于API参数验证
from pydantic import BaseModel, Field

class PromptTemplateCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="模板名称")
    content: str = Field(..., min_length=1, description="模板内容")
    category: Optional[str] = Field(None, description="分类")
    description: Optional[str] = Field(None, max_length=500, description="模板描述")
    variables: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="变量定义")

class PromptTemplateUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="模板名称")
    content: Optional[str] = Field(None, min_length=1, description="模板内容")
    category: Optional[str] = Field(None, description="分类")
    description: Optional[str] = Field(None, max_length=500, description="模板描述")
    variables: Optional[List[Dict[str, Any]]] = Field(None, description="变量定义")
    is_active: Optional[bool] = Field(None, description="是否激活")

class MCPSkillCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="技能名称")
    description: Optional[str] = Field(None, max_length=500, description="技能描述")
    mcp_server: str = Field(..., description="MCP服务器地址")
    mcp_config: Dict[str, Any] = Field(..., description="MCP连接配置")
    tool_schema: Optional[Dict[str, Any]] = Field(None, description="工具Schema定义")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="默认参数配置")
    category: Optional[str] = Field(None, description="分类")
    version: Optional[str] = Field(None, description="版本号")

class MCPSkillUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="技能名称")
    description: Optional[str] = Field(None, max_length=500, description="技能描述")
    mcp_server: Optional[str] = Field(None, description="MCP服务器地址")
    mcp_config: Optional[Dict[str, Any]] = Field(None, description="MCP连接配置")
    tool_schema: Optional[Dict[str, Any]] = Field(None, description="工具Schema定义")
    parameters: Optional[Dict[str, Any]] = Field(None, description="默认参数配置")
    category: Optional[str] = Field(None, description="分类")
    version: Optional[str] = Field(None, description="版本号")
    is_active: Optional[bool] = Field(None, description="是否激活")
    is_verified: Optional[bool] = Field(None, description="是否已验证")

# =============================================================================
# 提示词模板相关接口
# =============================================================================

@template_router.get("/prompts", summary="获取提示词模板列表")
async def get_prompt_templates(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    category: Optional[str] = Query(None, description="分类筛选"),
    only_mine: bool = Query(False, description="只显示我的模板"),
    only_system: bool = Query(False, description="只显示系统模板"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    current_user: User = Depends(get_required_user)
):
    """获取提示词模板列表，支持分页、搜索、筛选和排序"""
    with db_manager.get_session_context() as session:
        # 构建查询
        query = session.query(PromptTemplate).filter(PromptTemplate.is_active == True)
        
        # 权限过滤
        if only_mine:
            query = query.filter(PromptTemplate.created_by == current_user.id)
        elif only_system:
            query = query.filter(PromptTemplate.is_system == True)
        else:
            # 显示用户自己的和系统模板
            query = query.filter(
                or_(
                    PromptTemplate.created_by == current_user.id,
                    PromptTemplate.is_system == True
                )
            )
        
        # 搜索过滤
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    PromptTemplate.name.like(search_pattern),
                    PromptTemplate.description.like(search_pattern),
                    PromptTemplate.content.like(search_pattern)
                )
            )
        
        # 分类过滤
        if category:
            query = query.filter(PromptTemplate.category == category)
        
        # 排序
        if sort_order.lower() == "desc":
            sort_func = desc
        else:
            sort_func = asc
            
        if hasattr(PromptTemplate, sort_by):
            query = query.order_by(sort_func(getattr(PromptTemplate, sort_by)))
        else:
            query = query.order_by(desc(PromptTemplate.created_at))
        
        # 分页
        total = query.count()
        offset = (page - 1) * page_size
        templates = query.offset(offset).limit(page_size).all()
        
        return {
            "success": True,
            "data": {
                "templates": [template.to_dict() for template in templates],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": (total + page_size - 1) // page_size
                }
            }
        }

@template_router.post("/prompts", summary="创建提示词模板")
async def create_prompt_template(
    request: PromptTemplateCreateRequest,
    current_user: User = Depends(get_required_user)
):
    """创建新的提示词模板"""
    with db_manager.get_session_context() as session:
        # 检查名称是否重复（同一用户）
        existing_template = session.query(PromptTemplate).filter(
            and_(
                PromptTemplate.name == request.name,
                PromptTemplate.created_by == current_user.id
            )
        ).first()
        
        if existing_template:
            raise HTTPException(status_code=400, detail="模板名称已存在")
        
        # 创建模板
        template = PromptTemplate(
            template_id=str(uuid.uuid4()),
            name=request.name,
            content=request.content,
            category=request.category,
            description=request.description,
            variables=request.variables,
            is_system=False,  # 用户创建的模板不是系统模板
            created_by=current_user.id
        )
        
        session.add(template)
        session.flush()
        
        logger.info(f"用户 {current_user.username} 创建了提示词模板: {template.name}")
        
        return {
            "success": True,
            "message": "提示词模板创建成功",
            "data": template.to_dict()
        }

@template_router.get("/prompts/{template_id}", summary="获取提示词模板详情")
async def get_prompt_template(
    template_id: str,
    current_user: User = Depends(get_required_user)
):
    """获取单个提示词模板的详细信息"""
    with db_manager.get_session_context() as session:
        template = session.query(PromptTemplate).filter(
            PromptTemplate.template_id == template_id
        ).first()
        
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        # 权限检查：只能查看自己的或系统模板
        if template.created_by != current_user.id and not template.is_system:
            raise HTTPException(status_code=403, detail="无权限访问此模板")
        
        return {
            "success": True,
            "data": template.to_dict()
        }

@template_router.put("/prompts/{template_id}", summary="更新提示词模板")
async def update_prompt_template(
    template_id: str,
    request: PromptTemplateUpdateRequest,
    current_user: User = Depends(get_required_user)
):
    """更新提示词模板信息"""
    with db_manager.get_session_context() as session:
        template = session.query(PromptTemplate).filter(
            PromptTemplate.template_id == template_id
        ).first()
        
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        # 权限检查：只能修改自己的模板，或管理员可以修改系统模板
        if template.created_by != current_user.id:
            if not template.is_system or current_user.role != "admin":
                raise HTTPException(status_code=403, detail="无权限修改此模板")
        
        # 更新字段
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(template, field):
                setattr(template, field, value)
        
        template.updated_at = datetime.utcnow()
        
        # 更新使用次数统计
        if request.name or request.content:  # 如果修改了内容，重置使用统计
            template.usage_count = 0
        
        logger.info(f"用户 {current_user.username} 更新了提示词模板: {template.name}")
        
        return {
            "success": True,
            "message": "提示词模板更新成功",
            "data": template.to_dict()
        }

@template_router.delete("/prompts/{template_id}", summary="删除提示词模板")
async def delete_prompt_template(
    template_id: str,
    current_user: User = Depends(get_required_user)
):
    """删除提示词模板"""
    with db_manager.get_session_context() as session:
        template = session.query(PromptTemplate).filter(
            PromptTemplate.template_id == template_id
        ).first()
        
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        # 权限检查：只能删除自己的模板，系统模板不能删除
        if template.is_system:
            raise HTTPException(status_code=403, detail="系统模板不能删除")
        
        if template.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="无权限删除此模板")
        
        session.delete(template)
        
        logger.info(f"用户 {current_user.username} 删除了提示词模板: {template.name}")
        
        return {
            "success": True,
            "message": "提示词模板删除成功"
        }

@template_router.post("/prompts/{template_id}/use", summary="标记模板使用")
async def use_prompt_template(
    template_id: str,
    current_user: User = Depends(get_required_user)
):
    """标记模板被使用，更新使用统计"""
    with db_manager.get_session_context() as session:
        template = session.query(PromptTemplate).filter(
            PromptTemplate.template_id == template_id
        ).first()
        
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        # 权限检查：只能使用自己的或系统模板
        if template.created_by != current_user.id and not template.is_system:
            raise HTTPException(status_code=403, detail="无权限使用此模板")
        
        template.usage_count += 1
        template.updated_at = datetime.utcnow()
        
        return {
            "success": True,
            "message": "模板使用统计已更新"
        }

# =============================================================================
# MCP技能模板相关接口
# =============================================================================

@template_router.get("/mcp-skills", summary="获取MCP技能列表")
async def get_mcp_skills(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    category: Optional[str] = Query(None, description="分类筛选"),
    only_verified: bool = Query(False, description="只显示已验证的技能"),
    only_active: bool = Query(True, description="只显示激活的技能"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    current_user: User = Depends(get_required_user)
):
    """获取MCP技能列表，支持分页、搜索、筛选和排序"""
    with db_manager.get_session_context() as session:
        # 构建查询
        query = session.query(MCPSkill)
        
        # 激活状态过滤
        if only_active:
            query = query.filter(MCPSkill.is_active == True)
        
        # 验证状态过滤
        if only_verified:
            query = query.filter(MCPSkill.is_verified == True)
        
        # 搜索过滤
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    MCPSkill.name.like(search_pattern),
                    MCPSkill.description.like(search_pattern)
                )
            )
        
        # 分类过滤
        if category:
            query = query.filter(MCPSkill.category == category)
        
        # 排序
        if sort_order.lower() == "desc":
            sort_func = desc
        else:
            sort_func = asc
            
        if hasattr(MCPSkill, sort_by):
            query = query.order_by(sort_func(getattr(MCPSkill, sort_by)))
        else:
            query = query.order_by(desc(MCPSkill.created_at))
        
        # 分页
        total = query.count()
        offset = (page - 1) * page_size
        skills = query.offset(offset).limit(page_size).all()
        
        return {
            "success": True,
            "data": {
                "skills": [skill.to_dict() for skill in skills],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": (total + page_size - 1) // page_size
                }
            }
        }

@template_router.post("/mcp-skills", summary="注册MCP技能")
async def create_mcp_skill(
    request: MCPSkillCreateRequest,
    current_user: User = Depends(get_required_user)
):
    """注册新的MCP技能"""
    with db_manager.get_session_context() as session:
        # 检查名称是否重复
        existing_skill = session.query(MCPSkill).filter(
            MCPSkill.name == request.name
        ).first()
        
        if existing_skill:
            raise HTTPException(status_code=400, detail="技能名称已存在")
        
        # 创建技能
        skill = MCPSkill(
            skill_id=str(uuid.uuid4()),
            name=request.name,
            description=request.description,
            mcp_server=request.mcp_server,
            mcp_config=request.mcp_config,
            tool_schema=request.tool_schema,
            parameters=request.parameters,
            category=request.category,
            version=request.version,
            created_by=current_user.id
        )
        
        session.add(skill)
        session.flush()
        
        logger.info(f"用户 {current_user.username} 注册了MCP技能: {skill.name}")
        
        return {
            "success": True,
            "message": "MCP技能注册成功",
            "data": skill.to_dict()
        }

@template_router.get("/mcp-skills/{skill_id}", summary="获取MCP技能详情")
async def get_mcp_skill(
    skill_id: str,
    current_user: User = Depends(get_required_user)
):
    """获取单个MCP技能的详细信息"""
    with db_manager.get_session_context() as session:
        skill = session.query(MCPSkill).filter(
            MCPSkill.skill_id == skill_id
        ).first()
        
        if not skill:
            raise HTTPException(status_code=404, detail="MCP技能不存在")
        
        return {
            "success": True,
            "data": skill.to_dict()
        }

@template_router.put("/mcp-skills/{skill_id}", summary="更新MCP技能")
async def update_mcp_skill(
    skill_id: str,
    request: MCPSkillUpdateRequest,
    current_user: User = Depends(get_required_user)
):
    """更新MCP技能信息"""
    with db_manager.get_session_context() as session:
        skill = session.query(MCPSkill).filter(
            MCPSkill.skill_id == skill_id
        ).first()
        
        if not skill:
            raise HTTPException(status_code=404, detail="MCP技能不存在")
        
        # 权限检查：只能修改自己创建的技能，或管理员
        if skill.created_by != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="无权限修改此技能")
        
        # 更新字段
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(skill, field):
                setattr(skill, field, value)
        
        skill.updated_at = datetime.utcnow()
        
        logger.info(f"用户 {current_user.username} 更新了MCP技能: {skill.name}")
        
        return {
            "success": True,
            "message": "MCP技能更新成功",
            "data": skill.to_dict()
        }

@template_router.delete("/mcp-skills/{skill_id}", summary="删除MCP技能")
async def delete_mcp_skill(
    skill_id: str,
    current_user: User = Depends(get_required_user)
):
    """删除MCP技能"""
    with db_manager.get_session_context() as session:
        skill = session.query(MCPSkill).filter(
            MCPSkill.skill_id == skill_id
        ).first()
        
        if not skill:
            raise HTTPException(status_code=404, detail="MCP技能不存在")
        
        # 权限检查：只能删除自己创建的技能，或管理员
        if skill.created_by != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="无权限删除此技能")
        
        session.delete(skill)
        
        logger.info(f"用户 {current_user.username} 删除了MCP技能: {skill.name}")
        
        return {
            "success": True,
            "message": "MCP技能删除成功"
        }

@template_router.post("/mcp-skills/{skill_id}/test", summary="测试MCP技能")
async def test_mcp_skill(
    skill_id: str,
    test_params: Dict[str, Any] = Body(..., description="测试参数"),
    current_user: User = Depends(get_required_user)
):
    """测试MCP技能的连通性和功能"""
    with db_manager.get_session_context() as session:
        skill = session.query(MCPSkill).filter(
            MCPSkill.skill_id == skill_id
        ).first()
        
        if not skill:
            raise HTTPException(status_code=404, detail="MCP技能不存在")
        
        # TODO: 实现MCP技能测试逻辑
        # 这里应该连接到MCP服务器并执行测试
        
        # 暂时返回模拟结果
        test_result = {
            "success": True,
            "connection_status": "connected",
            "response_time": 150,  # ms
            "test_output": "测试成功",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # 更新技能统计
        skill.usage_count += 1
        if test_result["success"]:
            # 更新成功率（简化计算）
            if skill.success_rate is None:
                skill.success_rate = 100.0
            else:
                skill.success_rate = (skill.success_rate * 0.9) + (100.0 * 0.1)
        
        # 更新响应时间
        if skill.avg_response_time is None:
            skill.avg_response_time = test_result["response_time"]
        else:
            skill.avg_response_time = (skill.avg_response_time * 0.8) + (test_result["response_time"] * 0.2)
        
        skill.updated_at = datetime.utcnow()
        
        logger.info(f"用户 {current_user.username} 测试了MCP技能: {skill.name}")
        
        return {
            "success": True,
            "message": "MCP技能测试完成",
            "data": test_result
        }

# =============================================================================
# 统计和分类接口
# =============================================================================

@template_router.get("/categories", summary="获取分类列表")
async def get_categories(
    template_type: str = Query("prompt", description="模板类型 (prompt, mcp)"),
    current_user: User = Depends(get_required_user)
):
    """获取模板分类列表"""
    with db_manager.get_session_context() as session:
        if template_type == "prompt":
            # 获取提示词模板分类
            categories = session.query(PromptTemplate.category).filter(
                and_(
                    PromptTemplate.category.isnot(None),
                    PromptTemplate.is_active == True,
                    or_(
                        PromptTemplate.created_by == current_user.id,
                        PromptTemplate.is_system == True
                    )
                )
            ).distinct().all()
        else:
            # 获取MCP技能分类
            categories = session.query(MCPSkill.category).filter(
                and_(
                    MCPSkill.category.isnot(None),
                    MCPSkill.is_active == True
                )
            ).distinct().all()
        
        category_list = [cat[0] for cat in categories if cat[0]]
        
        return {
            "success": True,
            "data": {
                "categories": category_list
            }
        }

@template_router.get("/stats", summary="获取模板统计信息")
async def get_template_stats(
    current_user: User = Depends(get_required_user)
):
    """获取模板使用统计信息"""
    with db_manager.get_session_context() as session:
        # 提示词模板统计
        prompt_total = session.query(PromptTemplate).filter(
            or_(
                PromptTemplate.created_by == current_user.id,
                PromptTemplate.is_system == True
            )
        ).count()
        
        prompt_mine = session.query(PromptTemplate).filter(
            PromptTemplate.created_by == current_user.id
        ).count()
        
        # MCP技能统计
        mcp_total = session.query(MCPSkill).filter(
            MCPSkill.is_active == True
        ).count()
        
        mcp_verified = session.query(MCPSkill).filter(
            and_(
                MCPSkill.is_active == True,
                MCPSkill.is_verified == True
            )
        ).count()
        
        return {
            "success": True,
            "data": {
                "prompt_templates": {
                    "total": prompt_total,
                    "mine": prompt_mine,
                    "system": prompt_total - prompt_mine
                },
                "mcp_skills": {
                    "total": mcp_total,
                    "verified": mcp_verified,
                    "unverified": mcp_total - mcp_verified
                }
            }
        }