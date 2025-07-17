from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from models import Base

class CustomAgent(Base):
    """自定义智能体模型"""
    __tablename__ = 'custom_agents'

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String, nullable=False, unique=True, index=True, default=lambda: str(uuid.uuid4()))  # 智能体ID
    name = Column(String, nullable=False, index=True)  # 智能体名称
    description = Column(Text, nullable=True)  # 描述
    agent_type = Column(String, nullable=False, default='chatbot')  # 智能体类型 (chatbot, react等)
    avatar = Column(String, nullable=True)  # 头像URL
    
    # 配置字段
    system_prompt = Column(Text, nullable=True)  # 系统提示词
    llm_config = Column(JSON, nullable=True)  # 模型配置 {"provider": "zhipu", "model": "glm-4-plus", "config": {}}
    mcp_config = Column(JSON, nullable=True)  # 工具配置 
    knowledge_config = Column(JSON, nullable=True)  # 知识库配置 {"enabled": false, "databases": [], "retrieval_config": {}}
    tools = Column(JSON, nullable=True)  # 工具配置 
    # 元数据
    is_active = Column(Boolean, default=True)  # 是否激活
    is_public = Column(Boolean, default=False)  # 是否公开（其他用户可见）
    tags = Column(JSON, nullable=True)  # 标签列表
    
    # 用户关联
    created_by = Column(Integer, nullable=False, index=True)  # 创建者用户ID
    created_at = Column(DateTime, default=func.now())  # 创建时间
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # 更新时间
    deleted_at = Column(DateTime, nullable=True)  # 软删除时间
    
    # 关系
    instances = relationship("AgentInstance", back_populates="agent", cascade="all, delete-orphan")
    
    def to_dict(self, include_config=True):
        """转换为字典格式"""
        result = {
            "id": self.id,
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "agent_type": self.agent_type,
            "avatar": self.avatar,
            "is_active": self.is_active,
            "is_public": self.is_public,
            "tags": self.tags or [],
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_config:
            result.update({
                "system_prompt": self.system_prompt,
                "llm_config": self.llm_config or {},
                "tools": self.tools or {},
                "mcp_config": self.mcp_config or {},
                "knowledge_config": self.knowledge_config or {}
            })
        
        return result

    def to_chatbot_config(self) -> dict:
        """转换为ChatbotConfiguration兼容的配置格式"""
        from config.agent_config import AgentConfig, ModelConfig, KnowledgeConfig, McpConfig
        
        # 创建 AgentConfig 实例
        agent_config = AgentConfig()
        
        # 基础信息
        agent_config.name = self.name
        agent_config.description = self.description or ""
        agent_config.system_prompt = self.system_prompt or ""
        
        # 模型配置
        if self.llm_config:
            llm_config = ModelConfig()
            if "provider" in self.llm_config:
                llm_config.provider = self.llm_config["provider"]
            if "model" in self.llm_config:
                llm_config.model = self.llm_config["model"]
            if "config" in self.llm_config:
                llm_config.config = self.llm_config["config"]
            agent_config.llm_config = llm_config
        
        # MCP工具配置
        if self.mcp_config:
            mcp_config = McpConfig()
            if "enabled" in self.mcp_config:
                mcp_config.enabled = self.mcp_config["enabled"]
            if "servers" in self.mcp_config:
                mcp_config.servers = self.mcp_config["servers"]
            agent_config.mcp_config = mcp_config
        
        # 工具配置
        if self.tools:
            agent_config.tools = self.tools
        
        # 知识库配置
        if self.knowledge_config:
            knowledge_config = KnowledgeConfig()
            if "enabled" in self.knowledge_config:
                knowledge_config.enabled = self.knowledge_config["enabled"]
            if "databases" in self.knowledge_config:
                knowledge_config.databases = self.knowledge_config["databases"]
            if "retrieval_config" in self.knowledge_config:
                knowledge_config.retrieval_config = self.knowledge_config["retrieval_config"]
            agent_config.knowledge_config = knowledge_config

        
        # 返回 AgentConfig 的字典格式
        return agent_config.model_dump()

class AgentInstance(Base):
    """智能体实例模型 - 用于追踪用户与智能体的交互状态"""
    __tablename__ = 'agent_instances'

    id = Column(Integer, primary_key=True, autoincrement=True)
    instance_id = Column(String, nullable=False, unique=True, index=True, default=lambda: str(uuid.uuid4()))  # 实例ID
    
    # 关联
    agent_id = Column(String, ForeignKey('custom_agents.agent_id'), nullable=False, index=True)  # 智能体ID
    user_id = Column(String, nullable=False, index=True)  # 用户ID
    
    # 实例状态
    status = Column(String, default='active')  # 状态 (active, paused, stopped)
    config_override = Column(JSON, nullable=True)  # 配置覆盖（用户个性化配置）
    
    # 使用统计
    message_count = Column(Integer, default=0)  # 消息数量
    total_tokens = Column(Integer, default=0)  # 总token数
    last_used = Column(DateTime, nullable=True)  # 最后使用时间
    
    # 偏好设置
    is_favorite = Column(Boolean, default=False)  # 是否收藏
    custom_name = Column(String, nullable=True)  # 用户自定义名称
    
    # 时间戳
    created_at = Column(DateTime, default=func.now())  # 创建时间
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # 更新时间
    
    # 关系
    agent = relationship("CustomAgent", back_populates="instances")
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "instance_id": self.instance_id,
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "status": self.status,
            "config_override": self.config_override or {},
            "message_count": self.message_count,
            "total_tokens": self.total_tokens,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "is_favorite": self.is_favorite,
            "custom_name": self.custom_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
