from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, and_, or_
from typing import List, Optional, Dict, Any
import uuid
import json
from datetime import datetime
from pydantic import BaseModel, Field

from server.db_manager import DBManager
from server.models.agent_models import CustomAgent, AgentInstance, AgentShare
from server.models.user_model import User
from server.utils.auth_middleware import get_required_user, get_admin_user
from server.src.utils import logger

# 创建路由器
agent_router = APIRouter(prefix="/agents", tags=["agents"])
db_manager = DBManager()


# Pydantic模型用于API参数验证
class AgentCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    agent_type: str = Field(default="custom")
    avatar: Optional[str] = None
    system_prompt: Optional[str] = None
    model_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    tools_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    knowledge_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    tags: Optional[List[str]] = Field(default_factory=list)
    is_public: bool = Field(default=False)

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "客服助手",
                "description": "专业的客服智能体",
                "agent_type": "custom",
                "avatar": "https://example.com/avatar.png",
                "system_prompt": "你是一个专业的客服助手...",
                "model_config": {"provider": "zhipu", "model_name": "glm-4-plus"},
                "tools_config": {"builtin_tools": ["web_search"]},
                "knowledge_config": {"databases": ["kb_1"]},
                "tags": ["客服", "售后"],
                "is_public": False,
            }
        }
    }


class AgentUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    agent_type: Optional[str] = None
    avatar: Optional[str] = None
    system_prompt: Optional[str] = None
    model_config: Optional[Dict[str, Any]] = None
    tools_config: Optional[Dict[str, Any]] = None
    knowledge_config: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "更新后的客服助手",
                "description": "更新后的专业客服智能体",
                "agent_type": "custom",
                "avatar": "https://example.com/new_avatar.png",
                "system_prompt": "你是一个更专业的客服助手...",
                "model_config": {"provider": "zhipu", "model_name": "glm-4-plus"},
                "tools_config": {"builtin_tools": ["web_search", "calculator"]},
                "knowledge_config": {"databases": ["kb_1", "kb_2"]},
                "tags": ["客服", "售后", "技术支持"],
                "is_public": True,
            }
        }
    }


class AgentConfigOverride(BaseModel):
    model_config: Optional[Dict[str, Any]] = None
    tools_config: Optional[Dict[str, Any]] = None
    knowledge_config: Optional[Dict[str, Any]] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "model_config": {"temperature": 0.7},
                "tools_config": {"web_search": {"top_k": 3}},
                "knowledge_config": {"retrieval_params": {"top_k": 5}},
            }
        }
    }


@agent_router.post("/", summary="创建智能体")
async def create_agent(request: AgentCreateRequest, current_user: User = Depends(get_required_user)):
    """创建新的自定义智能体"""
    try:
        with db_manager.get_session_context() as session:
            # 检查名称是否重复（同一用户）
            existing_agent = (
                session.query(CustomAgent)
                .filter(and_(CustomAgent.name == request.name, CustomAgent.created_by == current_user.id, CustomAgent.deleted_at.is_(None)))
                .first()
            )

            if existing_agent:
                raise HTTPException(status_code=400, detail="智能体名称已存在")

            # 创建智能体
            agent = CustomAgent(
                agent_id=str(uuid.uuid4()),
                name=request.name,
                description=request.description,
                agent_type=request.agent_type,
                avatar=request.avatar,
                system_prompt=request.system_prompt,
                model_config=request.model_config,
                tools_config=request.tools_config,
                knowledge_config=request.knowledge_config,
                tags=request.tags,
                is_public=request.is_public,
                created_by=current_user.id,
            )

            session.add(agent)
            session.flush()  # 获取生成的ID

            logger.info(f"用户 {current_user.username} 创建了智能体: {agent.name}")

            return {"success": True, "message": "智能体创建成功", "data": agent.to_dict()}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建智能体失败: {e}")
        raise HTTPException(status_code=500, detail="创建智能体失败")


@agent_router.get("/", summary="获取智能体列表")
async def get_agents(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    category: Optional[str] = Query(None, description="分类筛选"),
    agent_type: Optional[str] = Query(None, description="类型筛选"),
    only_mine: bool = Query(False, description="只显示我的智能体"),
    only_public: bool = Query(False, description="只显示公开智能体"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    current_user: User = Depends(get_required_user),
):
    """获取智能体列表，支持分页、搜索、筛选和排序"""
    try:
        with db_manager.get_session_context() as session:
            # 构建查询
            query = session.query(CustomAgent).filter(CustomAgent.deleted_at.is_(None))

            # 权限过滤
            if only_mine:
                query = query.filter(CustomAgent.created_by == current_user.id)
            elif only_public:
                query = query.filter(CustomAgent.is_public == True)
            else:
                # 显示用户自己的和公开的智能体
                query = query.filter(or_(CustomAgent.created_by == current_user.id, CustomAgent.is_public == True))

            # 搜索过滤
            if search:
                search_pattern = f"%{search}%"
                query = query.filter(or_(CustomAgent.name.like(search_pattern), CustomAgent.description.like(search_pattern)))

            # 类型过滤
            if agent_type:
                query = query.filter(CustomAgent.agent_type == agent_type)

            # 标签过滤（如果category实际是标签）
            if category:
                query = query.filter(CustomAgent.tags.contains([category]))

            # 排序
            if sort_order.lower() == "desc":
                sort_func = desc
            else:
                sort_func = asc

            if hasattr(CustomAgent, sort_by):
                query = query.order_by(sort_func(getattr(CustomAgent, sort_by)))
            else:
                query = query.order_by(desc(CustomAgent.created_at))

            # 分页
            total = query.count()
            offset = (page - 1) * page_size
            agents = query.offset(offset).limit(page_size).all()

            # 转换为字典并添加实例信息
            agent_list = []
            for agent in agents:
                agent_dict = agent.to_dict(include_config=False)

                # 获取用户的实例信息（如果存在）
                instance = (
                    session.query(AgentInstance)
                    .filter(and_(AgentInstance.agent_id == agent.agent_id, AgentInstance.user_id == current_user.id))
                    .first()
                )

                if instance:
                    agent_dict["instance"] = instance.to_dict()
                else:
                    agent_dict["instance"] = None

                agent_list.append(agent_dict)

            return {
                "success": True,
                "data": {
                    "agents": agent_list,
                    "pagination": {"page": page, "page_size": page_size, "total": total, "total_pages": (total + page_size - 1) // page_size},
                },
            }

    except Exception as e:
        logger.error(f"获取智能体列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取智能体列表失败")


@agent_router.get("/{agent_id}", summary="获取智能体详情")
async def get_agent(agent_id: str, current_user: User = Depends(get_required_user)):
    """获取单个智能体的详细信息"""
    try:
        with db_manager.get_session_context() as session:
            # 查询智能体
            agent = session.query(CustomAgent).filter(and_(CustomAgent.agent_id == agent_id, CustomAgent.deleted_at.is_(None))).first()

            if not agent:
                raise HTTPException(status_code=404, detail="智能体不存在")

            # 权限检查：只能查看自己的或公开的智能体
            if agent.created_by != current_user.id and not agent.is_public:
                raise HTTPException(status_code=403, detail="无权限访问此智能体")

            # 获取用户的实例信息
            instance = session.query(AgentInstance).filter(and_(AgentInstance.agent_id == agent_id, AgentInstance.user_id == current_user.id)).first()

            agent_dict = agent.to_dict()
            if instance:
                agent_dict["instance"] = instance.to_dict()
            else:
                agent_dict["instance"] = None

            return {"success": True, "data": agent_dict}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取智能体详情失败: {e}")
        raise HTTPException(status_code=500, detail="获取智能体详情失败")


@agent_router.put("/{agent_id}", summary="更新智能体")
async def update_agent(agent_id: str, request: AgentUpdateRequest, current_user: User = Depends(get_required_user)):
    """更新智能体信息"""
    try:
        with db_manager.get_session_context() as session:
            # 查询智能体
            agent = session.query(CustomAgent).filter(and_(CustomAgent.agent_id == agent_id, CustomAgent.deleted_at.is_(None))).first()

            if not agent:
                raise HTTPException(status_code=404, detail="智能体不存在")

            # 权限检查：只能修改自己的智能体
            if agent.created_by != current_user.id:
                raise HTTPException(status_code=403, detail="无权限修改此智能体")

            # 更新字段
            update_data = request.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(agent, field):
                    setattr(agent, field, value)

            agent.updated_at = datetime.utcnow()

            logger.info(f"用户 {current_user.username} 更新了智能体: {agent.name}")

            return {"success": True, "message": "智能体更新成功", "data": agent.to_dict()}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新智能体失败: {e}")
        raise HTTPException(status_code=500, detail="更新智能体失败")


@agent_router.delete("/{agent_id}", summary="删除智能体")
async def delete_agent(agent_id: str, current_user: User = Depends(get_required_user)):
    """删除智能体（软删除）"""
    try:
        with db_manager.get_session_context() as session:
            # 查询智能体
            agent = session.query(CustomAgent).filter(and_(CustomAgent.agent_id == agent_id, CustomAgent.deleted_at.is_(None))).first()

            if not agent:
                raise HTTPException(status_code=404, detail="智能体不存在")

            # 权限检查：只能删除自己的智能体
            if agent.created_by != current_user.id:
                raise HTTPException(status_code=403, detail="无权限删除此智能体")

            # 软删除
            agent.deleted_at = datetime.utcnow()
            agent.is_active = False

            logger.info(f"用户 {current_user.username} 删除了智能体: {agent.name}")

            return {"success": True, "message": "智能体删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除智能体失败: {e}")
        raise HTTPException(status_code=500, detail="删除智能体失败")


@agent_router.post("/{agent_id}/duplicate", summary="复制智能体")
async def duplicate_agent(
    agent_id: str, new_name: Optional[str] = Body(None, description="新智能体名称"), current_user: User = Depends(get_required_user)
):
    """复制现有智能体创建新的智能体"""
    try:
        with db_manager.get_session_context() as session:
            # 查询原智能体
            original_agent = session.query(CustomAgent).filter(and_(CustomAgent.agent_id == agent_id, CustomAgent.deleted_at.is_(None))).first()

            if not original_agent:
                raise HTTPException(status_code=404, detail="智能体不存在")

            # 权限检查：只能复制自己的或公开的智能体
            if original_agent.created_by != current_user.id and not original_agent.is_public:
                raise HTTPException(status_code=403, detail="无权限复制此智能体")

            # 生成新名称
            if not new_name:
                new_name = f"{original_agent.name} - 副本"

            # 检查新名称是否重复
            existing_agent = (
                session.query(CustomAgent)
                .filter(and_(CustomAgent.name == new_name, CustomAgent.created_by == current_user.id, CustomAgent.deleted_at.is_(None)))
                .first()
            )

            if existing_agent:
                # 添加序号
                counter = 1
                while existing_agent:
                    test_name = f"{new_name} ({counter})"
                    existing_agent = (
                        session.query(CustomAgent)
                        .filter(and_(CustomAgent.name == test_name, CustomAgent.created_by == current_user.id, CustomAgent.deleted_at.is_(None)))
                        .first()
                    )
                    counter += 1
                new_name = f"{new_name} ({counter - 1})"

            # 创建新智能体
            new_agent = CustomAgent(
                agent_id=str(uuid.uuid4()),
                name=new_name,
                description=original_agent.description,
                agent_type=original_agent.agent_type,
                avatar=original_agent.avatar,
                system_prompt=original_agent.system_prompt,
                model_config=original_agent.model_config,
                tools_config=original_agent.tools_config,
                knowledge_config=original_agent.knowledge_config,
                tags=original_agent.tags,
                is_public=False,  # 复制的智能体默认为私有
                created_by=current_user.id,
            )

            session.add(new_agent)
            session.flush()

            logger.info(f"用户 {current_user.username} 复制了智能体: {original_agent.name} -> {new_name}")

            return {"success": True, "message": "智能体复制成功", "data": new_agent.to_dict()}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"复制智能体失败: {e}")
        raise HTTPException(status_code=500, detail="复制智能体失败")


@agent_router.post("/{agent_id}/instance", summary="创建智能体实例")
async def create_agent_instance(agent_id: str, config_override: AgentConfigOverride = Body(...), current_user: User = Depends(get_required_user)):
    """为用户创建智能体实例"""
    try:
        with db_manager.get_session_context() as session:
            # 检查智能体是否存在
            agent = (
                session.query(CustomAgent)
                .filter(and_(CustomAgent.agent_id == agent_id, CustomAgent.deleted_at.is_(None), CustomAgent.is_active == True))
                .first()
            )

            if not agent:
                raise HTTPException(status_code=404, detail="智能体不存在或已停用")

            # 权限检查
            if agent.created_by != current_user.id and not agent.is_public:
                raise HTTPException(status_code=403, detail="无权限使用此智能体")

            # 检查是否已有实例
            existing_instance = (
                session.query(AgentInstance).filter(and_(AgentInstance.agent_id == agent_id, AgentInstance.user_id == current_user.id)).first()
            )

            if existing_instance:
                # 更新现有实例
                existing_instance.config_override = config_override.model_dump(exclude_unset=True)
                existing_instance.last_used = datetime.utcnow()
                existing_instance.updated_at = datetime.utcnow()

                return {"success": True, "message": "智能体实例更新成功", "data": existing_instance.to_dict()}
            else:
                # 创建新实例
                instance = AgentInstance(
                    instance_id=str(uuid.uuid4()),
                    agent_id=agent_id,
                    user_id=current_user.id,
                    config_override=config_override.model_dump(exclude_unset=True),
                    last_used=datetime.utcnow(),
                )

                session.add(instance)
                session.flush()

                return {"success": True, "message": "智能体实例创建成功", "data": instance.to_dict()}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建智能体实例失败: {e}")
        raise HTTPException(status_code=500, detail="创建智能体实例失败")


@agent_router.get("/{agent_id}/instance", summary="获取用户的智能体实例")
async def get_agent_instance(agent_id: str, current_user: User = Depends(get_required_user)):
    """获取用户的智能体实例信息"""
    try:
        with db_manager.get_session_context() as session:
            instance = session.query(AgentInstance).filter(and_(AgentInstance.agent_id == agent_id, AgentInstance.user_id == current_user.id)).first()

            if not instance:
                raise HTTPException(status_code=404, detail="智能体实例不存在")

            return {"success": True, "data": instance.to_dict()}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取智能体实例失败: {e}")
        raise HTTPException(status_code=500, detail="获取智能体实例失败")


@agent_router.delete("/{agent_id}/instance", summary="删除智能体实例")
async def delete_agent_instance(agent_id: str, current_user: User = Depends(get_required_user)):
    """删除用户的智能体实例"""
    try:
        with db_manager.get_session_context() as session:
            instance = session.query(AgentInstance).filter(and_(AgentInstance.agent_id == agent_id, AgentInstance.user_id == current_user.id)).first()

            if not instance:
                raise HTTPException(status_code=404, detail="智能体实例不存在")

            session.delete(instance)

            return {"success": True, "message": "智能体实例删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除智能体实例失败: {e}")
        raise HTTPException(status_code=500, detail="删除智能体实例失败")
