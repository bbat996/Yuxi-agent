from typing import Annotated

from langchain_core.tools import tool
from langchain_tavily import TavilySearch

from src import config, graph_base


@tool
def calculator(a: float, b: float, operation: str) -> float:
    """Calculate two numbers. operation: add, subtract, multiply, divide"""
    if operation == "add":
        return a + b
    elif operation == "subtract":
        return a - b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        return a / b
    else:
        raise ValueError(f"Invalid operation: {operation}, only support add, subtract, multiply, divide")


@tool
def query_knowledge_graph(query: Annotated[str, "The keyword to query knowledge graph."]):
    """Use this to query knowledge graph."""
    return graph_base.query_node(query, hops=2)


_TOOLS_REGISTRY = {
    "Calculator": calculator,
    "QueryKnowledgeGraph": query_knowledge_graph,
}

if config.enable_web_search:
    _TOOLS_REGISTRY["WebSearchWithTavily"] = TavilySearch(max_results=10)
