from fastapi import APIRouter
from routers.chat_router import chat
from routers.data_router import data
from routers.base_router import base
from routers.auth_router import auth
from routers.agent_router import agent_router
from routers.model_router import model_router
from routers.mcp_router import mcp_router
from routers.prompt_router import prompt_router
from routers.site_config_router import site_config
from routers.group_chat_router import group_chat
# from routers.graph_router import graph

router = APIRouter()
router.include_router(base)
router.include_router(chat)
router.include_router(data)
router.include_router(auth)
router.include_router(agent_router)
router.include_router(model_router)
router.include_router(mcp_router)
router.include_router(prompt_router)
router.include_router(site_config)
router.include_router(group_chat)
# router.include_router(graph)
