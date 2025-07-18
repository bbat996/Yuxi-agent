from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from db_manager import db_manager
from models.user_model import User, OperationLog
from utils.auth_utils import AuthUtils
from utils.auth_middleware import get_db, get_current_user, get_admin_user, get_superadmin_user, oauth2_scheme

# 创建路由器
auth = APIRouter(prefix="/auth", tags=["auth"])

# 请求和响应模型
class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
    role: str

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "user"

class UserUpdate(BaseModel):
    username: str | None = None
    password: str | None = None
    role: str | None = None

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    created_at: str
    last_login: str | None = None

class InitializeAdmin(BaseModel):
    username: str
    password: str

# 记录操作日志
def log_operation(db: Session, user_id: int, operation: str, details: str = None, request: Request = None):
    ip_address = None
    if request:
        ip_address = request.client.host if request.client else None

    log = OperationLog(
        user_id=user_id,
        operation=operation,
        details=details,
        ip_address=ip_address
    )
    db.add(log)
    db.commit()

# 路由：登录获取令牌
@auth.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # 查找用户
    user = db.query(User).filter(User.username == form_data.username).first()

    # 验证用户存在且密码正确
    if not user or not AuthUtils.verify_password(user.password_hash, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 更新最后登录时间
    user.last_login = datetime.now()
    db.commit()

    # 生成访问令牌
    token_data = {"sub": str(user.id)}
    access_token = AuthUtils.create_access_token(token_data)

    # 记录登录操作
    log_operation(db, user.id, "登录")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "role": user.role
    }

# 路由：校验是否需要初始化管理员
@auth.get("/check-first-run")
async def check_first_run():
    is_first_run = db_manager.check_first_run()
    return {"first_run": is_first_run}

# 路由：初始化管理员账户
@auth.post("/initialize", response_model=Token)
async def initialize_admin(
    admin_data: InitializeAdmin,
    db: Session = Depends(get_db)
):
    # 检查是否是首次运行
    if not db_manager.check_first_run():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="系统已经初始化，无法再次创建初始管理员",
        )

    # 创建管理员账户
    hashed_password = AuthUtils.hash_password(admin_data.password)

    new_admin = User(
        username=admin_data.username,
        password_hash=hashed_password,
        role="superadmin",
        last_login=datetime.now()
    )

    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    # 生成访问令牌
    token_data = {"sub": str(new_admin.id)}
    access_token = AuthUtils.create_access_token(token_data)

    # 记录操作
    log_operation(db, new_admin.id, "系统初始化", "创建超级管理员账户")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": new_admin.id,
        "username": new_admin.username,
        "role": new_admin.role
    }

# 路由：获取当前用户信息
@auth.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user.to_dict()

# 路由：创建新用户（管理员权限）
@auth.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    request: Request,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )

    # 创建新用户
    hashed_password = AuthUtils.hash_password(user_data.password)

    # 检查角色权限
    # 超级管理员可以创建任何类型的用户
    if user_data.role == "superadmin" and current_user.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有超级管理员才能创建超级管理员账户",
        )

    # 管理员只能创建普通用户
    if current_user.role == "admin" and user_data.role != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理员只能创建普通用户账户",
        )

    new_user = User(
        username=user_data.username,
        password_hash=hashed_password,
        role=user_data.role
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 记录操作
    log_operation(
        db,
        current_user.id,
        "创建用户",
        f"创建用户: {user_data.username}, 角色: {user_data.role}",
        request
    )

    return new_user.to_dict()

# 路由：获取所有用户（管理员权限）
@auth.get("/users", response_model=list[UserResponse])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    users = db.query(User).offset(skip).limit(limit).all()
    return [user.to_dict() for user in users]

# 路由：获取特定用户信息（管理员权限）
@auth.get("/users/{user_id}", response_model=UserResponse)
async def read_user(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )
    return user.to_dict()

# 路由：更新用户信息（管理员权限）
@auth.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    request: Request,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    # 检查权限
    if user.role == "superadmin" and current_user.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有超级管理员才能修改超级管理员账户",
        )

    # 超级管理员账户不能被降级（只能由其他超级管理员修改）
    if user.role == "superadmin" and user_data.role and user_data.role != "superadmin" and current_user.id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="不能降级超级管理员账户",
        )

    # 更新信息
    update_details = []

    if user_data.username is not None:
        # 检查用户名是否已被其他用户使用
        existing_user = db.query(User).filter(User.username == user_data.username, User.id != user_id).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在",
            )
        user.username = user_data.username
        update_details.append(f"用户名: {user_data.username}")

    if user_data.password is not None:
        user.password_hash = AuthUtils.hash_password(user_data.password)
        update_details.append("密码已更新")

    if user_data.role is not None:
        user.role = user_data.role
        update_details.append(f"角色: {user_data.role}")

    db.commit()

    # 记录操作
    log_operation(
        db,
        current_user.id,
        "更新用户",
        f"更新用户ID {user_id}: {', '.join(update_details)}",
        request
    )

    return user.to_dict()

# 路由：删除用户（管理员权限）
@auth.delete("/users/{user_id}", response_model=dict)
async def delete_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    # 检查权限
    if user.role == "superadmin":
        # 只有超级管理员可以删除超级管理员
        if current_user.role != "superadmin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有超级管理员才能删除超级管理员账户",
            )

        # 检查是否是最后一个超级管理员
        superadmin_count = db.query(User).filter(User.role == "superadmin").count()
        if superadmin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除最后一个超级管理员账户",
            )

    # 不能删除自己的账户
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己的账户",
        )

    # 记录操作
    log_operation(
        db,
        current_user.id,
        "删除用户",
        f"删除用户: {user.username}, ID: {user.id}, 角色: {user.role}",
        request
    )

    # 删除用户
    db.delete(user)
    db.commit()

    return {"success": True, "message": "用户已删除"}


# ===== 个人信息管理相关API =====

class ProfileUpdate(BaseModel):
    display_name: str | None = None
    email: str | None = None
    avatar: str | None = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

@auth.get("/profile", summary="获取个人信息")
async def get_profile(current_user: User = Depends(get_current_user)):
    """获取当前用户的个人信息"""
    return {
        "success": True,
        "data": {
            "id": current_user.id,
            "username": current_user.username,
            "display_name": current_user.display_name,
            "email": current_user.email,
            "avatar": current_user.avatar,
            "role": current_user.role,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
            "updated_at": current_user.updated_at.isoformat() if current_user.updated_at else None
        }
    }

@auth.put("/profile", summary="更新个人信息")
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """更新当前用户的个人信息"""
    try:
        # 更新字段
        if profile_data.display_name is not None:
            current_user.display_name = profile_data.display_name
        if profile_data.email is not None:
            current_user.email = profile_data.email
        if profile_data.avatar is not None:
            current_user.avatar = profile_data.avatar
        
        # 更新时间戳
        current_user.updated_at = datetime.now()
        
        db.commit()
        
        # 记录操作日志
        log_operation(
            db,
            current_user.id,
            "profile_update",
            f"更新个人信息: {profile_data.model_dump_json()}",
            request
        )
        
        return {
            "success": True,
            "message": "个人信息更新成功",
            "data": {
                "id": current_user.id,
                "username": current_user.username,
                "display_name": current_user.display_name,
                "email": current_user.email,
                "avatar": current_user.avatar,
                "role": current_user.role,
                "updated_at": current_user.updated_at.isoformat()
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新个人信息失败: {str(e)}")

@auth.post("/change-password", summary="修改密码")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """修改当前用户密码"""
    try:
        # 验证当前密码
        if not AuthUtils.verify_password(password_data.current_password, current_user.password_hash):
            raise HTTPException(status_code=400, detail="当前密码不正确")
        
        # 更新密码
        current_user.password_hash = AuthUtils.hash_password(password_data.new_password)
        current_user.updated_at = datetime.now()
        
        db.commit()
        
        # 记录操作日志
        log_operation(
            db,
            current_user.id,
            "password_change",
            "修改密码",
            request
        )
        
        return {"success": True, "message": "密码修改成功"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"修改密码失败: {str(e)}")

@auth.get("/profile/stats", summary="获取个人统计信息")
async def get_profile_stats(current_user: User = Depends(get_current_user)):
    """获取当前用户的统计信息"""
    return {
        "success": True,
        "data": {
            "total_messages": current_user.total_messages or 0,
            "total_tokens": current_user.total_tokens or 0,
            "total_chats": current_user.total_chats or 0,
            "file_storage_used": current_user.file_storage_used or 0,
            "file_storage_used_mb": current_user.get_storage_used_mb(),
            "account_age_days": (datetime.now() - current_user.created_at).days if current_user.created_at else 0
        }
    }

@auth.get("/profile/file-storage", summary="获取个人文件存储信息")
async def get_file_storage_info(current_user: User = Depends(get_current_user)):
    """获取当前用户的文件存储信息"""
    import os
    from config.app_config import config
    
    # 构建用户文件存储路径
    user_storage_path = os.path.join(config.storage_dir, "users", str(current_user.id))
    
    # 计算实际使用的存储空间
    actual_used = 0
    if os.path.exists(user_storage_path):
        for root, dirs, files in os.walk(user_storage_path):
            actual_used += sum(os.path.getsize(os.path.join(root, file)) for file in files)
    
    # 更新数据库中的存储使用量（如果有差异）
    if abs(actual_used - (current_user.file_storage_used or 0)) > 1024:  # 差异超过1KB才更新
        from db_manager import db_manager
        with db_manager.get_session_context() as db:
            db_user = db.query(User).filter(User.id == current_user.id).first()
            if db_user:
                db_user.file_storage_used = actual_used
                db.commit()
    
    return {
        "success": True,
        "data": {
            "storage_path": user_storage_path,
            "used_bytes": actual_used,
            "used_mb": round(actual_used / (1024 * 1024), 2),
            "limit_mb": 1024,  # 默认限制1GB，可以配置
            "usage_percentage": round((actual_used / (1024 * 1024 * 1024)) * 100, 2)  # 基于1GB限制的百分比
        }
    }
