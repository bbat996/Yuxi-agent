import os
import traceback
from typing import Any, Dict, List
from pathlib import Path
import yaml
from dataclasses import dataclass, field

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


@dataclass(kw_only=True)
class ChatbotConfiguration(Configuration):
    """自定义智能体配置类"""

    # 基础信息
    name: str = field(default="智能助手", metadata={"name": "智能体名称", "configurable": True})
    description: str = field(default="一个功能强大的智能助手", metadata={"name": "智能体描述", "configurable": True})
    agent_type: str = field(default="chatbot", metadata={"name": "智能体类型", "configurable": False})

    # 核心配置
    system_prompt: str = field(default="You are a helpful assistant.", metadata={"name": "系统提示词", "configurable": True})
    
    # 模型配置 - 分开配置
    provider: str = field(default="zhipu", metadata={"name": "模型提供商", "configurable": True})
    model_name: str = field(default="glm-4-plus", metadata={"name": "模型名称", "configurable": True})

    # 工具配置
    tools: List[str] = field(default_factory=list, metadata={"name": "内置工具", "configurable": True})
    mcp_skills: Dict[str, Any] = field(default_factory=dict, metadata={"name": "MCP技能", "configurable": True})

    # 知识库配置
    knowledge_databases: List[str] = field(default_factory=list, metadata={"name": "知识库", "configurable": True})
    retrieval_params: Dict[str, Any] = field(default_factory=dict, metadata={"name": "检索参数", "configurable": True})

    # 模型参数
    model_parameters: Dict[str, Any] = field(default_factory=dict, metadata={"name": "模型参数", "configurable": True})

    @classmethod
    def from_db_record(cls, db_record) -> "ChatbotConfiguration":
        """从数据库记录创建配置"""
        # 使用数据库模型的to_chatbot_config方法
        if hasattr(db_record, 'to_chatbot_config'):
            config_data = db_record.to_chatbot_config()
        else:
            # 兼容旧版本
            config_data = {}

            # 基础信息
            if hasattr(db_record, 'name') and db_record.name:
                config_data["name"] = db_record.name
            if hasattr(db_record, 'description') and db_record.description:
                config_data["description"] = db_record.description
            if hasattr(db_record, 'agent_type') and db_record.agent_type:
                config_data["agent_type"] = db_record.agent_type
            if hasattr(db_record, 'system_prompt') and db_record.system_prompt:
                config_data["system_prompt"] = db_record.system_prompt

            # 模型配置
            if hasattr(db_record, 'model_config') and db_record.model_config:
                model_config = db_record.model_config
                if "provider" in model_config and "model_name" in model_config:
                    config_data["provider"] = model_config["provider"]
                    config_data["model_name"] = model_config["model_name"]
                if "parameters" in model_config:
                    config_data["model_parameters"] = model_config["parameters"]

            # 工具配置
            if hasattr(db_record, 'tools_config') and db_record.tools_config:
                tools_config = db_record.tools_config
                if "builtin_tools" in tools_config:
                    config_data["tools"] = tools_config["builtin_tools"]
                if "mcp_skills" in tools_config:
                    config_data["mcp_skills"] = tools_config["mcp_skills"]

            # 知识库配置
            if hasattr(db_record, 'knowledge_config') and db_record.knowledge_config:
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

    @classmethod
    async def create(cls, agent_id: str = None, config: dict = None, **kwargs) -> "ChatbotAgent":
        """异步工厂方法，用于创建和初始化ChatbotAgent实例"""
        agent = cls(agent_id=agent_id, config=config, **kwargs, _skip_init=True)
        await agent._ainitialize_llm_and_tools()
        logger.info(f"ChatbotAgent 异步初始化完成: {agent.name}")
        return agent

    @classmethod
    def from_db_record(cls, db_record, agent_id: str = None, **kwargs) -> "ChatbotAgent":
        """从数据库记录创建ChatbotAgent实例（同步，可能不完全初始化）"""
        # 获取配置
        config = ChatbotConfiguration.from_db_record(db_record)
        
        # 创建实例
        agent_id = agent_id or getattr(db_record, 'agent_id', None)
        # 注意：这里返回的实例可能没有完全初始化LLM和工具
        return cls(agent_id=agent_id, config=config.to_dict(), **kwargs)

    def __init__(self, agent_id: str = None, config: dict = None, _skip_init: bool = False, **kwargs):
        self.agent_id = agent_id or "chatbot"
        
        # 合并 YAML、外部 config、默认值
        if config is not None:
            self.config_schema = ChatbotConfiguration.from_runnable_config(config, agent_name=self.agent_id)
        else:
            self.config_schema = ChatbotConfiguration.from_runnable_config(agent_name=self.agent_id)
        
        # 从配置中获取名称和描述
        self.name = getattr(self.config_schema, "name", "chatbot")
        self.description = (
            kwargs.get("description") or 
            getattr(self.config_schema, "description", "基础的对话机器人，可以回答问题，默认不使用任何工具，可在配置中启用需要的工具。")
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
            self._initialize_llm_and_tools() # 同步版本，可能不完整
            logger.info(f"ChatbotAgent 同步初始化完成: {self.name}")

    async def _ainitialize_llm_and_tools(self):
        """异步初始化或重新初始化LLM、工具和绑定后的模型"""
        # 获取模型配置
        model_config = self._get_model_config()
        model_parameters = getattr(self.config_schema, "model_parameters", {})

        # 加载模型
        logger.info(f"开始加载模型: {model_config.get('provider')}/{model_config.get('model_name')}")
        self.model = load_chat_model(
            provider=model_config.get("provider"),
            model=model_config.get("model_name"),
            model_parameters=model_parameters
        )
        logger.info("模型加载成功")

        # 获取工具
        tools_config = getattr(self.config_schema, "tools", [])
        mcp_skills_config = getattr(self.config_schema, "mcp_skills", [])
        self.tools = await self._aget_tools(
            tools_config,
            mcp_skills_config,
        )
        
        logger.info("=== 工具配置 ===")
        if self.tools:
            tool_names = [getattr(tool, 'name', str(tool)) for tool in self.tools]
            logger.info(f"可用工具: {', '.join(tool_names)}")
            self.llm_with_tools = self.model.bind_tools(self.tools)
        else:
            logger.info("无可用工具")
            self.llm_with_tools = self.model

    def _init_mcp_connections(self):
        """初始化MCP连接配置"""
        from src.agents.mcp_client import get_mcp_client, load_mcp_connections_from_config
        mcp_config = getattr(self.config_schema, "mcp_skills", {})
        if isinstance(mcp_config, list) and mcp_config:
            # 兼容list格式，直接跳过连接配置（只用技能名，不需要连接）
            logger.info(f"mcp_skills 为 list（{mcp_config}），使用默认MCP连接配置")
            # 不更新连接
        elif isinstance(mcp_config, dict) and mcp_config:
            connections = load_mcp_connections_from_config(mcp_config)
            if connections:
                mcp_integration = get_mcp_client()
                mcp_integration.update_connections(connections)
                logger.info(f"智能体 {self.name} 加载了 {len(connections)} 个MCP技能配置")
        else:
            logger.info(f"mcp_skills 类型未知（{type(mcp_config)}），跳过 MCP 连接初始化: {mcp_config}")

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
        model_config = self._get_model_config()
        model_parameters = getattr(self.config_schema, "model_parameters", {})

        # 加载模型
        logger.info(f"(同步) 开始加载模型: {model_config.get('provider')}/{model_config.get('model_name')}")
        self.model = load_chat_model(
            provider=model_config.get("provider"),
            model=model_config.get("model_name"),
            model_parameters=model_parameters
        )
        logger.info("(同步) 模型加载成功")

        # 获取工具 (同步版本，跳过MCP)
        tools_config = getattr(self.config_schema, "tools", [])
        self.tools = self._get_tools(tools_config, []) # 传入空的mcp_skills
        
        logger.info("=== (同步) 工具配置 ===")
        if self.tools:
            tool_names = [getattr(tool, 'name', str(tool)) for tool in self.tools]
            logger.info(f"可用工具: {', '.join(tool_names)}")
            self.llm_with_tools = self.model.bind_tools(self.tools)
        else:
            logger.info("无可用工具")
            self.llm_with_tools = self.model

    async def _aget_tools(self, tools: List[str], mcp_skills: List[str] = None) -> List:
        """
        根据配置获取工具
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
        knowledge_dbs = getattr(self.config_schema, "knowledge_databases", [])
        if knowledge_dbs:
            for db_id in knowledge_dbs:
                tool_name = f"retrieve_{db_id[:8]}"
                if tool_name in platform_tools:
                    result_tools.append(platform_tools[tool_name])
                    logger.debug(f"添加知识库工具: {tool_name}")

        # 添加MCP技能工具（支持list格式）
        if mcp_skills and isinstance(mcp_skills, list):
            from src.agents.mcp_client import get_mcp_tools_for_agent
            mcp_tools = await get_mcp_tools_for_agent(mcp_skills)
            if isinstance(mcp_tools, list):
                result_tools.extend(mcp_tools)
                logger.debug(f"添加MCP工具: {len(mcp_tools)} 个")
        return result_tools

    def _get_model_config(self) -> Dict[str, Any]:
        """获取模型配置"""
        model_config = {}
        
        # 使用分开配置方式
        provider = getattr(self.config_schema, "provider", "deepseek")
        model_name = getattr(self.config_schema, "model_name", "deepseek-chat")
        
        model_config["provider"] = provider
        model_config["model_name"] = model_name
        
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

        # 异步调用模型
        messages = [{"role": "system", "content": system_prompt}] + state["messages"]
        try:
            # 使用预先加载和绑定的模型与工具
            result = await self.llm_with_tools.ainvoke(messages)
            
            # 格式化打印结果
            logger.info("=== 模型调用成功 ===")
            logger.info(f"返回类型: {type(result).__name__}")
            
            # 检查是否有工具调用
            if hasattr(result, 'tool_calls') and result.tool_calls:
                logger.info(f"工具调用数量: {len(result.tool_calls)}")
                logger.info(f"工具调用: {result.tool_calls}")
            else:
                logger.info("无工具调用")
                if hasattr(result, 'content') and result.content:
                    logger.info(f"回复内容: {result.content[:200]}{'...' if len(result.content) > 200 else ''}")
            
            # 打印token使用情况
            if hasattr(result, 'response_metadata') and result.response_metadata:
                token_usage = result.response_metadata.get('token_usage', {})
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
