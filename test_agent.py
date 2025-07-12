



import asyncio
import uuid
from server.src.agents.chatbot.graph import ChatbotAgent


def main():
    agent = ChatbotAgent()

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    from server.src.agents.utils import agent_cli

    agent_cli(agent, config)


if __name__ == "__main__":
    main()
    # asyncio.run(main())
