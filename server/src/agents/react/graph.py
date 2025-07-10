import asyncio
import uuid


from server.src.utils import logger
from server.src.agents.registry import BaseAgent
from server.src.agents.react.configuration import ReActConfiguration

class ReActAgent(BaseAgent):
    name = "ReAct"
    description = "A react agent that can answer questions and help with tasks."
    config_schema = ReActConfiguration

    async def get_graph(self, **kwargs):
        from .workflows import graph
        return graph





if __name__ == "__main__":
    pass
