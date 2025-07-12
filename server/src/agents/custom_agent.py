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


class CustomAgentConfiguration(Configuration):
    """自定义智能体配置类"""

    # 基础配置
    name: str = "自定义智能体"
    description: str = "用户自定义的智能体"
    agent_type: str = "custom"

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
    def from_db_record(cls, db_record: CustomAgentModel) -> "CustomAgentConfiguration":
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


class CustomAgent(BaseAgent):
    """动态自定义智能体类"""

    def __init__(self, agent_id: str, **kwargs):
        """
        初始化自定义智能体

        Args:
            agent_id: 智能体ID
            **kwargs: 额外参数
        """
        self.agent_id = agent_id
        self.db_manager = DBManager()

        # 从数据库加载智能体配置
        self._load_agent_from_db()

        # 设置基础属性
        self.name = self.db_record.name or "custom_agent"
        self.description = self.db_record.description or "自定义智能体"
        self.config_schema = CustomAgentConfiguration.from_db_record(self.db_record)
        self.requirements = []  # 自定义智能体没有硬性要求

        # 工作目录
        self.workdir = Path(sys_config.save_dir) / "agents" / f"custom_{self.agent_id[:8]}"
        self.workdir.mkdir(parents=True, exist_ok=True)

        # 图实例缓存
        self.graph = None

        # 检查要求
        self.check_requirements()

        logger.info(f"自定义智能体初始化完成: {self.name} (ID: {self.agent_id})")

    def _load_agent_from_db(self):
        """从数据库加载智能体配置"""
        with self.db_manager.get_session_context() as session:
            db_record = (
                session.query(CustomAgentModel)
                .filter(CustomAgentModel.agent_id == self.agent_id, CustomAgentModel.deleted_at.is_(None), CustomAgentModel.is_active == True)
                .first()
            )

            if not db_record:
                raise ValueError(f"智能体不存在或已停用: {self.agent_id}")

            self.db_record = db_record

    def reload_config(self):
        """重新加载配置"""
        self._load_agent_from_db()
        self.config_schema = CustomAgentConfiguration.from_db_record(self.db_record)
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

        # 添加知识库检索工具
        if self.db_record.knowledge_config and self.db_record.knowledge_config.get("databases"):
            for db_id in self.db_record.knowledge_config["databases"]:
                tool_name = f"retrieve_{db_id[:8]}"
                if tool_name in platform_tools:
                    result_tools.append(platform_tools[tool_name])
                    logger.debug(f"添加知识库工具: {tool_name}")

        # 添加MCP技能工具
        if mcp_skills and isinstance(mcp_skills, list):
            from server.src.agents.mcp_integration import get_mcp_tools_for_agent
            import asyncio

            # 异步获取MCP工具
            if asyncio.get_event_loop().is_running():
                # 如果在异步环境中，直接调用
                mcp_tools = asyncio.create_task(get_mcp_tools_for_agent(mcp_skills))
            else:
                # 如果在同步环境中，使用run_until_complete
                mcp_tools = asyncio.run(get_mcp_tools_for_agent(mcp_skills))

            if isinstance(mcp_tools, list):
                result_tools.extend(mcp_tools)
                logger.debug(f"添加MCP工具: {len(mcp_tools)} 个")

        logger.info(f"智能体 {self.name} 加载了 {len(result_tools)} 个工具")
        return result_tools

    def _get_model_config(self) -> Dict[str, Any]:
        """获取模型配置"""
        model_config = {}

        # 基础模型配置
        if self.db_record.model_config:
            model_config.update(self.db_record.model_config)

        # 确保有默认的模型设置
        if "provider" not in model_config:
            model_config["provider"] = "zhipu"
        if "model_name" not in model_config:
            model_config["model_name"] = "glm-4-plus"

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
        tools = self._get_tools(final_config.get("tools", self.config_schema.tools), final_config.get("mcp_skills", self.config_schema.mcp_skills))

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
        """获取智能体信息"""
        # 重新加载最新配置
        self._load_agent_from_db()

        # 获取配置信息
        config_dict = self.config_schema.to_dict()

        # 获取工具信息
        tools = self._get_tools(config_dict.get("tools", []), config_dict.get("mcp_skills", []))
        tool_names = [getattr(tool, "name", str(tool)) for tool in tools]

        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "agent_type": self.db_record.agent_type,
            "config_schema": config_dict,
            "requirements": self.requirements,
            "available_tools": tool_names,
            "has_checkpointer": await self.check_checkpointer(),
            "met_requirements": self.check_requirements(),
            "is_active": self.db_record.is_active,
            "created_at": self.db_record.created_at.isoformat() if self.db_record.created_at else None,
            "updated_at": self.db_record.updated_at.isoformat() if self.db_record.updated_at else None,
        }

    def check_requirements(self) -> bool:
        """检查环境要求"""
        # 自定义智能体的要求检查
        # 检查模型配置
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
        if self.db_record.tools_config:
            tools = self.db_record.tools_config.get("builtin_tools", [])
            if "web_search" in tools and "TAVILY_API_KEY" not in os.environ:
                logger.warning("启用了网页搜索但缺少 TAVILY_API_KEY 环境变量")
                return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "agent_type": self.db_record.agent_type if hasattr(self, "db_record") else "custom",
            "workdir": str(self.workdir),
            "config": self.config_schema.to_dict() if self.config_schema else {},
        }
