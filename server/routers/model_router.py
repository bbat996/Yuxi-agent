from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from src import config
from src.models import select_model
from src.utils.logging_config import logger
from routers.auth_router import get_admin_user
from utils.auth_middleware import get_required_user
from models.user_model import User

model_router = APIRouter(prefix="/model", tags=["model"])


@model_router.get("/models")
async def get_chat_models(model_provider: str, current_user: User = Depends(get_admin_user)):
    """获取指定模型提供商的模型列表（需要登录）"""
    model = select_model(model_provider=model_provider)
    return {"models": model.get_models()}


@model_router.post("/models/update")
async def update_chat_models(model_provider: str, model_names: list[str], current_user=Depends(get_admin_user)):
    """更新指定模型提供商的模型列表 (仅管理员)"""
    config.model_names[model_provider]["models"] = model_names
    config._save_models_to_file()
    return {"models": config.model_names[model_provider]["models"]}


@model_router.get("/provider/{provider}/config")
async def get_provider_config(provider: str, current_user: User = Depends(get_admin_user)):
    """获取指定模型提供商的配置信息（仅管理员）"""
    provider_config = config.get_provider_config(provider)
    return provider_config


@model_router.post("/provider/{provider}/config")
async def update_provider_config(
    provider: str, 
    config_data: dict = Body(...), 
    current_user: User = Depends(get_admin_user)
):
    """更新指定模型提供商的配置信息（仅管理员）"""
    config.update_provider_config(provider, config_data)
    return {
        "success": True,
        "message": f"模型提供商 {provider} 配置已更新",
        "config": config.get_provider_config(provider)
    }


@model_router.post("/provider/{provider}/models/add")
async def add_provider_model(
    provider: str, 
    model_name: str = Body(...), 
    current_user: User = Depends(get_admin_user)
):
    """为指定模型提供商添加模型（仅管理员）"""
    config.add_provider_model(provider, model_name)
    return {
        "success": True,
        "message": f"模型 {model_name} 已添加到 {provider}",
        "models": config.model_names[provider]["models"]
    }


@model_router.delete("/provider/{provider}/models/{model_name}")
async def remove_provider_model(
    provider: str, 
    model_name: str, 
    current_user: User = Depends(get_admin_user)
):
    """从指定模型提供商删除模型（仅管理员）"""
    config.remove_provider_model(provider, model_name)
    return {
        "success": True,
        "message": f"模型 {model_name} 已从 {provider} 中删除",
        "models": config.model_names[provider]["models"]
    }


@model_router.post("/provider/{provider}/test")
async def test_provider_connection(
    provider: str, 
    config_data: dict = Body(...), 
    current_user: User = Depends(get_admin_user)
):
    """测试模型提供商连接（仅管理员）"""
    if provider not in config.model_names:
        raise HTTPException(status_code=404, detail=f"模型提供商 {provider} 不存在")
    
    # 临时设置配置进行测试
    test_base_url = config_data.get("base_url", config.model_names[provider].get("base_url", ""))
    test_api_key = config_data.get("api_key", "")
    
    if not test_base_url or not test_api_key:
        raise HTTPException(status_code=400, detail="base_url 和 api_key 不能为空")
    
    # 创建临时模型实例进行测试
    from src.models.chat_model import OpenAIBase
    test_model = OpenAIBase(
        api_key=test_api_key,
        base_url=test_base_url,
        model_name="test-model"
    )
    
    # 尝试获取模型列表
    models = test_model.get_models()
    
    return {
        "success": True,
        "message": "连接测试成功",
        "models_count": len(models) if models else 0
    }


@model_router.post("/provider/{provider}/toggle")
async def toggle_provider_status(
    provider: str, 
    status_data: dict = Body(...), 
    current_user: User = Depends(get_admin_user)
):
    """切换模型提供商启用状态（仅管理员）"""
    if provider not in config.model_names:
        raise HTTPException(status_code=404, detail=f"模型提供商 {provider} 不存在")
    
    enabled = status_data.get("enabled")
    if enabled is None:
        raise HTTPException(status_code=400, detail="enabled 参数不能为空")
    
    try:
        config.toggle_provider_status(provider, enabled)
        return {
            "success": True,
            "message": f"模型提供商 {provider} 已{'启用' if enabled else '禁用'}",
            "provider": provider,
            "enabled": enabled
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"切换模型提供商状态失败: {e}")
        raise HTTPException(status_code=500, detail="切换模型提供商状态失败")
