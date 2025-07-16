from typing import Annotated

from langchain_core.tools import tool
from langchain_tavily import TavilySearch

from src import config, graph_base


@tool
def query_knowledge_graph(query: Annotated[str, "The keyword to query knowledge graph."]):
    """Use this to query knowledge graph."""
    return graph_base.query_node(query, hops=2)


_TOOLS_REGISTRY = {
    "QueryKnowledgeGraph": query_knowledge_graph,
}

if config.enable_web_search:
    _TOOLS_REGISTRY["WebSearchWithTavily"] = TavilySearch(max_results=10)
