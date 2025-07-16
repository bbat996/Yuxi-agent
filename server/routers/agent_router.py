from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy import desc, asc, and_, or_
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
from pydantic import BaseModel, Field

from db_manager import DBManager
from models.agent_models import CustomAgent, AgentInstance
from models.user_model import User
from utils.auth_middleware import get_required_user
from src.utils import logger

# 创建路由器
agent_router = APIRouter(prefix="/agents", tags=["agents"])
db_manager = DBManager()


class AgentCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="智能体名称")
    description: Optional[str] = Field(None, max_length=500, description="智能体描述")
    agent_type: str = Field(default="chatbot", description="智能体类型")
    avatar: Optional[str] = Field(None, description="头像URL")
    system_prompt: Optional[str] = Field(None, description="系统提示词")

    # 分开的模型配置
    provider: Optional[str] = Field(default="zhipu", description="模型提供商")
    model_name: Optional[str] = Field(default="glm-4-plus", description="模型名称")
    model_parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="模型参数")

    # 工具配置
    tools: Optional[List[str]] = Field(default_factory=list, description="内置工具列表")
    mcp_skills: Optional[List[str]] = Field(default_factory=list, description="MCP技能列表")

    # 知识库配置
    knowledge_databases: Optional[List[str]] = Field(default_factory=list, description="知识库ID列表")
    retrieval_params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="检索参数")

    tags: Optional[List[str]] = Field(default_factory=list, description="标签列表")
    is_public: bool = Field(default=False, description="是否公开")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "客服助手",
                "description": "专业的客服智能体",
                "agent_type": "chatbot",
                "avatar": "https://example.com/avatar.png",
                "system_prompt": "你是一个专业的客服助手...",
                "provider": "zhipu",
                "model_name": "glm-4-plus",
                "model_parameters": {"temperature": 0.7},
                "tools": ["web_search", "calculator"],
                "mcp_skills": {"file_manager": {"enabled": True}},
                "knowledge_databases": ["kb_1", "kb_2"],
                "retrieval_params": {"top_k": 5},
                "tags": ["客服", "售后"],
                "is_public": False,
            }
        }
    }


class AgentUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="智能体名称")
    description: Optional[str] = Field(None, max_length=500, description="智能体描述")
    agent_type: Optional[str] = Field(None, description="智能体类型")
    avatar: Optional[str] = Field(None, description="头像URL")
    system_prompt: Optional[str] = Field(None, description="系统提示词")

    # 分开的模型配置
    provider: Optional[str] = Field(None, description="模型提供商")
    model_name: Optional[str] = Field(None, description="模型名称")
    model_parameters: Optional[Dict[str, Any]] = Field(None, description="模型参数")

    # 工具配置
    tools: Optional[List[str]] = Field(None, description="内置工具列表")
    mcp_skills: Optional[List[str]] = Field(None, description="MCP技能列表")

    # 知识库配置
    knowledge_databases: Optional[List[str]] = Field(None, description="知识库ID列表")
    retrieval_params: Optional[Dict[str, Any]] = Field(None, description="检索参数")

    tags: Optional[List[str]] = Field(None, description="标签列表")
    is_public: Optional[bool] = Field(None, description="是否公开")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "更新后的客服助手",
                "description": "更新后的专业客服智能体",
                "agent_type": "chatbot",
                "avatar": "https://example.com/new_avatar.png",
                "system_prompt": "你是一个更专业的客服助手...",
                "provider": "zhipu",
                "model_name": "glm-4-plus",
                "model_parameters": {"temperature": 0.8},
                "tools": ["web_search", "calculator", "file_reader"],
                "mcp_skills": ["file_manager", "calendar"],
                "knowledge_databases": ["kb_1", "kb_2", "kb_3"],
                "retrieval_params": {"top_k": 10},
                "tags": ["客服", "售后", "技术支持"],
                "is_public": True,
            }
        }
    }


class AgentConfigOverride(BaseModel):
    """运行时配置覆盖"""

    provider: Optional[str] = Field(None, description="模型提供商")
    model_name: Optional[str] = Field(None, description="模型名称")
    model_parameters: Optional[Dict[str, Any]] = Field(None, description="模型参数")
    tools: Optional[List[str]] = Field(None, description="内置工具列表")
    mcp_skills: Optional[List[str]] = Field(None, description="MCP技能列表")
    knowledge_databases: Optional[List[str]] = Field(None, description="知识库ID列表")
    retrieval_params: Optional[Dict[str, Any]] = Field(None, description="检索参数")

    model_config = {
        "json_schema_extra": {
            "example": {
                "provider": "openai",
                "model_name": "gpt-4",
                "model_parameters": {"temperature": 0.7},
                "tools": ["web_search"],
                "mcp_skills": ["file_manager"],
                "knowledge_databases": ["kb_1"],
                "retrieval_params": {"top_k": 3},
            }
        }
    }


def _build_model_config(provider: str = None, model_name: str = None, model_parameters: Dict[str, Any] = None) -> Dict[str, Any]:
    """构建模型配置字典"""
    config = {}
    if provider:
        config["provider"] = provider
    if model_name:
        config["model_name"] = model_name
    if model_parameters:
        config["parameters"] = model_parameters
    return config


def _build_tools_config(tools: List[str] = None, mcp_skills: List[str] = None) -> Dict[str, Any]:
    """构建工具配置字典"""
    config = {}
    if tools is not None:
        config["builtin_tools"] = tools
    if mcp_skills is not None:
        config["mcp_skills"] = mcp_skills
    return config


def _build_knowledge_config(knowledge_databases: List[str] = None, retrieval_params: Dict[str, Any] = None) -> Dict[str, Any]:
    """构建知识库配置字典"""
    config = {}
    if knowledge_databases is not None:
        config["databases"] = knowledge_databases
    if retrieval_params is not None:
        config["retrieval_params"] = retrieval_params
    return config


@agent_router.get("", summary="获取智能体列表")
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
                session.query(AgentInstance).filter(and_(AgentInstance.agent_id == agent.agent_id, AgentInstance.user_id == current_user.id)).first()
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
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": (total + page_size - 1) // page_size,
                },
            },
        }


@agent_router.post("", summary="创建智能体")
async def create_agent(request: AgentCreateRequest, current_user: User = Depends(get_required_user)):
    """创建新的自定义智能体"""
    with db_manager.get_session_context() as session:
        # 检查名称是否重复（同一用户）
        existing_agent = (
            session.query(CustomAgent)
            .filter(
                and_(
                    CustomAgent.name == request.name,
                    CustomAgent.created_by == current_user.id,
                    CustomAgent.deleted_at.is_(None),
                )
            )
            .first()
        )

        if existing_agent:
            raise HTTPException(status_code=400, detail="智能体名称已存在")

        # 构建配置字典
        model_config = _build_model_config(provider=request.provider, model_name=request.model_name, model_parameters=request.model_parameters)

        tools_config = _build_tools_config(tools=request.tools, mcp_skills=request.mcp_skills)

        knowledge_config = _build_knowledge_config(knowledge_databases=request.knowledge_databases, retrieval_params=request.retrieval_params)

        # 创建智能体
        agent = CustomAgent(
            agent_id=str(uuid.uuid4()),
            name=request.name,
            description=request.description,
            agent_type=request.agent_type,
            avatar=request.avatar,
            system_prompt=request.system_prompt,
            model_config=model_config,
            tools_config=tools_config,
            knowledge_config=knowledge_config,
            tags=request.tags,
            is_public=request.is_public,
            created_by=current_user.id,
        )

        session.add(agent)
        session.flush()  # 获取生成的ID

        logger.info(f"用户 {current_user.username} 创建了智能体: {agent.name}")

        return {"success": True, "message": "智能体创建成功", "data": agent.to_dict()}


@agent_router.get("/{agent_id}", summary="获取智能体详情")
async def get_agent(agent_id: str, current_user: User = Depends(get_required_user)):
    """获取单个智能体的详细信息"""
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


@agent_router.put("/{agent_id}", summary="更新智能体")
async def update_agent(agent_id: str, request: AgentUpdateRequest, current_user: User = Depends(get_required_user)):
    """更新智能体信息"""
    with db_manager.get_session_context() as session:
        # 查询智能体
        agent = session.query(CustomAgent).filter(and_(CustomAgent.agent_id == agent_id, CustomAgent.deleted_at.is_(None))).first()

        if not agent:
            raise HTTPException(status_code=404, detail="智能体不存在")

        # 权限检查：只能修改自己的智能体
        if agent.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="无权限修改此智能体")

        # 更新基础字段
        update_data = request.model_dump(exclude_unset=True)
        basic_fields = ["name", "description", "agent_type", "avatar", "system_prompt", "tags", "is_public"]

        for field in basic_fields:
            if field in update_data:
                setattr(agent, field, update_data[field])

        # 更新模型配置
        if any(field in update_data for field in ["provider", "model_name", "model_parameters"]):
            current_model_config = agent.model_config or {}
            if "provider" in update_data:
                current_model_config["provider"] = update_data["provider"]
            if "model_name" in update_data:
                current_model_config["model_name"] = update_data["model_name"]
            if "model_parameters" in update_data:
                current_model_config["parameters"] = update_data["model_parameters"]
            agent.model_config = current_model_config

        # 更新工具配置
        if any(field in update_data for field in ["tools", "mcp_skills"]):
            current_tools_config = agent.tools_config or {}
            if "tools" in update_data:
                current_tools_config["builtin_tools"] = update_data["tools"]
            if "mcp_skills" in update_data:
                current_tools_config["mcp_skills"] = update_data["mcp_skills"]
            agent.tools_config = current_tools_config

        # 更新知识库配置
        if any(field in update_data for field in ["knowledge_databases", "retrieval_params"]):
            current_knowledge_config = agent.knowledge_config or {}
            if "knowledge_databases" in update_data:
                current_knowledge_config["databases"] = update_data["knowledge_databases"]
            if "retrieval_params" in update_data:
                current_knowledge_config["retrieval_params"] = update_data["retrieval_params"]
            agent.knowledge_config = current_knowledge_config

        agent.updated_at = datetime.utcnow()

        # === 新增：保存配置到YAML文件 ===
        import yaml
        import os
        # 组装格式
        config = {
            "name": agent.name,
            "description": agent.description or "",
            "system_prompt": agent.system_prompt or "",
            "provider": (agent.model_config or {}).get("provider", ""),
            "model_name": (agent.model_config or {}).get("model_name", ""),
            "model_parameters": (agent.model_config or {}).get("parameters", {}),
            "tools": (agent.tools_config or {}).get("builtin_tools", []),
            "mcp_skills": (agent.tools_config or {}).get("mcp_skills", []),
            "knowledge_databases": (agent.knowledge_config or {}).get("databases", []),
            "retrieval_params": (agent.knowledge_config or {}).get("retrieval_params", {}),
        }
        # 文件名处理，前缀加@，防止特殊字符
        safe_name = agent.name.replace("/", "_").replace("\\", "_").replace(" ", "_")
        file_name = f"@{safe_name}.private.yaml"
        config_dir = os.path.join(os.path.dirname(__file__), "../config/agents")
        os.makedirs(config_dir, exist_ok=True)
        file_path = os.path.join(config_dir, file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, sort_keys=False)
        # === END ===

        logger.info(f"用户 {current_user.username} 更新了智能体: {agent.name}")

        return {"success": True, "message": "智能体更新成功", "data": agent.to_dict()}


@agent_router.delete("/{agent_id}", summary="删除智能体")
async def delete_agent(agent_id: str, current_user: User = Depends(get_required_user)):
    """删除智能体（软删除）"""
    with db_manager.get_session_context() as session:
        # 查询智能体
        agent = session.query(CustomAgent).filter(and_(CustomAgent.agent_id == agent_id, CustomAgent.deleted_at.is_(None))).first()

        if not agent:
            raise HTTPException(status_code=404, detail="智能体不存在")

        # 权限检查：只能删除自己的智能体
        if agent.created_by != str(current_user.id) and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="无权限删除此智能体")

        # 软删除
        agent.deleted_at = datetime.utcnow()
        agent.is_active = False

        logger.info(f"用户 {current_user.username} 删除了智能体: {agent.name}")

        return {"success": True, "message": "智能体删除成功"}


@agent_router.post("/{agent_id}/duplicate", summary="复制智能体")
async def duplicate_agent(
    agent_id: str,
    new_name: Optional[str] = Body(None, description="新智能体名称"),
    current_user: User = Depends(get_required_user),
):
    """复制现有智能体创建新的智能体"""
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
            .filter(
                and_(
                    CustomAgent.name == new_name,
                    CustomAgent.created_by == current_user.id,
                    CustomAgent.deleted_at.is_(None),
                )
            )
            .first()
        )

        if existing_agent:
            # 添加序号
            counter = 1
            while existing_agent:
                test_name = f"{new_name} ({counter})"
                existing_agent = (
                    session.query(CustomAgent)
                    .filter(
                        and_(
                            CustomAgent.name == test_name,
                            CustomAgent.created_by == current_user.id,
                            CustomAgent.deleted_at.is_(None),
                        )
                    )
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


@agent_router.post("/{agent_id}/instance", summary="创建智能体实例")
async def create_agent_instance(agent_id: str, config_override: AgentConfigOverride = Body(...), current_user: User = Depends(get_required_user)):
    """为用户创建智能体实例"""
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


@agent_router.get("/{agent_id}/instance", summary="获取用户的智能体实例")
async def get_agent_instance(agent_id: str, current_user: User = Depends(get_required_user)):
    """获取用户的智能体实例信息"""
    with db_manager.get_session_context() as session:
        instance = session.query(AgentInstance).filter(and_(AgentInstance.agent_id == agent_id, AgentInstance.user_id == current_user.id)).first()

        if not instance:
            raise HTTPException(status_code=404, detail="智能体实例不存在")

        return {"success": True, "data": instance.to_dict()}


@agent_router.delete("/{agent_id}/instance", summary="删除智能体实例")
async def delete_agent_instance(agent_id: str, current_user: User = Depends(get_required_user)):
    """删除用户的智能体实例"""
    with db_manager.get_session_context() as session:
        instance = session.query(AgentInstance).filter(and_(AgentInstance.agent_id == agent_id, AgentInstance.user_id == current_user.id)).first()

        if not instance:
            raise HTTPException(status_code=404, detail="智能体实例不存在")

        session.delete(instance)

        return {"success": True, "message": "智能体实例删除成功"}


@agent_router.post("/{agent_id}/create_chatbot", summary="创建ChatbotAgent实例")
async def create_chatbot_agent(agent_id: str, current_user: User = Depends(get_required_user)):
    """从数据库记录创建ChatbotAgent实例"""
    with db_manager.get_session_context() as session:
        # 查询智能体
        agent = session.query(CustomAgent).filter(and_(CustomAgent.agent_id == agent_id, CustomAgent.deleted_at.is_(None))).first()

        if not agent:
            raise HTTPException(status_code=404, detail="智能体不存在")

        # 权限检查：只能使用自己的或公开的智能体
        if agent.created_by != current_user.id and not agent.is_public:
            raise HTTPException(status_code=403, detail="无权限使用此智能体")

        try:
            # 导入ChatbotAgent
            from src.agents.chatbot_agent import ChatbotAgent

            # 直接从数据库记录创建ChatbotAgent实例
            chatbot_agent = ChatbotAgent.from_db_record(agent)

            # 获取智能体信息
            agent_info = await chatbot_agent.get_info()

            logger.info(f"用户 {current_user.username} 创建了ChatbotAgent实例: {agent.name}")

            return {
                "success": True,
                "message": "ChatbotAgent实例创建成功",
                "data": {"agent_info": agent_info, "agent_config": agent_info.get("config_schema", {})},
            }

        except Exception as e:
            logger.error(f"创建ChatbotAgent实例失败: {e}")
            raise HTTPException(status_code=500, detail=f"创建智能体实例失败: {str(e)}")


@agent_router.get("/{agent_id}/config", summary="获取智能体配置")
async def get_agent_config(agent_id: str, current_user: User = Depends(get_required_user)):
    """获取智能体的ChatbotConfiguration兼容配置"""
    with db_manager.get_session_context() as session:
        # 查询智能体
        agent = session.query(CustomAgent).filter(and_(CustomAgent.agent_id == agent_id, CustomAgent.deleted_at.is_(None))).first()

        if not agent:
            raise HTTPException(status_code=404, detail="智能体不存在")

        # 权限检查：只能查看自己的或公开的智能体
        if agent.created_by != current_user.id and not agent.is_public:
            raise HTTPException(status_code=403, detail="无权限访问此智能体")

        # 转换为ChatbotConfiguration兼容格式
        config = agent.to_chatbot_config()

        return {
            "success": True,
            "data": {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "description": agent.description,
                "agent_type": agent.agent_type,
                "config": config,
            },
        }


@agent_router.get("/{agent_id}/stats", summary="获取智能体统计信息")
async def get_agent_stats(agent_id: str, current_user: User = Depends(get_required_user)):
    """获取智能体的统计信息（如实例数量、创建时间、最后更新时间）"""
    with db_manager.get_session_context() as session:
        agent = session.query(CustomAgent).filter(
            and_(CustomAgent.agent_id == agent_id, CustomAgent.deleted_at.is_(None))
        ).first()
        if not agent:
            raise HTTPException(status_code=404, detail="智能体不存在")

        # 统计该 agent 的实例数量
        instance_count = session.query(AgentInstance).filter(AgentInstance.agent_id == agent_id).count()

        stats = {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "created_at": agent.created_at,
            "updated_at": agent.updated_at,
            "instance_count": instance_count,
        }
        return {"success": True, "data": stats}
