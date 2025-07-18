from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.sql import func

from models import Base

class SiteConfig(Base):
    """网站配置模型"""
    __tablename__ = 'site_configs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String, nullable=False, unique=True, index=True)  # 配置键，如 'site_name', 'site_logo'
    config_value = Column(Text, nullable=True)  # 配置值
    config_type = Column(String, nullable=False, default='string')  # 配置类型: string, number, boolean, json, file
    description = Column(Text, nullable=True)  # 配置描述
    category = Column(String, nullable=False, default='general')  # 配置分类: general, appearance, advanced
    is_system = Column(Boolean, default=False)  # 是否为系统配置（不可删除）
    is_public = Column(Boolean, default=True)  # 是否为公开配置（前端可访问）
    
    # 时间戳
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "config_key": self.config_key,
            "config_value": self.config_value,
            "config_type": self.config_type,
            "description": self.description,
            "category": self.category,
            "is_system": self.is_system,
            "is_public": self.is_public,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def get_typed_value(self):
        """根据配置类型返回正确的值类型"""
        if self.config_value is None:
            return None
            
        if self.config_type == 'boolean':
            return self.config_value.lower() in ('true', '1', 'yes', 'on')
        elif self.config_type == 'number':
            try:
                if '.' in self.config_value:
                    return float(self.config_value)
                else:
                    return int(self.config_value)
            except (ValueError, TypeError):
                return 0
        elif self.config_type == 'json':
            import json
            try:
                return json.loads(self.config_value)
            except (json.JSONDecodeError, TypeError):
                return {}
        else:  # string, file
            return self.config_value

    @staticmethod
    def get_default_configs():
        """获取默认配置列表"""
        return [
            {
                "config_key": "site_name",
                "config_value": "Yuxi Agent",
                "config_type": "string",
                "description": "网站名称",
                "category": "general",
                "is_system": True,
                "is_public": True
            },
            {
                "config_key": "site_description",
                "config_value": "智能代理平台",
                "config_type": "string",
                "description": "网站描述",
                "category": "general",
                "is_system": True,
                "is_public": True
            },
            {
                "config_key": "site_logo",
                "config_value": "/public/avatar.png",
                "config_type": "file",
                "description": "网站Logo",
                "category": "appearance",
                "is_system": True,
                "is_public": True
            },
            {
                "config_key": "site_domain",
                "config_value": "localhost:8000",
                "config_type": "string",
                "description": "网站域名",
                "category": "general",
                "is_system": True,
                "is_public": False
            },
            {
                "config_key": "site_theme",
                "config_value": "light",
                "config_type": "string",
                "description": "网站主题",
                "category": "appearance",
                "is_system": True,
                "is_public": True
            },
            {
                "config_key": "registration_enabled",
                "config_value": "true",
                "config_type": "boolean",
                "description": "是否允许用户注册",
                "category": "general",
                "is_system": True,
                "is_public": False
            },
            {
                "config_key": "max_file_size_mb",
                "config_value": "10",
                "config_type": "number",
                "description": "最大文件上传大小(MB)",
                "category": "advanced",
                "is_system": True,
                "is_public": False
            },
            {
                "config_key": "user_storage_limit_mb",
                "config_value": "1024",
                "config_type": "number",
                "description": "用户存储空间限制(MB)",
                "category": "advanced",
                "is_system": True,
                "is_public": False
            }
        ] 