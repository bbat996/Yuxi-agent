from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from db_manager import db_manager
from models.site_config_model import SiteConfig
from models.user_model import User
from utils.auth_middleware import get_db, get_superadmin_user

# 创建路由器
site_config = APIRouter(prefix="/site-config", tags=["site-config"])

# 请求和响应模型
class ConfigUpdate(BaseModel):
    config_key: str
    config_value: str

class ConfigBatchUpdate(BaseModel):
    configs: List[ConfigUpdate]

class ConfigResponse(BaseModel):
    id: int
    config_key: str
    config_value: str
    config_type: str
    description: str
    category: str
    is_system: bool
    is_public: bool

@site_config.get("/", summary="获取所有网站配置")
async def get_site_configs(
    category: Optional[str] = None,
    public_only: bool = False,
    current_user: User = Depends(get_superadmin_user),
    db: Session = Depends(get_db)
):
    """获取网站配置列表"""
    try:
        query = db.query(SiteConfig)
        
        if category:
            query = query.filter(SiteConfig.category == category)
        
        if public_only:
            query = query.filter(SiteConfig.is_public == True)
        
        configs = query.all()
        
        # 将配置转换为字典格式，方便前端使用
        config_dict = {}
        config_list = []
        
        for config in configs:
            config_dict[config.config_key] = config.get_typed_value()
            config_list.append(config.to_dict())
        
        return {
            "success": True,
            "data": {
                "configs": config_dict,
                "config_list": config_list
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取网站配置失败: {str(e)}")

@site_config.get("/public", summary="获取公开的网站配置")
async def get_public_configs(db: Session = Depends(get_db)):
    """获取公开的网站配置（无需认证）"""
    try:
        configs = db.query(SiteConfig).filter(SiteConfig.is_public == True).all()
        
        config_dict = {}
        for config in configs:
            config_dict[config.config_key] = config.get_typed_value()
        
        return {
            "success": True,
            "data": config_dict
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取公开配置失败: {str(e)}")

@site_config.put("/{config_key}", summary="更新单个网站配置")
async def update_site_config(
    config_key: str,
    config_update: ConfigUpdate,
    current_user: User = Depends(get_superadmin_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """更新单个网站配置"""
    try:
        config = db.query(SiteConfig).filter(SiteConfig.config_key == config_key).first()
        
        if not config:
            raise HTTPException(status_code=404, detail=f"配置 {config_key} 不存在")
        
        # 更新配置值
        config.config_value = config_update.config_value
        config.updated_at = datetime.now()
        
        db.commit()
        
        return {
            "success": True,
            "message": f"配置 {config_key} 更新成功",
            "data": config.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")

@site_config.put("/batch", summary="批量更新网站配置")
async def batch_update_configs(
    config_batch: ConfigBatchUpdate,
    current_user: User = Depends(get_superadmin_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """批量更新网站配置"""
    try:
        updated_configs = []
        
        for config_update in config_batch.configs:
            config = db.query(SiteConfig).filter(
                SiteConfig.config_key == config_update.config_key
            ).first()
            
            if config:
                config.config_value = config_update.config_value
                config.updated_at = datetime.now()
                updated_configs.append(config.config_key)
        
        db.commit()
        
        return {
            "success": True,
            "message": f"成功更新 {len(updated_configs)} 个配置",
            "data": {
                "updated_configs": updated_configs
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量更新配置失败: {str(e)}")

@site_config.post("/initialize", summary="初始化默认网站配置")
async def initialize_site_configs(
    current_user: User = Depends(get_superadmin_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """初始化默认网站配置"""
    try:
        # 获取默认配置
        default_configs = SiteConfig.get_default_configs()
        
        created_count = 0
        updated_count = 0
        
        for config_data in default_configs:
            existing_config = db.query(SiteConfig).filter(
                SiteConfig.config_key == config_data["config_key"]
            ).first()
            
            if existing_config:
                # 如果配置已存在，只更新非值字段
                existing_config.description = config_data["description"]
                existing_config.category = config_data["category"]
                existing_config.config_type = config_data["config_type"]
                existing_config.updated_at = datetime.now()
                updated_count += 1
            else:
                # 创建新配置
                new_config = SiteConfig(**config_data)
                db.add(new_config)
                created_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": f"配置初始化完成：创建 {created_count} 个，更新 {updated_count} 个",
            "data": {
                "created": created_count,
                "updated": updated_count
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"初始化配置失败: {str(e)}")

@site_config.delete("/{config_key}", summary="删除网站配置")
async def delete_site_config(
    config_key: str,
    current_user: User = Depends(get_superadmin_user),
    db: Session = Depends(get_db)
):
    """删除网站配置（仅限非系统配置）"""
    try:
        config = db.query(SiteConfig).filter(SiteConfig.config_key == config_key).first()
        
        if not config:
            raise HTTPException(status_code=404, detail=f"配置 {config_key} 不存在")
        
        if config.is_system:
            raise HTTPException(status_code=400, detail="系统配置不能删除")
        
        db.delete(config)
        db.commit()
        
        return {
            "success": True,
            "message": f"配置 {config_key} 删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除配置失败: {str(e)}")

@site_config.get("/categories", summary="获取配置分类")
async def get_config_categories(
    current_user: User = Depends(get_superadmin_user),
    db: Session = Depends(get_db)
):
    """获取所有配置分类"""
    try:
        categories = db.query(SiteConfig.category).distinct().all()
        category_list = [cat[0] for cat in categories]
        
        return {
            "success": True,
            "data": category_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置分类失败: {str(e)}") 