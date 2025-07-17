import os
import traceback
from typing import Any, Dict, List
from pathlib import Path
import yaml
from dataclasses import dataclass, field
import asyncio

from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver, aiosqlite

from src import config as sys_config
from src.utils import logger
from src.agents.registry import State, BaseAgent, Configuration
from src.agents.utils import load_chat_model, get_cur_time_with_utc
from src.agents.tools_factory import get_all_tools
from db_manager import DBManager
from models.agent_models import CustomAgent as CustomAgentModel
from config.agent_config import AgentConfig, ModelConfig, KnowledgeConfig, McpConfig


class ChatbotConfiguration(Configuration):
    """使用 AgentConfig 的智能体配置类"""

    def __init__(self, agent_config: AgentConfig = None):
        from config.agent_config import AgentConfig as AC

        if agent_config is None:
            self.agent_config = AC()
        elif isinstance(agent_config, dict):
            self.agent_config = AC(**agent_config)
        else:
            self.agent_config = agent_config
        # 调用父类初始化，但不传递参数，避免冲突
        super().__init__()

    @classmethod
    def from_runnable_config(cls, config: dict = None, agent_name: str = None) -> "ChatbotConfiguration":
        """从可运行配置创建配置实例"""
        # 先创建实例
        instance = cls()
        from config.agent_config import ModelConfig, KnowledgeConfig, McpConfig, AgentConfig

        if config is not None:
            # 如果 config 已经是 AgentConfig 对象，直接使用
            if isinstance(config, AgentConfig):
                instance.agent_config = config
            else:
                # 过滤掉 configurable 等非 AgentConfig 字段
                agent_config_dict = {
                    k: v for k, v in config.items() if k not in ["configurable", "recursion_limit", "max_concurrency"]
                }
                # Ensure nested configs are correct types
                if "llm_config" in agent_config_dict and isinstance(agent_config_dict["llm_config"], dict):
                    agent_config_dict["llm_config"] = ModelConfig(**agent_config_dict["llm_config"])
                if "knowledge_config" in agent_config_dict and isinstance(agent_config_dict["knowledge_config"], dict):
                    agent_config_dict["knowledge_config"] = KnowledgeConfig(**agent_config_dict["knowledge_config"])
                if "mcp_config" in agent_config_dict and isinstance(agent_config_dict["mcp_config"], dict):
                    agent_config_dict["mcp_config"] = McpConfig(**agent_config_dict["mcp_config"])
                instance.agent_config = AgentConfig(**agent_config_dict)

                # 处理 configurable 中的字段，设置到 Configuration 基类
                configurable = config.get("configurable", {})
                for key, value in configurable.items():
                    if hasattr(instance, key):
                        setattr(instance, key, value)

        return instance

    @classmethod
    def from_db_record(cls, db_record) -> "ChatbotConfiguration":
        """从数据库记录创建配置"""
        # 使用数据库模型的to_chatbot_config方法
        if hasattr(db_record, "to_chatbot_config"):
            config_data = db_record.to_chatbot_config()
            agent_config = AgentConfig(**config_data)
        else:
            # 创建默认配置
            agent_config = AgentConfig()
            if hasattr(db_record, "name") and db_record.name:
                agent_config.name = db_record.name
            if hasattr(db_record, "description") and db_record.description:
                agent_config.description = db_record.description
            if hasattr(db_record, "system_prompt") and db_record.system_prompt:
                agent_config.system_prompt = db_record.system_prompt
            else:
                agent_config.system_prompt = ""

        return cls(agent_config)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return self.agent_config.model_dump()

    def __getattr__(self, name):
        """代理到 agent_config 的属性"""
        value = getattr(self.agent_config, name)
        if name == "llm_config":
            from config.agent_config import ModelConfig

            if isinstance(value, dict):
                return ModelConfig(**value)
        elif name == "knowledge_config":
            from config.agent_config import KnowledgeConfig

            if isinstance(value, dict):
                return KnowledgeConfig(**value)
        elif name == "mcp_config":
            from config.agent_config import McpConfig

            if isinstance(value, dict):
                return McpConfig(**value)
        return value

    def __setattr__(self, name, value):
        """设置属性"""
        if name == "agent_config":
            super().__setattr__(name, value)
        elif name in ["thread_id", "user_id"]:
            # 这些字段属于 Configuration 基类，设置到实例本身
            super().__setattr__(name, value)
        else:
            # 其他字段代理到 agent_config
            setattr(self.agent_config, name, value)


class ChatbotAgent(BaseAgent):
    """使用 AgentConfig 的 ChatbotAgent"""

    # 基础配置
    name: str = "chatbot"
    description: str = "基础的对话机器人，可以回答问题，默认不使用任何工具，可在配置中启用需要的工具。"
    agent_type: str = "chatbot"

    @classmethod
    async def create(cls, agent_id: str = None, config: dict = None, **kwargs) -> "ChatbotAgent":
        """异步工厂方法，用于创建和初始化ChatbotAgent实例"""
        agent = cls(agent_id=agent_id, config=config, **kwargs, _skip_init=True)
        await agent._ainitialize_llm_and_tools()
        return agent

    @classmethod
    def from_db_record(cls, db_record, agent_id: str = None, **kwargs) -> "ChatbotAgent":
        """从数据库记录创建ChatbotAgent实例（同步，可能不完全初始化）"""
        # 获取配置
        config = ChatbotConfiguration.from_db_record(db_record)

        # 创建实例
        agent_id = agent_id or getattr(db_record, "agent_id", None)
        # 注意：这里返回的实例可能没有完全初始化LLM和工具
        return cls(agent_id=agent_id, config=config.to_dict(), **kwargs)

    def __init__(self, agent_id: str = None, config: dict = None, _skip_init: bool = False, **kwargs):
        self.agent_id = agent_id or "chatbot"

        # 合并 YAML、外部 config、默认值
        if config is not None:
            self.config_schema = ChatbotConfiguration.from_runnable_config(config)
        else:
            self.config_schema = ChatbotConfiguration()

        # 从配置中获取名称和描述
        self.name = self.config_schema.name or "chatbot"
        self.description = (
            kwargs.get("description")
            or self.config_schema.description
            or "基础的对话机器人，可以回答问题，默认不使用任何工具，可在配置中启用需要的工具。"
        )

        # 初始化MCP连接配置
        self._init_mcp_connections()
        self.requirements = ["TAVILY_API_KEY", "ZHIPUAI_API_KEY"]
        self.workdir = Path(sys_config.storage_dir) / "agents" / self.name
        self.workdir.mkdir(parents=True, exist_ok=True)

        # 初始化模型和工具
        self.model = None
        self.tools = []
        self.llm_with_tools = None
        self.graph = None

        if not _skip_init:
            logger.warning("同步初始化 ChatbotAgent，MCP工具可能无法加载。请使用 ChatbotAgent.create() 异步初始化。")
            self._initialize_llm_and_tools()  # 同步版本，可能不完整
            logger.info(f"ChatbotAgent 同步初始化完成: {self.name}")

    async def _ainitialize_llm_and_tools(self):
        """异步初始化或重新初始化LLM、工具和绑定后的模型"""
        # 获取模型配置
        llm_config = self._get_llm_config()
        llm_parameters = self.config_schema.llm_config.config

        # 加载模型
        logger.info(f"开始加载模型: {llm_config.get('provider')}/{llm_config.get('model')}")
        self.model = load_chat_model(
            provider=llm_config.get("provider"), model=llm_config.get("model"), model_parameters=llm_parameters
        )
        logger.info("模型加载成功")

        # 获取工具
        tools_config = self.config_schema.tools
        mcp_skills_config = self.config_schema.mcp_config.servers if self.config_schema.mcp_config.enabled else []

        # 确保在 _aget_tools 之前，所有工具（包括知识库）已经被注册
        # 这里可以加一个预加载或检查的步骤
        get_all_tools()  # 确保知识库等工具已加载

        self.tools = await self._aget_tools(
            tools_config,
            mcp_skills_config,
        )

        logger.info("=== 工具配置 ===")
        if self.tools:
            tool_names = [getattr(tool, "name", str(tool)) for tool in self.tools]
            logger.info(f"可用工具: {', '.join(tool_names)}")
            self.llm_with_tools = self.model.bind_tools(self.tools)
        else:
            logger.info("无可用工具")
            self.llm_with_tools = self.model

    def _init_mcp_connections(self):
        """初始化MCP连接配置"""
        from src.agents.mcp_client import MCPClient

        mcp_config = self.config_schema.mcp_config
        if mcp_config.enabled and mcp_config.servers:
            # 将 servers 列表转换为配置格式
            mcp_skills_dict = {server: {} for server in mcp_config.servers}
            mcp_integration = MCPClient.get_instance()
            connections = mcp_integration.load_connections_from_config(mcp_skills_dict)
            if connections:
                mcp_integration.update_connections(connections)
                logger.info(f"智能体 {self.name} 加载了 {len(connections)} 个MCP技能配置")
        else:
            logger.info(f"智能体 {self.name} 未启用MCP技能")

    def reload_config(self):
        """重新加载配置"""
        # 清除图缓存，强制重新构建
        self.graph = None
        # 重新初始化MCP连接配置
        self._init_mcp_connections()
        # 重新初始化模型和工具
        # 注意：reload_config 是同步的，无法调用异步初始化
        # 如果需要完全重新加载，需要重新创建实例
        logger.warning("reload_config 是同步的，只会重新加载部分配置。如需完全重载，请重新创建 agent 实例。")
        self._initialize_llm_and_tools()
        logger.info(f"智能体配置重新加载完成: {self.name}")

    def _initialize_llm_and_tools(self):
        """同步初始化LLM和工具（不支持异步的MCP工具）"""
        # 获取模型配置
        llm_config = self._get_llm_config()
        llm_parameters = self.config_schema.llm_config.config

        # 加载模型
        logger.info(f"(同步) 开始加载模型: {llm_config.get('provider')}/{llm_config.get('model')}")
        self.model = load_chat_model(
            provider=llm_config.get("provider"), model=llm_config.get("model"), model_parameters=llm_parameters
        )
        logger.info("(同步) 模型加载成功")

        # 获取工具 (同步版本，跳过MCP)
        tools_config = self.config_schema.tools
        self.tools = asyncio.run(self._aget_tools(tools_config, []))  # 传入空的mcp_skills

        logger.info("=== (同步) 工具配置 ===")
        if self.tools:
            tool_names = [getattr(tool, "name", str(tool)) for tool in self.tools]
            logger.info(f"可用工具: {', '.join(tool_names)}")
            self.llm_with_tools = self.model.bind_tools(self.tools)
        else:
            logger.info("无可用工具")
            self.llm_with_tools = self.model

    async def _aget_tools(self, tools: List[str], mcp_skills: List[str] = None) -> List:
        """
        异步获取所有工具，包括函数工具和MCP技能。
        Args:
            tools: 内置工具列表
            mcp_skills: MCP技能列表（list of str）
        Returns:
            工具列表
        """
        result_tools = []
        platform_tools = get_all_tools()

        # 添加内置工具
        if tools and isinstance(tools, list):
            for tool_name in tools:
                if tool_name in platform_tools:
                    result_tools.append(platform_tools[tool_name])
                    logger.debug(f"添加内置工具: {tool_name}")

        # 添加知识库检索工具（从 config_schema 获取）
        knowledge_dbs = (
            self.config_schema.knowledge_config.databases if self.config_schema.knowledge_config.enabled else []
        )
        if knowledge_dbs:
            for db_id in knowledge_dbs:
                tool_name = f"retrieve_{db_id[:8]}"
                if tool_name in platform_tools:
                    result_tools.append(platform_tools[tool_name])
                    logger.debug(f"添加知识库工具: {tool_name}")

        # 添加MCP技能工具（支持list格式）
        if mcp_skills and isinstance(mcp_skills, list):
            from src.agents.mcp_client import MCPClient

            mcp_client = MCPClient.get_instance()
            mcp_tools = await mcp_client.get_mcp_tools_for_agent(mcp_skills)
            if isinstance(mcp_tools, list):
                result_tools.extend(mcp_tools)
                logger.debug(f"添加MCP工具: {len(mcp_tools)} 个")
        return result_tools

    def _get_llm_config(self) -> Dict[str, Any]:
        print("DEBUG: type of self.config_schema.llm_config:", type(self.config_schema.llm_config))
        provider = self.config_schema.llm_config.provider or "deepseek"
        model = self.config_schema.llm_config.model or "deepseek-chat"
        model_parameters = self.config_schema.llm_config.config or {}
        return {
            "provider": provider,
            "model": model,
            "config": model_parameters,
        }

    async def llm_call(self, state: State, config: RunnableConfig = None) -> Dict[str, Any]:
        """调用LLM模型"""
        # 合并配置：运行时配置可以覆盖默认配置
        final_config = self.config_schema.to_dict()
        if config and "configurable" in config:
            final_config.update(config["configurable"])

        # 构建系统提示词
        system_prompt = final_config.get("system_prompt", self.config_schema.system_prompt)
        system_prompt = f"{system_prompt} Now is {get_cur_time_with_utc()}"

        # 异步调用模型
        messages = [{"role": "system", "content": system_prompt}] + state["messages"]
        try:
            # 使用预先加载和绑定的模型与工具
            result = await self.llm_with_tools.ainvoke(messages)

            # 格式化打印结果
            logger.info("=== 模型调用成功 ===")
            logger.info(f"返回类型: {type(result).__name__}")

            # 检查是否有工具调用
            if hasattr(result, "tool_calls") and result.tool_calls:
                logger.info(f"工具调用数量: {len(result.tool_calls)}")
                logger.info(f"工具调用: {result.tool_calls}")
            else:
                logger.info("无工具调用")
                if hasattr(result, "content") and result.content:
                    logger.info(f"回复内容: {result.content[:200]}{'...' if len(result.content) > 200 else ''}")

            # 打印token使用情况
            if hasattr(result, "response_metadata") and result.response_metadata:
                token_usage = result.response_metadata.get("token_usage", {})
                if token_usage:
                    logger.info(f"Token使用: {token_usage}")
            return {"messages": [result]}
        except Exception as e:
            logger.error(f"模型调用失败: {e}")
            logger.error(f"错误详情: {traceback.format_exc()}")
            raise

    async def get_graph(self, config_schema: RunnableConfig = None, **kwargs):
        """构建执行图"""
        if self.graph is not None:
            return self.graph
        workflow = StateGraph(State, config_schema=self.config_schema)
        workflow.add_node("llm", self.llm_call)
        if self.tools:
            workflow.add_node("tools", ToolNode(tools=self.tools))
        workflow.add_edge(START, "llm")
        if self.tools:
            workflow.add_conditional_edges(
                "llm",
                tools_condition,
            )
            workflow.add_edge("tools", "llm")
        workflow.add_edge("llm", END)
        try:
            sqlite_checkpointer = AsyncSqliteSaver(await self.get_async_conn())
            graph = workflow.compile(checkpointer=sqlite_checkpointer)
            self.graph = graph
            logger.info(f"智能体 {self.name} 图构建成功（带检查点）")
            return graph
        except Exception as e:
            logger.warning(f"智能体 {self.name} 设置检查点失败: {e}，使用无检查点模式")
            graph = workflow.compile()
            self.graph = graph
            return graph

    async def get_async_conn(self):
        """获取异步数据库连接"""
        db_path = self.workdir / "checkpoint.db"
        return await aiosqlite.connect(str(db_path))

    async def check_checkpointer(self) -> bool:
        """检查检查点是否可用"""
        conn = await self.get_async_conn()
        await conn.close()
        return True

    async def get_info(self):
        """获取智能体信息（无数据库依赖）"""
        config_dict = self.config_schema.to_dict()
        tools = self._get_tools(config_dict.get("tools", []), [])
        tool_names = [getattr(tool, "name", str(tool)) for tool in tools]
        info = {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "agent_type": self.name,
            "config_schema": config_dict,
            "requirements": self.requirements,
            "available_tools": tool_names,
            "has_checkpointer": await self.check_checkpointer(),
            "met_requirements": self.check_requirements(),
            "is_active": True,
            "created_at": None,
            "updated_at": None,
        }
        return info

    def check_requirements(self) -> bool:
        """检查环境要求（无数据库依赖）"""
        llm_config = self._get_llm_config()
        provider = llm_config.get("provider")

        # 根据不同的模型提供商检查API密钥
        if provider == "zhipu" and "ZHIPUAI_API_KEY" not in os.environ:
            logger.warning("缺少 ZHIPUAI_API_KEY 环境变量")
            return False
        elif provider == "openai" and "OPENAI_API_KEY" not in os.environ:
            logger.warning("缺少 OPENAI_API_KEY 环境变量")
            return False

        # 检查工具要求
        tools = self.config_schema.tools
        if "web_search" in tools and "TAVILY_API_KEY" not in os.environ:
            logger.warning("启用了网页搜索但缺少 TAVILY_API_KEY 环境变量")
            return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（无数据库依赖）"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "agent_type": self.name,
            "workdir": str(self.workdir),
            "config": self.config_schema.to_dict() if self.config_schema else {},
        }
