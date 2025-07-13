import os
from typing import Any, Dict, List
from pathlib import Path

from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver, aiosqlite

from server.src import config as sys_config
from server.src.utils import logger
from server.src.agents.registry import State, BaseAgent, Configuration
from server.src.agents.utils import load_chat_model, get_cur_time_with_utc
from server.src.agents.tools_factory import get_all_tools
from server.db_manager import DBManager
from server.models.agent_models import CustomAgent as CustomAgentModel


class ChatbotAgentConfiguration(Configuration):
    """自定义智能体配置类"""

    # 核心配置
    system_prompt: str = "You are a helpful assistant."
    model: str = "zhipu/glm-4-plus"

    # 工具配置
    tools: List[str] = []
    mcp_skills: List[str] = []

    # 知识库配置
    knowledge_databases: List[str] = []
    retrieval_params: Dict[str, Any] = {}

    # 模型参数
    model_parameters: Dict[str, Any] = {}

    @classmethod
    def from_db_record(cls, db_record: CustomAgentModel) -> "ChatbotAgentConfiguration":
        """从数据库记录创建配置"""
        config_data = {}

        # 基础信息
        if db_record.name:
            config_data["name"] = db_record.name
        if db_record.description:
            config_data["description"] = db_record.description
        if db_record.agent_type:
            config_data["agent_type"] = db_record.agent_type
        if db_record.system_prompt:
            config_data["system_prompt"] = db_record.system_prompt

        # 模型配置
        if db_record.model_config:
            model_config = db_record.model_config
            if "provider" in model_config and "model_name" in model_config:
                config_data["model"] = f"{model_config['provider']}/{model_config['model_name']}"
            if "parameters" in model_config:
                config_data["model_parameters"] = model_config["parameters"]

        # 工具配置
        if db_record.tools_config:
            tools_config = db_record.tools_config
            if "builtin_tools" in tools_config:
                config_data["tools"] = tools_config["builtin_tools"]
            if "mcp_skills" in tools_config:
                config_data["mcp_skills"] = tools_config["mcp_skills"]

        # 知识库配置
        if db_record.knowledge_config:
            knowledge_config = db_record.knowledge_config
            if "databases" in knowledge_config:
                config_data["knowledge_databases"] = knowledge_config["databases"]
            if "retrieval_params" in knowledge_config:
                config_data["retrieval_params"] = knowledge_config["retrieval_params"]

        return cls(**config_data)


class ChatbotAgent(BaseAgent):
    """无数据库依赖的 ChatbotAgent，所有配置均外部传入或YAML"""

    # 基础配置
    name: str = "chatbot"
    description: str = "基础的对话机器人，可以回答问题，默认不使用任何工具，可在配置中启用需要的工具。"
    agent_type: str = "chatbot"

    def __init__(self, agent_id: str = None, config: dict = None, **kwargs):
        # agent_id 仅用于区分工作目录和日志
        self.agent_id = agent_id or "chatbot"
        self.description = (
            kwargs.get("description")
            or "基础的对话机器人，可以回答问题，默认不使用任何工具，可在配置中启用需要的工具。"
        )
        # 合并 YAML、外部 config、默认值
        if config is not None:
            self.config_schema = ChatbotAgentConfiguration.from_runnable_config(config, agent_name=self.agent_id)
        else:
            self.config_schema = ChatbotAgentConfiguration.from_runnable_config(agent_name=self.agent_id)
        self.requirements = ["TAVILY_API_KEY", "ZHIPUAI_API_KEY"]
        self.workdir = Path(sys_config.storage_dir) / "agents" / self.name
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.graph = None
        logger.info(f"ChatbotAgent 初始化完成: {self.name}")

    def reload_config(self):
        """重新加载配置"""
        # 清除图缓存，强制重新构建
        self.graph = None
        logger.info(f"智能体配置重新加载完成: {self.name}")

    def _get_tools(self, tools: List[str], mcp_skills: List[str] = None) -> List:
        """
        根据配置获取工具
        Args:
            tools: 内置工具列表
            mcp_skills: MCP技能列表
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
        knowledge_dbs = getattr(self.config_schema, "knowledge_databases", [])
        if knowledge_dbs:
            for db_id in knowledge_dbs:
                tool_name = f"retrieve_{db_id[:8]}"
                if tool_name in platform_tools:
                    result_tools.append(platform_tools[tool_name])
                    logger.debug(f"添加知识库工具: {tool_name}")

        # 添加MCP技能工具（langchain-mcp-adapters 版）
        if mcp_skills and isinstance(mcp_skills, list):
            from server.src.agents.mcp_client import get_mcp_tools_for_agent
            import asyncio

            # 兼容异步环境
            try:
                loop = asyncio.get_running_loop()
                mcp_tools = loop.run_until_complete(get_mcp_tools_for_agent(mcp_skills))
            except RuntimeError:
                mcp_tools = asyncio.run(get_mcp_tools_for_agent(mcp_skills))

            if isinstance(mcp_tools, list):
                result_tools.extend(mcp_tools)
                logger.debug(f"添加MCP工具: {len(mcp_tools)} 个")

        logger.info(f"智能体 {self.name} 加载了 {len(result_tools)} 个工具")
        return result_tools

    def _get_model_config(self) -> Dict[str, Any]:
        """获取模型配置（仅从 config_schema）"""
        model_config = {}
        model_str = getattr(self.config_schema, "model", "zhipu/glm-4-plus")
        if "/" in model_str:
            provider, model_name = model_str.split("/", 1)
            model_config["provider"] = provider
            model_config["model_name"] = model_name
        else:
            model_config["provider"] = "zhipu"
            model_config["model_name"] = model_str
        # 额外参数
        if hasattr(self.config_schema, "model_parameters"):
            model_config["parameters"] = getattr(self.config_schema, "model_parameters")
        return model_config

    async def llm_call(self, state: State, config: RunnableConfig = None) -> Dict[str, Any]:
        """调用LLM模型"""
        # 合并配置：运行时配置可以覆盖默认配置
        final_config = self.config_schema.to_dict()
        if config and "configurable" in config:
            final_config.update(config["configurable"])

        # 构建系统提示词
        system_prompt = final_config.get("system_prompt", self.config_schema.system_prompt)
        system_prompt = f"{system_prompt} Now is {get_cur_time_with_utc()}"

        # 加载模型
        model_str = final_config.get("model", self.config_schema.model)
        model = load_chat_model(model_str)

        # 获取工具
        tools = self._get_tools(
            final_config.get("tools", self.config_schema.tools),
            final_config.get("mcp_skills", self.config_schema.mcp_skills),
        )

        if tools:
            model = model.bind_tools(tools)

        # 异步调用模型
        messages = [{"role": "system", "content": system_prompt}] + state["messages"]
        result = await model.ainvoke(messages)

        return {"messages": [result]}

    async def get_graph(self, config_schema: RunnableConfig = None, **kwargs):
        """构建执行图"""
        # 如果图已存在且配置未改变，直接返回
        if self.graph is not None:
            return self.graph

        # 创建状态图
        workflow = StateGraph(State, config_schema=self.config_schema)

        # 添加节点
        workflow.add_node("llm", self.llm_call)

        # 获取所有可用工具用于工具节点
        all_tools = list(get_all_tools().values())
        if all_tools:
            workflow.add_node("tools", ToolNode(tools=all_tools))

        # 添加边
        workflow.add_edge(START, "llm")

        if all_tools:
            workflow.add_conditional_edges(
                "llm",
                tools_condition,
            )
            workflow.add_edge("tools", "llm")

        workflow.add_edge("llm", END)

        # 编译图并设置检查点
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
        tools = self._get_tools(config_dict.get("tools", []), config_dict.get("mcp_skills", []))
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
        model_config = self._get_model_config()
        provider = model_config.get("provider")

        # 根据不同的模型提供商检查API密钥
        if provider == "zhipu" and "ZHIPUAI_API_KEY" not in os.environ:
            logger.warning("缺少 ZHIPUAI_API_KEY 环境变量")
            return False
        elif provider == "openai" and "OPENAI_API_KEY" not in os.environ:
            logger.warning("缺少 OPENAI_API_KEY 环境变量")
            return False

        # 检查工具要求
        tools = getattr(self.config_schema, "tools", [])
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
