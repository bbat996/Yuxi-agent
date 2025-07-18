from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import uuid
import json

from db_manager import db_manager
from models.group_chat_model import GroupChat, GroupChatMember, GroupChatMessage, GroupChatFile
from models.user_model import User
from models.agent_models import CustomAgent
from utils.auth_middleware import get_db, get_current_user
from config.app_config import config

# 创建路由器
group_chat = APIRouter(prefix="/group-chat", tags=["group-chat"])

# 请求和响应模型
class GroupChatCreate(BaseModel):
    name: str
    description: str = None
    avatar: str = None
    max_members: int = 10
    allow_file_sharing: bool = True
    auto_save_files: bool = True
    initial_agents: List[str] = []  # 初始智能体ID列表

class GroupChatUpdate(BaseModel):
    name: str = None
    description: str = None
    avatar: str = None
    max_members: int = None
    allow_file_sharing: bool = None
    auto_save_files: bool = None

class MemberAdd(BaseModel):
    member_type: str  # 'user' 或 'agent'
    member_id: str
    role: str = 'member'

class MessageSend(BaseModel):
    content: str
    message_type: str = 'text'
    metadata: Dict[str, Any] = None
    reply_to: str = None

@group_chat.post("/", summary="创建群聊")
async def create_group_chat(
    group_data: GroupChatCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建新的群聊"""
    try:
        # 创建群聊
        new_group = GroupChat(
            name=group_data.name,
            description=group_data.description,
            avatar=group_data.avatar,
            created_by=current_user.id,
            max_members=group_data.max_members,
            allow_file_sharing=group_data.allow_file_sharing,
            auto_save_files=group_data.auto_save_files
        )
        
        db.add(new_group)
        db.flush()  # 获取group_id
        
        # 添加创建者为管理员
        creator_member = GroupChatMember(
            group_id=new_group.group_id,
            member_type='user',
            member_id=str(current_user.id),
            member_name=current_user.get_display_name(),
            member_avatar=current_user.avatar,
            role='admin'
        )
        db.add(creator_member)
        
        # 添加初始智能体
        for agent_id in group_data.initial_agents:
            agent = db.query(CustomAgent).filter(CustomAgent.agent_id == agent_id).first()
            if agent:
                agent_member = GroupChatMember(
                    group_id=new_group.group_id,
                    member_type='agent',
                    member_id=agent_id,
                    member_name=agent.name,
                    member_avatar=agent.avatar,
                    role='member'
                )
                db.add(agent_member)
        
        # 添加系统欢迎消息
        welcome_message = GroupChatMessage(
            group_id=new_group.group_id,
            sender_type='system',
            sender_id='system',
            sender_name='系统',
            content=f'欢迎来到群聊 "{group_data.name}"！',
            message_type='system'
        )
        db.add(welcome_message)
        
        new_group.message_count = 1
        new_group.last_message_at = datetime.now()
        
        db.commit()
        
        return {
            "success": True,
            "message": "群聊创建成功",
            "data": new_group.to_dict(include_members=True)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建群聊失败: {str(e)}")

@group_chat.get("/", summary="获取用户的群聊列表")
async def get_user_group_chats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户参与的群聊列表"""
    try:
        # 查找用户参与的群聊
        user_groups = db.query(GroupChat).join(GroupChatMember).filter(
            GroupChatMember.member_type == 'user',
            GroupChatMember.member_id == str(current_user.id),
            GroupChatMember.is_active == True,
            GroupChat.is_active == True
        ).all()
        
        groups_data = []
        for group in user_groups:
            group_dict = group.to_dict(include_stats=True)
            # 获取最新消息
            latest_message = db.query(GroupChatMessage).filter(
                GroupChatMessage.group_id == group.group_id,
                GroupChatMessage.is_deleted == False
            ).order_by(GroupChatMessage.created_at.desc()).first()
            
            if latest_message:
                group_dict["latest_message"] = latest_message.to_dict()
            
            groups_data.append(group_dict)
        
        return {
            "success": True,
            "data": groups_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取群聊列表失败: {str(e)}")

@group_chat.get("/{group_id}", summary="获取群聊详情")
async def get_group_chat_detail(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取群聊详情"""
    try:
        # 验证用户权限
        group = db.query(GroupChat).filter(GroupChat.group_id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="群聊不存在")
        
        # 检查用户是否为群聊成员
        member = db.query(GroupChatMember).filter(
            GroupChatMember.group_id == group_id,
            GroupChatMember.member_type == 'user',
            GroupChatMember.member_id == str(current_user.id),
            GroupChatMember.is_active == True
        ).first()
        
        if not member:
            raise HTTPException(status_code=403, detail="无权限访问此群聊")
        
        return {
            "success": True,
            "data": group.to_dict(include_members=True)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取群聊详情失败: {str(e)}")

@group_chat.post("/{group_id}/members", summary="添加群聊成员")
async def add_group_member(
    group_id: str,
    member_data: MemberAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加群聊成员"""
    try:
        # 验证群聊存在和权限
        group = db.query(GroupChat).filter(GroupChat.group_id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="群聊不存在")
        
        # 检查当前用户是否为管理员
        current_member = db.query(GroupChatMember).filter(
            GroupChatMember.group_id == group_id,
            GroupChatMember.member_type == 'user',
            GroupChatMember.member_id == str(current_user.id),
            GroupChatMember.role == 'admin'
        ).first()
        
        if not current_member:
            raise HTTPException(status_code=403, detail="只有群聊管理员可以添加成员")
        
        # 检查成员数量限制
        current_member_count = db.query(GroupChatMember).filter(
            GroupChatMember.group_id == group_id,
            GroupChatMember.is_active == True
        ).count()
        
        if current_member_count >= group.max_members:
            raise HTTPException(status_code=400, detail="群聊成员数量已达上限")
        
        # 检查成员是否已存在
        existing_member = db.query(GroupChatMember).filter(
            GroupChatMember.group_id == group_id,
            GroupChatMember.member_type == member_data.member_type,
            GroupChatMember.member_id == member_data.member_id
        ).first()
        
        if existing_member:
            if existing_member.is_active:
                raise HTTPException(status_code=400, detail="成员已在群聊中")
            else:
                # 重新激活成员
                existing_member.is_active = True
                existing_member.joined_at = datetime.now()
                db.commit()
                return {
                    "success": True,
                    "message": "成员重新加入群聊",
                    "data": existing_member.to_dict()
                }
        
        # 获取成员信息
        member_name = ""
        member_avatar = ""
        
        if member_data.member_type == 'user':
            user = db.query(User).filter(User.id == int(member_data.member_id)).first()
            if not user:
                raise HTTPException(status_code=404, detail="用户不存在")
            member_name = user.get_display_name()
            member_avatar = user.avatar
        elif member_data.member_type == 'agent':
            agent = db.query(CustomAgent).filter(CustomAgent.agent_id == member_data.member_id).first()
            if not agent:
                raise HTTPException(status_code=404, detail="智能体不存在")
            member_name = agent.name
            member_avatar = agent.avatar
        else:
            raise HTTPException(status_code=400, detail="无效的成员类型")
        
        # 创建新成员
        new_member = GroupChatMember(
            group_id=group_id,
            member_type=member_data.member_type,
            member_id=member_data.member_id,
            member_name=member_name,
            member_avatar=member_avatar,
            role=member_data.role
        )
        
        db.add(new_member)
        
        # 添加系统消息
        system_message = GroupChatMessage(
            group_id=group_id,
            sender_type='system',
            sender_id='system',
            sender_name='系统',
            content=f'{member_name} 加入了群聊',
            message_type='system'
        )
        db.add(system_message)
        
        group.message_count += 1
        group.last_message_at = datetime.now()
        
        db.commit()
        
        return {
            "success": True,
            "message": "成员添加成功",
            "data": new_member.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"添加成员失败: {str(e)}")

@group_chat.post("/{group_id}/messages", summary="发送群聊消息")
async def send_group_message(
    group_id: str,
    message_data: MessageSend,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """发送群聊消息"""
    try:
        # 验证群聊和成员权限
        member = db.query(GroupChatMember).filter(
            GroupChatMember.group_id == group_id,
            GroupChatMember.member_type == 'user',
            GroupChatMember.member_id == str(current_user.id),
            GroupChatMember.is_active == True
        ).first()
        
        if not member:
            raise HTTPException(status_code=403, detail="无权限在此群聊发送消息")
        
        # 创建消息
        new_message = GroupChatMessage(
            group_id=group_id,
            sender_type='user',
            sender_id=str(current_user.id),
            sender_name=current_user.get_display_name(),
            content=message_data.content,
            message_type=message_data.message_type,
            metadata=message_data.metadata,
            reply_to=message_data.reply_to
        )
        
        db.add(new_message)
        
        # 更新群聊统计
        group = db.query(GroupChat).filter(GroupChat.group_id == group_id).first()
        group.message_count += 1
        group.last_message_at = datetime.now()
        
        # 更新成员最后查看时间
        member.last_seen = datetime.now()
        
        db.commit()
        
        # 处理@提及的智能体
        if message_data.metadata and 'mentions' in message_data.metadata:
            # 这里可以添加智能体响应逻辑
            pass
        
        return {
            "success": True,
            "message": "消息发送成功",
            "data": new_message.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"发送消息失败: {str(e)}")

@group_chat.get("/{group_id}/messages", summary="获取群聊消息")
async def get_group_messages(
    group_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取群聊消息列表"""
    try:
        # 验证权限
        member = db.query(GroupChatMember).filter(
            GroupChatMember.group_id == group_id,
            GroupChatMember.member_type == 'user',
            GroupChatMember.member_id == str(current_user.id),
            GroupChatMember.is_active == True
        ).first()
        
        if not member:
            raise HTTPException(status_code=403, detail="无权限访问此群聊消息")
        
        # 获取消息
        messages = db.query(GroupChatMessage).filter(
            GroupChatMessage.group_id == group_id,
            GroupChatMessage.is_deleted == False
        ).order_by(GroupChatMessage.created_at.desc()).offset(offset).limit(limit).all()
        
        messages_data = [message.to_dict() for message in reversed(messages)]
        
        return {
            "success": True,
            "data": {
                "messages": messages_data,
                "total": len(messages),
                "has_more": len(messages) == limit
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取消息失败: {str(e)}")

@group_chat.post("/{group_id}/files", summary="上传群聊文件")
async def upload_group_file(
    group_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传文件到群聊"""
    try:
        # 验证权限
        group = db.query(GroupChat).filter(GroupChat.group_id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="群聊不存在")
        
        if not group.allow_file_sharing:
            raise HTTPException(status_code=403, detail="该群聊不允许文件分享")
        
        member = db.query(GroupChatMember).filter(
            GroupChatMember.group_id == group_id,
            GroupChatMember.member_type == 'user',
            GroupChatMember.member_id == str(current_user.id),
            GroupChatMember.is_active == True
        ).first()
        
        if not member:
            raise HTTPException(status_code=403, detail="无权限上传文件到此群聊")
        
        # 创建存储目录
        group_storage_path = os.path.join(config.storage_dir, "groups", group_id, "files")
        os.makedirs(group_storage_path, exist_ok=True)
        
        # 生成文件名
        file_extension = os.path.splitext(file.filename)[1]
        stored_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(group_storage_path, stored_filename)
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
            file_size = len(content)
        
        # 创建文件记录
        new_file = GroupChatFile(
            group_id=group_id,
            original_name=file.filename,
            file_name=stored_filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file.content_type,
            uploaded_by_type='user',
            uploaded_by_id=str(current_user.id),
            uploaded_by_name=current_user.get_display_name()
        )
        
        db.add(new_file)
        
        # 创建文件分享消息
        file_message = GroupChatMessage(
            group_id=group_id,
            sender_type='user',
            sender_id=str(current_user.id),
            sender_name=current_user.get_display_name(),
            content=f'分享了文件: {file.filename}',
            message_type='file',
            metadata={
                'file_id': new_file.file_id,
                'file_name': file.filename,
                'file_size': file_size,
                'file_type': file.content_type
            }
        )
        
        db.add(file_message)
        new_file.message_id = file_message.message_id
        
        # 更新统计
        group.file_count += 1
        group.message_count += 1
        group.last_message_at = datetime.now()
        
        # 如果启用自动保存，同时保存到用户空间
        if group.auto_save_files:
            user_storage_path = os.path.join(config.storage_dir, "users", str(current_user.id), "files")
            os.makedirs(user_storage_path, exist_ok=True)
            
            user_file_path = os.path.join(user_storage_path, stored_filename)
            with open(user_file_path, "wb") as user_buffer:
                user_buffer.write(content)
        
        db.commit()
        
        return {
            "success": True,
            "message": "文件上传成功",
            "data": new_file.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

@group_chat.get("/{group_id}/files", summary="获取群聊文件列表")
async def get_group_files(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取群聊文件列表"""
    try:
        # 验证权限
        member = db.query(GroupChatMember).filter(
            GroupChatMember.group_id == group_id,
            GroupChatMember.member_type == 'user',
            GroupChatMember.member_id == str(current_user.id),
            GroupChatMember.is_active == True
        ).first()
        
        if not member:
            raise HTTPException(status_code=403, detail="无权限访问此群聊文件")
        
        # 获取文件列表
        files = db.query(GroupChatFile).filter(
            GroupChatFile.group_id == group_id,
            GroupChatFile.is_public == True
        ).order_by(GroupChatFile.created_at.desc()).all()
        
        files_data = [file.to_dict() for file in files]
        
        return {
            "success": True,
            "data": files_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}") 