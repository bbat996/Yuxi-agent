import os
import yaml
from pathlib import Path
from fastapi import Request, Body, Depends, HTTPException
from fastapi import APIRouter

from server.config import CONFIG_PATH
from server.src import config, knowledge_base, graph_base
from server.utils.auth_middleware import get_admin_user, get_superadmin_user
from server.models.user_model import User
from server.src.utils.logging_config import logger


base = APIRouter(tags=["base"])


def load_info_config():
    """加载信息配置文件"""
    # 配置文件路径
    config_path = Path(f"{CONFIG_PATH}/info.local.yaml")
    # 读取配置文件
    with open(config_path, encoding="utf-8") as file:
        config = yaml.safe_load(file)

    return config


@base.get("/")
async def route_index():
    return {"message": "You Got It!"}


@base.get("/health")
async def health_check():
    """简单的健康检查接口"""
    return {"status": "ok", "message": "服务正常运行"}


@base.get("/config")
def get_config(current_user: User = Depends(get_admin_user)):
    return config.dump_config()


@base.post("/config")
async def update_config(key=Body(...), value=Body(...), current_user: User = Depends(get_admin_user)) -> dict:
    config[key] = value
    config.save()
    return config.dump_config()


@base.post("/config/update")
async def update_config_item(items: dict = Body(...), current_user: User = Depends(get_admin_user)) -> dict:
    config.update(items)
    config.save()
    return config.dump_config()


@base.post("/restart")
async def restart(current_user: User = Depends(get_superadmin_user)):
    # graph_base.start()
    return {"message": "Restarted!"}


@base.get("/log")
def get_log(current_user: User = Depends(get_admin_user)):
    from server.src.utils.logging_config import LOG_FILE
    from collections import deque

    with open(LOG_FILE, encoding="utf-8") as f:
        last_lines = deque(f, maxlen=1000)

    log = "".join(last_lines)
    return {"log": log, "message": "success", "log_file": LOG_FILE}


@base.get("/info")
async def get_info_config():
    """获取系统信息配置（公开接口，无需认证）"""
    try:
        config = load_info_config()
        return {"success": True, "data": config}
    except Exception as e:
        logger.error(f"获取信息配置失败: {e}")
        raise HTTPException(status_code=500, detail="获取信息配置失败")


@base.get("/info/reload")
async def reload_info_config():
    """重新加载信息配置（管理员接口）"""
    # 注：这里暂时不添加权限验证，后续可以根据需要添加
    try:
        config = load_info_config()
        return {"success": True, "message": "配置重新加载成功", "data": config}
    except Exception as e:
        logger.error(f"重新加载信息配置失败: {e}")
        raise HTTPException(status_code=500, detail="重新加载信息配置失败")
