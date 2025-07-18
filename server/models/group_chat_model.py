from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from models import Base

class GroupChat(Base):
    """群聊模型"""
    __tablename__ = 'group_chats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(String, nullable=False, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)  # 群聊名称
    description = Column(Text, nullable=True)  # 群聊描述
    avatar = Column(Text, nullable=True)  # 群聊头像
    
    # 创建者和状态
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    is_active = Column(Boolean, default=True)  # 是否活跃
    
    # 群聊设置
    max_members = Column(Integer, default=10)  # 最大成员数（包括智能体）
    allow_file_sharing = Column(Boolean, default=True)  # 是否允许文件分享
    auto_save_files = Column(Boolean, default=True)  # 是否自动保存文件到创建者空间
    
    # 统计信息
    message_count = Column(Integer, default=0)  # 消息总数
    file_count = Column(Integer, default=0)  # 文件总数
    
    # 时间戳
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_message_at = Column(DateTime, nullable=True)  # 最后消息时间

    # 关系
    members = relationship("GroupChatMember", back_populates="group_chat", cascade="all, delete-orphan")
    messages = relationship("GroupChatMessage", back_populates="group_chat", cascade="all, delete-orphan")
    files = relationship("GroupChatFile", back_populates="group_chat", cascade="all, delete-orphan")

    def to_dict(self, include_members=False, include_stats=True):
        result = {
            "id": self.id,
            "group_id": self.group_id,
            "name": self.name,
            "description": self.description,
            "avatar": self.avatar,
            "created_by": self.created_by,
            "is_active": self.is_active,
            "max_members": self.max_members,
            "allow_file_sharing": self.allow_file_sharing,
            "auto_save_files": self.auto_save_files,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None
        }
        
        if include_stats:
            result.update({
                "message_count": self.message_count,
                "file_count": self.file_count,
                "member_count": len(self.members) if self.members else 0
            })
        
        if include_members and self.members:
            result["members"] = [member.to_dict() for member in self.members]
        
        return result

class GroupChatMember(Base):
    """群聊成员模型"""
    __tablename__ = 'group_chat_members'

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(String, ForeignKey('group_chats.group_id'), nullable=False)
    
    # 成员类型和标识
    member_type = Column(String, nullable=False)  # 'user' 或 'agent'
    member_id = Column(String, nullable=False)  # 用户ID或智能体ID
    member_name = Column(String, nullable=False)  # 成员显示名称
    member_avatar = Column(Text, nullable=True)  # 成员头像
    
    # 权限和状态
    role = Column(String, default='member')  # 'admin', 'member'
    is_active = Column(Boolean, default=True)  # 是否活跃
    
    # 个性化设置
    nickname = Column(String, nullable=True)  # 群内昵称
    mute_notifications = Column(Boolean, default=False)  # 是否静音通知
    
    # 时间戳
    joined_at = Column(DateTime, default=func.now())
    last_seen = Column(DateTime, nullable=True)

    # 关系
    group_chat = relationship("GroupChat", back_populates="members")

    def to_dict(self):
        return {
            "id": self.id,
            "group_id": self.group_id,
            "member_type": self.member_type,
            "member_id": self.member_id,
            "member_name": self.member_name,
            "member_avatar": self.member_avatar,
            "role": self.role,
            "is_active": self.is_active,
            "nickname": self.nickname,
            "mute_notifications": self.mute_notifications,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None
        }

class GroupChatMessage(Base):
    """群聊消息模型"""
    __tablename__ = 'group_chat_messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String, nullable=False, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    group_id = Column(String, ForeignKey('group_chats.group_id'), nullable=False)
    
    # 发送者信息
    sender_type = Column(String, nullable=False)  # 'user' 或 'agent'
    sender_id = Column(String, nullable=False)  # 发送者ID
    sender_name = Column(String, nullable=False)  # 发送者显示名称
    
    # 消息内容
    content = Column(Text, nullable=False)  # 消息内容
    message_type = Column(String, default='text')  # 'text', 'file', 'system', 'tool_call'
    
    # 消息元数据
    message_metadata = Column(JSON, nullable=True)  # 消息元数据（@mentions, 文件信息等）
    reply_to = Column(String, nullable=True)  # 回复的消息ID
    
    # 消息状态
    is_edited = Column(Boolean, default=False)  # 是否已编辑
    is_deleted = Column(Boolean, default=False)  # 是否已删除
    
    # 时间戳
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关系
    group_chat = relationship("GroupChat", back_populates="messages")

    def to_dict(self):
        return {
            "id": self.id,
            "message_id": self.message_id,
            "group_id": self.group_id,
            "sender_type": self.sender_type,
            "sender_id": self.sender_id,
            "sender_name": self.sender_name,
            "content": self.content,
            "message_type": self.message_type,
            "message_metadata": self.message_metadata,
            "reply_to": self.reply_to,
            "is_edited": self.is_edited,
            "is_deleted": self.is_deleted,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class GroupChatFile(Base):
    """群聊文件模型"""
    __tablename__ = 'group_chat_files'

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(String, nullable=False, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    group_id = Column(String, ForeignKey('group_chats.group_id'), nullable=False)
    
    # 文件信息
    original_name = Column(String, nullable=False)  # 原始文件名
    file_name = Column(String, nullable=False)  # 存储文件名
    file_path = Column(Text, nullable=False)  # 文件存储路径
    file_size = Column(BigInteger, nullable=False)  # 文件大小（字节）
    file_type = Column(String, nullable=True)  # 文件类型/MIME类型
    
    # 上传者信息
    uploaded_by_type = Column(String, nullable=False)  # 'user' 或 'agent'
    uploaded_by_id = Column(String, nullable=False)  # 上传者ID
    uploaded_by_name = Column(String, nullable=False)  # 上传者名称
    
    # 关联消息
    message_id = Column(String, nullable=True)  # 关联的消息ID
    
    # 文件状态
    is_public = Column(Boolean, default=True)  # 群内是否公开
    download_count = Column(Integer, default=0)  # 下载次数
    
    # 时间戳
    created_at = Column(DateTime, default=func.now())

    # 关系
    group_chat = relationship("GroupChat", back_populates="files")

    def to_dict(self):
        return {
            "id": self.id,
            "file_id": self.file_id,
            "group_id": self.group_id,
            "original_name": self.original_name,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "uploaded_by_type": self.uploaded_by_type,
            "uploaded_by_id": self.uploaded_by_id,
            "uploaded_by_name": self.uploaded_by_name,
            "message_id": self.message_id,
            "is_public": self.is_public,
            "download_count": self.download_count,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def get_file_size_mb(self):
        """获取文件大小(MB)"""
        return round(self.file_size / (1024 * 1024), 2) if self.file_size else 0 