



import asyncio
import uuid
from src.agents.chatbot_agent import ChatbotAgent
from src.agents.utils import agent_cli


async def main():
    agent = await ChatbotAgent.create()

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}


    await agent_cli(agent, config)


if __name__ == "__main__":
    asyncio.run(main())
