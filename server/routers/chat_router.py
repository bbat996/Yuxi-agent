import os
import json
import asyncio
import traceback
import uuid
import time
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessageChunk, HumanMessage
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src import executor, config
from src.core import HistoryManager
from src.agents.agent_manager import agent_manager
from src.models import select_model
from src.utils.logging_config import logger
from src.agents.tools_factory import get_all_tools
from routers.auth_router import get_admin_user
from utils.auth_middleware import get_required_user, get_db
from models.user_model import User
from models.thread_model import Thread

chat = APIRouter(prefix="/chat", tags=["chat"])





@chat.get("/")
async def chat_get(current_user: User = Depends(get_required_user)):
    """聊天服务健康检查（需要登录）"""
    return "Chat Get!"


@chat.post("/call")
async def call(query: str = Body(...), meta: dict = Body(None), current_user: User = Depends(get_required_user)):
    """调用模型进行简单问答（需要登录）"""
    meta = meta or {}
    model = select_model(model_provider=meta.get("model_provider"), model_name=meta.get("model_name"))

    async def predict_async(query):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, model.predict, query)

    response = await predict_async(query)
    logger.debug({"query": query, "response": response.content})

    return {"response": response.content}


@chat.get("/agent")
async def get_agent(current_user: User = Depends(get_required_user)):
    """获取当前用户可用的所有智能体（自己创建的+公开的）"""
    agent_list = agent_manager.get_agents_by_user(current_user.id)
    return {"agents": agent_list}


@chat.post("/agent/{agent_name}")
async def chat_agent(
    agent_name: str,
    query: str = Body(...),
    config: dict = Body({}),
    meta: dict = Body({}),
    current_user: User = Depends(get_required_user),
):
    """使用特定智能体进行对话（需要登录）"""

    meta.update(
        {
            "query": query,
            "agent_name": agent_name,
            "server_model_name": config.get("model", agent_name),
            "thread_id": config.get("thread_id"),
            "user_id": current_user.id,
        }
    )

    # 将meta和thread_id整合到config中
    def make_chunk(content=None, **kwargs):

        return json.dumps({"request_id": meta.get("request_id"), "response": content, **kwargs}, ensure_ascii=False).encode("utf-8") + b"\n"

    async def stream_messages():

        # 代表服务端已经收到了请求
        yield make_chunk(status="init", meta=meta, msg=HumanMessage(content=query).model_dump())

        # 尝试获取智能体（预定义或自定义）
        agent = agent_manager.get_agent_by_identifier(agent_name)

        messages = [{"role": "user", "content": query}]

        # 构造运行时配置，如果没有thread_id则生成一个
        config["user_id"] = current_user.id
        if "thread_id" not in config or not config["thread_id"]:
            config["thread_id"] = str(uuid.uuid4())
            logger.debug(f"没有thread_id，生成一个: {config['thread_id']=}")

        runnable_config = {"configurable": {**config}}

        async for msg, metadata in agent.stream_messages(messages, config_schema=runnable_config):
            # logger.debug(f"msg: {msg.model_dump()}, metadata: {metadata}")
            if isinstance(msg, AIMessageChunk):
                yield make_chunk(content=msg.content, msg=msg.model_dump(), metadata=metadata, status="loading")
            else:
                yield make_chunk(msg=msg.model_dump(), metadata=metadata, status="loading")

        yield make_chunk(status="finished", meta=meta)

    return StreamingResponse(stream_messages(), media_type="application/json")


@chat.get("/tools")
async def get_tools(current_user: User = Depends(get_admin_user)):
    """获取所有可用工具（需要登录）"""
    return {"tools": list(get_all_tools().keys())}


@chat.post("/agent/{agent_name}/config")
async def save_agent_config(agent_name: str, config: dict = Body(...), current_user: User = Depends(get_admin_user)):
    """保存智能体配置到YAML文件（需要管理员权限）"""
    # 获取Agent实例和配置类
    agent = agent_manager.get_agent_by_identifier(agent_name)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"智能体 {agent_name} 不存在")

    # 使用配置类的save_to_file方法保存配置
    config_cls = agent.config_schema
    result = config_cls.save_to_file(config, agent_name)

    if result:
        return {"success": True, "message": f"智能体 {agent_name} 配置已保存"}
    else:
        raise HTTPException(status_code=500, detail="保存智能体配置失败")


@chat.get("/agent/{agent_name}/history")
async def get_agent_history(agent_name: str, thread_id: str, current_user: User = Depends(get_required_user)):
    """获取智能体历史消息（需要登录）"""
    # 获取Agent实例和配置类
    agent = agent_manager.get_agent_by_identifier(agent_name)
    # 获取历史消息
    history = await agent.get_history(user_id=current_user.id, thread_id=thread_id)
    return {"history": history}


@chat.get("/agent/{agent_name}/config")
async def get_agent_config(agent_name: str, current_user: User = Depends(get_required_user)):
    """从YAML文件加载智能体配置（需要登录）"""
    # 检查智能体是否存在
    agent = agent_manager.get_agent_by_identifier(agent_name)

    config_data = agent.config_schema.from_runnable_config(config={}, agent_name=agent_name)
    return {"success": True, "config": config_data}


# ==================== 线程管理 API ====================


class ThreadCreate(BaseModel):
    title: str | None = None
    agent_id: str
    description: str | None = None
    metadata: dict | None = None


class ThreadResponse(BaseModel):
    id: str
    user_id: str
    agent_id: str
    title: str | None = None
    description: str | None = None
    create_at: str
    update_at: str


@chat.post("/thread", response_model=ThreadResponse)
async def create_thread(thread: ThreadCreate, db: Session = Depends(get_db), current_user: User = Depends(get_required_user)):
    """创建新对话线程"""
    thread_id = str(uuid.uuid4())

    new_thread = Thread(
        id=thread_id,
        user_id=current_user.id,
        agent_id=thread.agent_id,
        title=thread.title or "新对话",
        description=thread.description,
    )

    db.add(new_thread)
    db.commit()
    db.refresh(new_thread)

    return {
        "id": new_thread.id,
        "user_id": new_thread.user_id,
        "agent_id": new_thread.agent_id,
        "title": new_thread.title,
        "description": new_thread.description,
        "create_at": new_thread.create_at.isoformat(),
        "update_at": new_thread.update_at.isoformat(),
    }


@chat.get("/threads", response_model=list[ThreadResponse])
async def list_threads(agent_id: str | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_required_user)):
    """获取用户的所有对话线程"""
    query = db.query(Thread).filter(Thread.user_id == current_user.id, Thread.status == 1)

    if agent_id:
        query = query.filter(Thread.agent_id == agent_id)

    threads = query.order_by(Thread.update_at.desc()).all()

    return [
        {
            "id": thread.id,
            "user_id": thread.user_id,
            "agent_id": thread.agent_id,
            "title": thread.title,
            "description": thread.description,
            "create_at": thread.create_at.isoformat(),
            "update_at": thread.update_at.isoformat(),
        }
        for thread in threads
    ]


@chat.delete("/thread/{thread_id}")
async def delete_thread(thread_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_required_user)):
    """删除对话线程"""
    thread = db.query(Thread).filter(Thread.id == thread_id, Thread.user_id == current_user.id).first()

    if not thread:
        raise HTTPException(status_code=404, detail="对话线程不存在")

    # 软删除
    thread.status = 0
    db.commit()

    return {"message": "删除成功"}


class ThreadUpdate(BaseModel):
    title: str | None = None
    description: str | None = None


@chat.put("/thread/{thread_id}", response_model=ThreadResponse)
async def update_thread(
    thread_id: str,
    thread_update: ThreadUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_required_user),
):
    """更新对话线程信息"""
    thread = db.query(Thread).filter(Thread.id == thread_id, Thread.user_id == current_user.id, Thread.status == 1).first()

    if not thread:
        raise HTTPException(status_code=404, detail="对话线程不存在")

    if thread_update.title is not None:
        thread.title = thread_update.title

    if thread_update.description is not None:
        thread.description = thread_update.description

    db.commit()
    db.refresh(thread)

    return {
        "id": thread.id,
        "user_id": thread.user_id,
        "agent_id": thread.agent_id,
        "title": thread.title,
        "description": thread.description,
        "create_at": thread.create_at.isoformat(),
        "update_at": thread.update_at.isoformat(),
    }
