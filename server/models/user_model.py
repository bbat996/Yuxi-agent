from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from models import Base

class User(Base):
    """用户模型"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default='user')  # 角色: superadmin, admin, user
    
    # 基本个人信息
    display_name = Column(String, nullable=True)  # 显示名称
    email = Column(String, nullable=True)  # 邮箱
    avatar = Column(Text, nullable=True)  # 头像(base64 或 文件路径)
    
    # 使用统计
    total_messages = Column(Integer, default=0)  # 总消息数
    total_tokens = Column(BigInteger, default=0)  # 总Token使用量
    total_chats = Column(Integer, default=0)  # 总对话数
    file_storage_used = Column(BigInteger, default=0)  # 文件存储使用量(字节)
    
    # 时间戳
    created_at = Column(DateTime, default=func.now())
    last_login = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关联操作日志
    operation_logs = relationship("OperationLog", back_populates="user")

    def to_dict(self, include_password=False):
        result = {
            "id": self.id,
            "username": self.username,
            "display_name": self.display_name,
            "email": self.email,
            "avatar": self.avatar,
            "role": self.role,
            "total_messages": self.total_messages,
            "total_tokens": self.total_tokens,
            "total_chats": self.total_chats,
            "file_storage_used": self.file_storage_used,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        if include_password:
            result["password_hash"] = self.password_hash
        return result

    def get_display_name(self):
        """获取显示名称，如果没有设置则使用用户名"""
        return self.display_name or self.username
    
    def get_storage_used_mb(self):
        """获取存储使用量(MB)"""
        return round(self.file_storage_used / (1024 * 1024), 2) if self.file_storage_used else 0

class OperationLog(Base):
    """操作日志模型"""
    __tablename__ = 'operation_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    operation = Column(String, nullable=False)
    details = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    timestamp = Column(DateTime, default=func.now())

    # 关联用户
    user = relationship("User", back_populates="operation_logs")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "operation": self.operation,
            "details": self.details,
            "ip_address": self.ip_address,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }
