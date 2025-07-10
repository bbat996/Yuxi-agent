from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from server.models import Base

class CustomAgent(Base):
    """自定义智能体模型"""
    __tablename__ = 'custom_agents'

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String, nullable=False, unique=True, index=True, default=lambda: str(uuid.uuid4()))  # 智能体ID
    name = Column(String, nullable=False, index=True)  # 智能体名称
    description = Column(Text, nullable=True)  # 描述
    agent_type = Column(String, nullable=False, default='custom')  # 智能体类型 (custom, chatbot, react等)
    avatar = Column(String, nullable=True)  # 头像URL
    
    # 配置字段
    system_prompt = Column(Text, nullable=True)  # 系统提示词
    model_config = Column(JSON, nullable=True)  # 模型配置 {"provider": "zhipu", "model_name": "glm-4-plus", "parameters": {}}
    tools_config = Column(JSON, nullable=True)  # 工具配置 {"builtin_tools": [], "mcp_skills": []}
    knowledge_config = Column(JSON, nullable=True)  # 知识库配置 {"databases": [], "retrieval_params": {}}
    
    # 元数据
    is_active = Column(Boolean, default=True)  # 是否激活
    is_public = Column(Boolean, default=False)  # 是否公开（其他用户可见）
    tags = Column(JSON, nullable=True)  # 标签列表
    
    # 用户关联
    created_by = Column(String, nullable=False, index=True)  # 创建者用户ID
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
                "model_config": self.model_config or {},
                "tools_config": self.tools_config or {},
                "knowledge_config": self.knowledge_config or {}
            })
        
        return result

class PromptTemplate(Base):
    """提示词模板模型"""
    __tablename__ = 'prompt_templates'

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(String, nullable=False, unique=True, index=True, default=lambda: str(uuid.uuid4()))  # 模板ID
    name = Column(String, nullable=False, index=True)  # 模板名称
    content = Column(Text, nullable=False)  # 模板内容
    category = Column(String, nullable=True, index=True)  # 分类 (customer_service, assistant, creative等)
    description = Column(Text, nullable=True)  # 描述
    
    # 模板元数据
    variables = Column(JSON, nullable=True)  # 变量定义 [{"name": "user_name", "type": "string", "description": "用户名称"}]
    is_system = Column(Boolean, default=False)  # 是否为系统预置模板
    is_active = Column(Boolean, default=True)  # 是否激活
    usage_count = Column(Integer, default=0)  # 使用次数
    
    # 创建信息
    created_by = Column(String, nullable=True, index=True)  # 创建者（系统模板为空）
    created_at = Column(DateTime, default=func.now())  # 创建时间
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # 更新时间
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "template_id": self.template_id,
            "name": self.name,
            "content": self.content,
            "category": self.category,
            "description": self.description,
            "variables": self.variables or [],
            "is_system": self.is_system,
            "is_active": self.is_active,
            "usage_count": self.usage_count,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class MCPSkill(Base):
    """MCP技能模型"""
    __tablename__ = 'mcp_skills'

    id = Column(Integer, primary_key=True, autoincrement=True)
    skill_id = Column(String, nullable=False, unique=True, index=True, default=lambda: str(uuid.uuid4()))  # 技能ID
    name = Column(String, nullable=False, index=True)  # 技能名称
    description = Column(Text, nullable=True)  # 技能描述
    
    # MCP配置
    mcp_server = Column(String, nullable=False)  # MCP服务器地址或标识
    mcp_config = Column(JSON, nullable=False)  # MCP连接配置
    tool_schema = Column(JSON, nullable=True)  # 工具Schema定义
    parameters = Column(JSON, nullable=True)  # 默认参数配置
    
    # 技能元数据
    category = Column(String, nullable=True, index=True)  # 分类 (communication, data_processing, automation等)
    version = Column(String, nullable=True)  # 版本号
    is_active = Column(Boolean, default=True)  # 是否激活
    is_verified = Column(Boolean, default=False)  # 是否已验证
    
    # 使用统计
    usage_count = Column(Integer, default=0)  # 使用次数
    success_rate = Column(Float, nullable=True)  # 成功率
    avg_response_time = Column(Float, nullable=True)  # 平均响应时间(毫秒)
    
    # 创建信息
    created_by = Column(String, nullable=True, index=True)  # 创建者
    created_at = Column(DateTime, default=func.now())  # 创建时间
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # 更新时间
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "mcp_server": self.mcp_server,
            "mcp_config": self.mcp_config,
            "tool_schema": self.tool_schema,
            "parameters": self.parameters or {},
            "category": self.category,
            "version": self.version,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "avg_response_time": self.avg_response_time,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

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

class AgentShare(Base):
    """智能体分享模型 - 用于智能体的分享和权限管理"""
    __tablename__ = 'agent_shares'

    id = Column(Integer, primary_key=True, autoincrement=True)
    share_id = Column(String, nullable=False, unique=True, index=True, default=lambda: str(uuid.uuid4()))  # 分享ID
    
    # 关联
    agent_id = Column(String, ForeignKey('custom_agents.agent_id'), nullable=False, index=True)  # 智能体ID
    shared_by = Column(String, nullable=False, index=True)  # 分享者用户ID
    shared_to = Column(String, nullable=True, index=True)  # 被分享者用户ID（为空表示公开分享）
    
    # 分享设置
    permission = Column(String, default='read')  # 权限 (read, write, admin)
    is_active = Column(Boolean, default=True)  # 是否激活
    expires_at = Column(DateTime, nullable=True)  # 过期时间
    
    # 时间戳
    created_at = Column(DateTime, default=func.now())  # 创建时间
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # 更新时间
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "share_id": self.share_id,
            "agent_id": self.agent_id,
            "shared_by": self.shared_by,
            "shared_to": self.shared_to,
            "permission": self.permission,
            "is_active": self.is_active,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        } 