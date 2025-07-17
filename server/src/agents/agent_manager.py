import asyncio
from src.agents.chatbot_agent import ChatbotAgent
from src.utils import logger
from db_manager import DBManager


class AgentManager:
    def __init__(self):
        self._instances = {}  # key: agent_id, value: agent实例
        self.db_manager = DBManager()

    def register_agent(self, agent_class):
        """注册预定义智能体类并缓存实例，agent_class需有唯一name属性"""
        agent = agent_class()
        self._instances[agent.name] = agent

    async def aget_agent(self, agent_id, **kwargs):
        """异步获取智能体实例（先查缓存，无则查库并异步创建、缓存）"""
        if agent_id in self._instances:
            return self._instances[agent_id]

        from models.agent_models import CustomAgent as CustomAgentModel
        from src.agents.chatbot_agent import ChatbotAgent

        with self.db_manager.get_session_context() as session:
            db_record = session.query(CustomAgentModel).filter(
                CustomAgentModel.agent_id == agent_id,
                CustomAgentModel.deleted_at.is_(None),
                CustomAgentModel.is_active == True
            ).first()

            if not db_record:
                raise ValueError(f"智能体 {agent_id} 不存在")

        # 使用异步工厂创建实例
        agent = await ChatbotAgent.create(agent_id=db_record.agent_id, config=db_record.to_chatbot_config())
        self._instances[agent_id] = agent
        return agent

    def get_agent(self, agent_id, **kwargs):
        """同步获取智能体实例（先查缓存，无则查库并缓存）。警告：可能不完全初始化。"""
        logger.warning(f"正在同步获取智能体 {agent_id}，MCP工具可能无法加载。推荐使用 aget_agent。")
        if agent_id in self._instances:
            return self._instances[agent_id]

        from models.agent_models import CustomAgent as CustomAgentModel
        from src.agents.chatbot_agent import ChatbotAgent

        with self.db_manager.get_session_context() as session:
            db_record = session.query(CustomAgentModel).filter(
                CustomAgentModel.agent_id == agent_id,
                CustomAgentModel.deleted_at.is_(None),
                CustomAgentModel.is_active == True
            ).first()

            if not db_record:
                raise ValueError(f"智能体 {agent_id} 不存在")

            # 使用同步方法创建，可能不完整
            agent = ChatbotAgent.from_db_record(db_record)
            self._instances[agent_id] = agent
            return agent

    async def aget_agent_by_identifier(self, identifier, **kwargs):
        """
        异步根据标识符获取智能体（支持 agent_id 或 name，优先缓存，无则查库）
        """
        if identifier in self._instances:
            return self._instances[identifier]

        from models.agent_models import CustomAgent as CustomAgentModel
        from src.agents.chatbot_agent import ChatbotAgent

        with self.db_manager.get_session_context() as session:
            db_record = session.query(CustomAgentModel).filter(
                ((CustomAgentModel.agent_id == identifier) | (CustomAgentModel.name == identifier)),
                CustomAgentModel.deleted_at.is_(None),
                CustomAgentModel.is_active == True
            ).first()

            if not db_record:
                return None
                
            # 在会话关闭前获取所有需要的数据
            agent_id = db_record.agent_id
            config = db_record.to_chatbot_config()

        # 使用异步工厂创建实例
        agent = await ChatbotAgent.create(agent_id=agent_id, config=config)
        self._instances[agent_id] = agent
        return agent

    def get_agent_by_identifier(self, identifier, **kwargs):
        """
        同步根据标识符获取智能体（支持 agent_id 或 name，优先缓存，无则查库）。警告：可能不完全初始化。
        """
        logger.warning(f"正在同步获取智能体 {identifier}，MCP工具可能无法加载。推荐使用 aget_agent_by_identifier。")
        if identifier in self._instances:
            return self._instances[identifier]

        from models.agent_models import CustomAgent as CustomAgentModel
        from src.agents.chatbot_agent import ChatbotAgent

        with self.db_manager.get_session_context() as session:
            db_record = session.query(CustomAgentModel).filter(
                ((CustomAgentModel.agent_id == identifier) | (CustomAgentModel.name == identifier)),
                CustomAgentModel.deleted_at.is_(None),
                CustomAgentModel.is_active == True
            ).first()

            if not db_record:
                return None

            agent = ChatbotAgent.from_db_record(db_record)
            self._instances[db_record.agent_id] = agent
            return agent

    def get_agents(self):
        """获取所有已缓存的智能体实例"""
        return list(self._instances.values())

    async def get_agents_info(self):
        """获取所有已缓存智能体的简要信息（异步）"""
        agents = self.get_agents()
        return await asyncio.gather(*[a.get_info() for a in agents])

    def get_agents_by_user(self, user_id, include_public=True):
        """获取指定用户的所有智能体（自己创建的+公开的），返回dict列表，避免DetachedInstanceError"""
        from sqlalchemy import or_
        from models.agent_models import CustomAgent as CustomAgentModel
        with self.db_manager.get_session_context() as session:
            query = session.query(CustomAgentModel).filter(CustomAgentModel.deleted_at.is_(None))
            if include_public:
                query = query.filter(or_(CustomAgentModel.created_by == user_id, CustomAgentModel.is_public == True))
            else:
                query = query.filter(CustomAgentModel.created_by == user_id)
            query = query.order_by(CustomAgentModel.created_at.desc())
            agents = query.all()
            return [agent.to_dict(include_config=False) for agent in agents]

    def clear_cache(self):
        self._instances.clear()
        logger.info("智能体管理器缓存已清空")


agent_manager = AgentManager()