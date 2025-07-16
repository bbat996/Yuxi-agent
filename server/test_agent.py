



import asyncio
import uuid
from src.agents.chatbot_agent import ChatbotAgent
from src.agents.utils import agent_cli


def main():
    agent = ChatbotAgent()

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}


    asyncio.run(agent_cli(agent, config))


if __name__ == "__main__":
    main()
