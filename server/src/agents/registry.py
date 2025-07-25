from __future__ import annotations

import os
import yaml
import uuid
from pathlib import Path
from typing import Annotated, TypedDict
from abc import abstractmethod
from dataclasses import dataclass, fields, field, asdict

from langchain_core.runnables import RunnableConfig
from langchain_core.messages import BaseMessage
from langgraph.graph.state import CompiledStateGraph
from langgraph.graph.message import add_messages

from config import PROJECT_DIR
from src.utils import logger


class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


@dataclass(kw_only=True)
class Configuration(dict):
    """
    定义一个基础 Configuration 供 各类 graph 继承

    配置优先级:
    1. 运行时配置(RunnableConfig)：最高优先级，直接从函数参数传入
    2. 文件配置(config.private.yaml)：中等优先级，从文件加载
    3. 类默认配置：最低优先级，类中定义的默认值
    """
    config_file_path = Path(f"{PROJECT_DIR}/server/config/agents/chatbot.private.yaml")
    

    @classmethod
    def from_runnable_config(cls, config: RunnableConfig | None = None, agent_name: str | None = None) -> Configuration:
        """Create a Configuration instance from a RunnableConfig object.

        Args:
            config: RunnableConfig object with highest priority
            agent_name: Name of the agent to load config file for

        Returns:
            Configuration instance with merged config values
        """
        from dataclasses import is_dataclass
        # 获取类默认配置：创建一个实例获取所有默认值
        instance = cls()
        # 获取所有字段，包括子类和所有 dataclass 父类的字段
        _fields = set()
        for base in cls.__mro__:
            if is_dataclass(base):
                _fields.update({f.name for f in fields(base) if f.init})

        # 尝试加载文件配置(中等优先级)
        file_config = {}
        if agent_name:
            file_config = cls.from_file(agent_name)

        # 获取运行时配置(最高优先级)
        configurable = (config.get("configurable") or {}) if config else {}

        # 合并三级配置，注意优先级
        merged_config = {}
        for config_field in _fields:
            # 1. 默认使用类默认值
            if hasattr(instance, config_field):
                merged_config[config_field] = getattr(instance, config_field)

            # 2. 如果文件配置中有此字段，则覆盖（文件配置优先级高于类默认值）
            if config_field in file_config:
                merged_config[config_field] = file_config[config_field]

            # 3. 如果运行时配置中有此字段，则覆盖（运行时配置优先级最高）
            if config_field in configurable:
                merged_config[config_field] = configurable[config_field]

        # 创建并返回配置实例
        logger.debug(f"最终合并配置: {merged_config}")
        return cls(**merged_config)

    @classmethod
    def from_file(cls, agent_name: str) -> Configuration:
        """从文件加载配置"""
        file_config = {}
        if os.path.exists(cls.config_file_path):
            try:
                with open(cls.config_file_path, encoding="utf-8") as f:
                    file_config = yaml.safe_load(f) or {}
            except Exception as e:
                logger.error(f"加载智能体配置文件出错: {e}")

        return file_config

    @classmethod
    def save_to_file(cls, config: dict, agent_name: str) -> bool:
        """Save configuration to a YAML file

        Args:
            config: Configuration dictionary to save
            agent_name: Name of the agent to save config for

        Returns:
            True if saving was successful, False otherwise
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(cls.config_file_path), exist_ok=True)
            with open(cls.config_file_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, indent=2, allow_unicode=True)

            # logger.info(f"智能体 {agent_name} 配置已保存到 {config_file_path}")
            return True
        except Exception as e:
            logger.error(f"保存智能体配置文件出错: {e}")
            return False

    def to_dict(self):
        return asdict(self)

    thread_id: str = field(
        default_factory=lambda: str(uuid.uuid4()),
        metadata={"name": "线程ID", "configurable": False, "description": "用来描述智能体的角色和行为"},
    )

    user_id: str = field(
        default_factory=lambda: str(uuid.uuid4()),
        metadata={"name": "用户ID", "configurable": False, "description": "用来描述智能体的角色和行为"},
    )


class BaseAgent:
    """
    定义一个基础 Agent 供 各类 graph 继承
    """

    name = "base_agent"
    description = "base_agent"
    config_schema: Configuration = Configuration
    requirements: list[str]

    def __init__(self, **kwargs):
        self.check_requirements()

    async def get_info(self):
        return {
            "name": self.name if hasattr(self, "name") else "Unknown",
            "description": self.description if hasattr(self, "description") else "Unknown",
            "config_schema": self.config_schema.to_dict(),
            "requirements": self.requirements if hasattr(self, "requirements") else [],
            "all_tools": self.all_tools if hasattr(self, "all_tools") else [],
            "has_checkpointer": await self.check_checkpointer(),
            "met_requirements": self.check_requirements(),
        }

    def check_requirements(self):
        if not hasattr(self, "requirements") or not self.requirements:
            return True
        for requirement in self.requirements:
            if requirement not in os.environ:
                raise ValueError(f"没有配置{requirement} 环境变量，请在 server/.env 文件中配置，并重新启动服务")
        return True

    async def stream_values(self, messages: list[str], config_schema: RunnableConfig = None, **kwargs):
        graph = await self.get_graph()
        logger.debug(f"stream_values: {config_schema}")
        for event in graph.astream({"messages": messages}, stream_mode="values", config=config_schema):
            yield event["messages"]

    async def stream_messages(self, messages: list[str], config_schema: RunnableConfig = None, **kwargs):
        graph = await self.get_graph()
        logger.debug(f"stream_messages: {config_schema}")

        async for msg, metadata in graph.astream({"messages": messages}, stream_mode="messages", config=config_schema):
            yield msg, metadata

    async def check_checkpointer(self):
        app = await self.get_graph()
        if not hasattr(app, "checkpointer") or app.checkpointer is None:
            logger.warning(f"智能体 {self.name} 的 Graph 未配置 checkpointer，无法获取历史记录")
            return False
        return True

    async def get_history(self, user_id, thread_id) -> list[dict]:
        """获取历史消息"""
        try:
            app = await self.get_graph()

            if not await self.check_checkpointer():
                return []

            config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}
            state = await app.aget_state(config)

            result = []
            if state:
                messages = state.values.get("messages", [])
                for msg in messages:
                    if hasattr(msg, "model_dump"):
                        msg_dict = msg.model_dump()  # 转换成字典
                    else:
                        msg_dict = dict(msg) if hasattr(msg, "__dict__") else {"content": str(msg)}
                    result.append(msg_dict)

            return result

        except Exception as e:
            logger.error(f"获取智能体 {self.name} 历史消息出错: {e}")
            return []

    @abstractmethod
    async def get_graph(self, **kwargs) -> CompiledStateGraph:
        """
        获取并编译对话图实例。
        必须确保在编译时设置 checkpointer，否则将无法获取历史记录。
        例如: graph = workflow.compile(checkpointer=sqlite_checkpointer)
        """
        pass
