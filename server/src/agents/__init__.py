import asyncio
from server.src.agents.chatbot import ChatbotAgent
from server.src.agents.react import ReActAgent
from server.src.utils import logger


class AgentManager:
    def __init__(self):
        self._classes = {}  # 预定义智能体类
        self._instances = {}  # 存储已创建的 agent 实例
        self._custom_instances = {}  # 存储自定义智能体实例
        self.db_manager = None  # 延迟初始化以避免循环导入

    def _init_db_manager(self):
        """延迟初始化数据库管理器"""
        if self.db_manager is None:
            from server.db_manager import DBManager

            self.db_manager = DBManager()

    def register_agent(self, agent_class):
        """注册预定义智能体类"""
        self._classes[agent_class.name] = agent_class

    def init_all_agents(self):
        """初始化所有预定义智能体"""
        for agent_class in self._classes.values():
            self.get_agent(agent_class.name)

    def get_agent(self, agent_name, **kwargs):
        """获取预定义智能体实例"""
        # 检查是否已经创建了该 agent 的实例
        if agent_name not in self._instances:
            if agent_name not in self._classes:
                raise ValueError(f"未知的智能体类型: {agent_name}")
            agent_class = self._classes[agent_name]
            self._instances[agent_name] = agent_class()

        return self._instances[agent_name]

    def get_custom_agent(self, agent_id: str, **kwargs):
        """获取自定义智能体实例"""
        from server.src.agents.custom_agent import CustomAgent

        # 使用agent_id作为缓存键
        cache_key = f"custom_{agent_id}"

        if cache_key not in self._custom_instances:
            try:
                # 创建自定义智能体实例
                self._custom_instances[cache_key] = CustomAgent(agent_id=agent_id, **kwargs)
            except Exception as e:
                logger.error(f"创建自定义智能体失败 {agent_id}: {e}")
                raise

        return self._custom_instances[cache_key]

    def reload_custom_agent(self, agent_id: str):
        """重新加载自定义智能体配置"""
        cache_key = f"custom_{agent_id}"
        if cache_key in self._custom_instances:
            try:
                self._custom_instances[cache_key].reload_config()
                logger.info(f"自定义智能体配置重新加载成功: {agent_id}")
            except Exception as e:
                logger.error(f"重新加载自定义智能体配置失败 {agent_id}: {e}")
                # 移除缓存的实例，下次访问时重新创建
                del self._custom_instances[cache_key]
                raise

    def remove_custom_agent(self, agent_id: str):
        """移除自定义智能体实例缓存"""
        cache_key = f"custom_{agent_id}"
        if cache_key in self._custom_instances:
            del self._custom_instances[cache_key]
            logger.info(f"自定义智能体实例已移除: {agent_id}")

    def get_agent_by_identifier(self, identifier: str, **kwargs):
        """
        根据标识符获取智能体（预定义或自定义）

        Args:
            identifier: 智能体标识符，可能是预定义名称或自定义ID

        Returns:
            智能体实例
        """
        # 首先尝试作为预定义智能体
        if identifier in self._classes:
            return self.get_agent(identifier, **kwargs)

        # 然后尝试作为自定义智能体ID
        try:
            return self.get_custom_agent(identifier, **kwargs)
        except Exception as e:
            logger.warning(f"无法获取智能体 {identifier}: {e}")
            raise ValueError(f"智能体不存在: {identifier}")

    def get_agents(self):
        """获取所有预定义智能体实例"""
        return list(self._instances.values())

    def get_custom_agents(self):
        """获取所有自定义智能体实例"""
        return list(self._custom_instances.values())

    def get_all_agents(self):
        """获取所有智能体实例（预定义+自定义）"""
        return self.get_agents() + self.get_custom_agents()

    async def get_agents_info(self):
        """获取所有预定义智能体信息"""
        agents = self.get_agents()
        return await asyncio.gather(*[a.get_info() for a in agents])

    async def get_all_agents_info(self, include_custom=True):
        """获取所有智能体信息（包括自定义智能体）"""
        info_list = []

        # 获取预定义智能体信息
        predefined_agents = self.get_agents()
        if predefined_agents:
            predefined_info = await asyncio.gather(*[a.get_info() for a in predefined_agents])
            info_list.extend(predefined_info)

        # 获取自定义智能体信息
        if include_custom:
            self._init_db_manager()
            try:
                from server.models.agent_models import CustomAgent as CustomAgentModel

                with self.db_manager.get_session_context() as session:
                    # 获取所有激活的自定义智能体
                    custom_agents_db = (
                        session.query(CustomAgentModel)
                        .filter(CustomAgentModel.deleted_at.is_(None), CustomAgentModel.is_active == True)
                        .all()
                    )

                    for db_record in custom_agents_db:
                        try:
                            # 获取或创建实例
                            custom_agent = self.get_custom_agent(db_record.agent_id)
                            agent_info = await custom_agent.get_info()
                            info_list.append(agent_info)
                        except Exception as e:
                            logger.error(f"获取自定义智能体信息失败 {db_record.agent_id}: {e}")
                            # 添加错误信息
                            info_list.append(
                                {
                                    "agent_id": db_record.agent_id,
                                    "name": db_record.name or "未知智能体",
                                    "description": "获取信息失败",
                                    "agent_type": "custom",
                                    "error": str(e),
                                    "is_active": False,
                                }
                            )
            except Exception as e:
                logger.error(f"获取自定义智能体列表失败: {e}")

        return info_list

    def clear_cache(self):
        """清空所有缓存"""
        self._instances.clear()
        self._custom_instances.clear()
        logger.info("智能体管理器缓存已清空")


agent_manager = AgentManager()
agent_manager.register_agent(ChatbotAgent)
agent_manager.register_agent(ReActAgent)  # 暂时屏蔽 ReActAgent
agent_manager.init_all_agents()

__all__ = ["agent_manager"]


if __name__ == "__main__":
    pass
