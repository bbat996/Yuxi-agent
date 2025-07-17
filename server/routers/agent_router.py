from fastapi import APIRouter, Depends, HTTPException, Query, Body, BackgroundTasks
from sqlalchemy import desc, asc, and_, or_
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
from pydantic import BaseModel, Field
import yaml
import os

from db_manager import DBManager
from models.agent_models import CustomAgent, AgentInstance
from models.user_model import User
from utils.auth_middleware import get_required_user
from src.utils import logger
from config.agent_config import AgentConfig, ModelConfig, KnowledgeConfig, McpConfig, RetrievalConfig

# 创建路由器
agent_router = APIRouter(prefix="/agents", tags=["agents"])
db_manager = DBManager()

# 模型配置
class ModelConfigRequest(BaseModel):
    provider: str = Field(default="", description="模型提供商")
    model: str = Field(default="", description="模型名称")
    config: Dict[str, Any] = Field(default={"temperature": 0.7, "max_tokens": 2048}, description="模型参数配置")

# 知识库检索配置
class RetrievalConfigRequest(BaseModel):
    top_k: int = Field(default=3, description="检索返回的文档数量")
    similarity_threshold: float = Field(default=0.5, description="相似度阈值")

# 知识库配置
class KnowledgeConfigRequest(BaseModel):
    enabled: bool = Field(default=False, description="是否启用知识库")
    databases: List[str] = Field(default_factory=list, description="知识库数据库列表")
    retrieval_config: RetrievalConfigRequest = Field(default_factory=RetrievalConfigRequest, description="检索配置")

# MCP配置
class McpConfigRequest(BaseModel):
    enabled: bool = Field(default=False, description="是否启用MCP服务")
    servers: List[str] = Field(default_factory=list, description="MCP服务器列表")

class AgentCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="智能体名称")
    description: Optional[str] = Field(None, max_length=500, description="智能体描述")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    llm_config: ModelConfigRequest = Field(default_factory=ModelConfigRequest, description="语言模型配置")
    knowledge_config: KnowledgeConfigRequest = Field(default_factory=KnowledgeConfigRequest, description="知识库配置")
    mcp_config: McpConfigRequest = Field(default_factory=McpConfigRequest, description="MCP配置")
    tools: List[str] = Field(default_factory=list, description="工具列表")
    

class AgentUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="智能体名称")
    description: Optional[str] = Field(None, max_length=500, description="智能体描述")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    llm_config: Optional[ModelConfigRequest] = Field(None, description="语言模型配置")
    knowledge_config: Optional[KnowledgeConfigRequest] = Field(None, description="知识库配置")
    mcp_config: Optional[McpConfigRequest] = Field(None, description="MCP配置")
    tools: Optional[List[str]] = Field(None, description="工具列表")


class AgentConfigOverride(BaseModel):
    """运行时配置覆盖"""
    llm_config: Optional[ModelConfigRequest] = Field(None, description="语言模型配置")
    knowledge_config: Optional[KnowledgeConfigRequest] = Field(None, description="知识库配置")
    mcp_config: Optional[McpConfigRequest] = Field(None, description="MCP配置")
    tools: Optional[List[str]] = Field(None, description="工具列表")


def _build_llm_config(provider: str = None, model_name: str = None, model_parameters: Dict[str, Any] = None) -> Dict[str, Any]:
    """构建模型配置字典"""
    config = {}
    if provider:
        config["provider"] = provider
    if model_name:
        config["model"] = model_name  # 修正字段名为model
    if model_parameters:
        config["config"] = model_parameters  # 修正字段名为config
    return config


# Function removed as we now directly set the tools and mcp_config fields


def _build_knowledge_config(knowledge_databases: List[str] = None, retrieval_params: Dict[str, Any] = None) -> Dict[str, Any]:
    """构建知识库配置字典"""
    config = {}
    if knowledge_databases is not None:
        config["databases"] = knowledge_databases
    if retrieval_params is not None:
        config["retrieval_config"] = retrieval_params  # 修正字段名为retrieval_config
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
        llm_config = _build_llm_config(provider=request.llm_config.provider, model_name=request.llm_config.model, model_parameters=request.llm_config.config)

        knowledge_config = _build_knowledge_config(knowledge_databases=request.knowledge_config.databases, retrieval_params=request.knowledge_config.retrieval_config.model_dump())

        # 创建智能体
        agent = CustomAgent(
            agent_id=str(uuid.uuid4()),
            name=request.name,
            description=request.description,
            agent_type="chatbot",  # Default type
            system_prompt=request.system_prompt,
            llm_config=llm_config,
            tools=request.tools,
            mcp_config={"enabled": bool(request.mcp_config.servers), "servers": request.mcp_config.servers} if request.mcp_config else None,
            knowledge_config=knowledge_config,
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
async def update_agent(agent_id: str, request: AgentUpdateRequest, background_tasks: BackgroundTasks, current_user: User = Depends(get_required_user)):
    """更新智能体信息"""
    with db_manager.get_session_context() as session:
        agent = session.query(CustomAgent).filter(and_(CustomAgent.agent_id == agent_id, CustomAgent.deleted_at.is_(None))).first()

        if not agent:
            raise HTTPException(status_code=404, detail="智能体不存在")

        if agent.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="无权限修改此智能体")

        # 记录更新请求
        logger.info(f"更新智能体 {agent_id}")
        
        # 更新基础字段
        if request.name is not None:
            agent.name = request.name
        if request.description is not None:
            agent.description = request.description
        if request.system_prompt is not None:
            agent.system_prompt = request.system_prompt

        # 更新模型配置
        if request.llm_config is not None:
            agent.llm_config = {
                "provider": request.llm_config.provider,
                "model": request.llm_config.model,
                "config": request.llm_config.config
            }

        # 更新工具配置
        if request.tools is not None:
            agent.tools = request.tools
        
        # 更新MCP配置
        if request.mcp_config is not None:
            agent.mcp_config = {
                "enabled": request.mcp_config.enabled,
                "servers": request.mcp_config.servers
            }

        # 更新知识库配置
        if request.knowledge_config is not None:
            agent.knowledge_config = {
                "enabled": request.knowledge_config.enabled,
                "databases": request.knowledge_config.databases,
                "retrieval_config": request.knowledge_config.retrieval_config.model_dump()
            }

        agent.updated_at = datetime.utcnow()
        
        logger.info(f"更新后的智能体配置: llm_config={agent.llm_config}, tools={agent.tools}, mcp_config={agent.mcp_config}, knowledge_config={agent.knowledge_config}")

        # 保存到数据库
        session.commit()
        session.flush()

        # 创建AgentConfig用于保存YAML文件
        try:
            # 从ORM模型转换为配置模型，确保字段一致性
            agent_config = AgentConfig(
                name=agent.name,
                description=agent.description or "",
                system_prompt=agent.system_prompt or "",
                llm_config=ModelConfig(
                    provider=agent.llm_config.get("provider", "") if agent.llm_config else "",
                    model=agent.llm_config.get("model", "") if agent.llm_config else "",
                    config=agent.llm_config.get("config", {}) if agent.llm_config else {}
                ),
                knowledge_config=KnowledgeConfig(
                    enabled=agent.knowledge_config.get("enabled", False) if agent.knowledge_config else False,
                    databases=agent.knowledge_config.get("databases", []) if agent.knowledge_config else [],
                    retrieval_config=RetrievalConfig(**(agent.knowledge_config.get("retrieval_config", {})) if agent.knowledge_config else {})
                ),
                mcp_config=McpConfig(
                    enabled=agent.mcp_config.get("enabled", False) if agent.mcp_config else False,
                    servers=agent.mcp_config.get("servers", []) if agent.mcp_config else []
                ),
                tools=agent.tools or []
            )
            background_tasks.add_task(agent_config.save_to_yaml)
        except Exception as e:
            logger.error(f"保存YAML文件失败: {e}")

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
        if agent.created_by != str(current_user.id) and current_user.role not in ['admin', 'superadmin']:
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
            system_prompt=original_agent.system_prompt,
            llm_config=original_agent.llm_config,
            tools=original_agent.tools,
            mcp_config=original_agent.mcp_config,
            knowledge_config=original_agent.knowledge_config,
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
            # 从 AgentManager 获取或创建实例
            from src.agents.agent_manager import agent_manager
            chatbot_agent = await agent_manager.aget_agent(agent_id)

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


@agent_router.get("/{agent_id}/publish", summary="获取智能体发布配置")
async def get_agent_publish_config(agent_id: str, current_user: User = Depends(get_required_user)):
    """获取智能体的发布配置"""
    with db_manager.get_session_context() as session:
        agent = session.query(CustomAgent).filter(and_(CustomAgent.agent_id == agent_id, CustomAgent.deleted_at.is_(None))).first()

        if not agent:
            raise HTTPException(status_code=404, detail="智能体不存在")

        # 权限检查：只能查看自己的或公开的智能体
        if agent.created_by != current_user.id and not agent.is_public:
            raise HTTPException(status_code=403, detail="无权限访问此智能体")

        # 返回默认的发布配置
        default_publish_config = {
            "channels": [],
            "api_settings": {
                "enabled": False,
                "api_key": "",
                "rate_limit": 60,
                "ip_whitelist_mode": "none",
                "ip_whitelist": "",
                "origin_mode": "none",
                "origin_whitelist": ""
            },
            "embed_settings": {
                "enabled": False,
                "mode": "chat",
                "allowed_domains": "",
                "theme_color": "1890ff",
                "position": "bottom-right", 
                "welcome_message": "您好！有什么可以帮助您的吗？",
                "button_text": "联系客服",
                "window_title": "智能客服"
            }
        }

        return {"success": True, "data": default_publish_config}


@agent_router.put("/{agent_id}/publish", summary="更新智能体发布配置")
async def update_agent_publish_config(agent_id: str, config: dict = Body(...), current_user: User = Depends(get_required_user)):
    """更新智能体的发布配置"""
    with db_manager.get_session_context() as session:
        agent = session.query(CustomAgent).filter(and_(CustomAgent.agent_id == agent_id, CustomAgent.deleted_at.is_(None))).first()

        if not agent:
            raise HTTPException(status_code=404, detail="智能体不存在")

        if agent.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="无权限修改此智能体")

        # 这里可以添加发布配置的验证逻辑
        # 暂时只记录日志，不保存到数据库
        logger.info(f"用户 {current_user.username} 更新了智能体 {agent_id} 的发布配置: {config}")

        return {"success": True, "message": "发布配置更新成功", "data": config}
