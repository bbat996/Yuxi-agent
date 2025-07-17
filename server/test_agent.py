



import asyncio
import uuid
from config import PROJECT_DIR
from src.agents.chatbot_agent import ChatbotAgent
from src.agents.utils import agent_cli
from config.agent_config import AgentConfig


async def main():
    config = AgentConfig.load_from_yaml(f"{PROJECT_DIR}/server/config/agents/chatbot.private.yaml")
    print(config)
    agent = await ChatbotAgent.create(config=config)

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    await agent_cli(agent, config)


if __name__ == "__main__":
    asyncio.run(main())
