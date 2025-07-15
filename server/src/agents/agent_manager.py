import asyncio
from server.src.agents.chatbot_agent import ChatbotAgent
from server.src.utils import logger
from server.db_manager import DBManager


class AgentManager:
    def __init__(self):
        self._instances = {}  # key: agent_id, value: agent实例
        self.db_manager = DBManager()

    def register_agent(self, agent_class):
        """注册预定义智能体类并缓存实例，agent_class需有唯一name属性"""
        agent = agent_class()
        self._instances[agent.name] = agent

    def get_agent(self, agent_id, **kwargs):
        """获取智能体实例（先查缓存，无则查库并缓存）"""
        if agent_id in self._instances:
            return self._instances[agent_id]
        # 数据库查找
        from server.models.agent_models import CustomAgent as CustomAgentModel
        from server.src.agents.chatbot_agent import ChatbotAgent
        with self.db_manager.get_session_context() as session:
            db_record = session.query(CustomAgentModel).filter(
                CustomAgentModel.agent_id == agent_id,
                CustomAgentModel.deleted_at.is_(None),
                CustomAgentModel.is_active == True
            ).first()
            if not db_record:
                raise ValueError(f"智能体 {agent_id} 不存在")
            agent = ChatbotAgent.from_db_record(db_record)
            self._instances[agent_id] = agent
            return agent

    def get_agent_by_identifier(self, identifier, **kwargs):
        """
        根据标识符获取智能体（支持 agent_id 或 name，优先缓存，无则查库）
        """
        # 先查缓存
        if identifier in self._instances:
            return self._instances[identifier]
        # 再查数据库（支持用 name 查找）
        from server.models.agent_models import CustomAgent as CustomAgentModel
        from server.src.agents.chatbot_agent import ChatbotAgent
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

    async def get_all_agents_info(self):
        """获取所有已缓存智能体的详细信息（异步，兼容旧接口）"""
        return await self.get_agents_info()

    def clear_cache(self):
        self._instances.clear()
        logger.info("智能体管理器缓存已清空")


agent_manager = AgentManager()