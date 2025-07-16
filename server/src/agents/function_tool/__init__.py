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
    # 从配置中获取tavily参数
    tavily_kwargs = {"max_results": 10}
    
    # 如果配置了自定义的base_url，则使用它
    if hasattr(config, 'tavily_base_url') and config.tavily_base_url:
        tavily_kwargs["base_url"] = config.tavily_base_url
    
    # 如果配置了API key，则使用它
    if hasattr(config, 'tavily_api_key') and config.tavily_api_key:
        tavily_kwargs["api_key"] = config.tavily_api_key
    
    _TOOLS_REGISTRY["WebSearchWithTavily"] = TavilySearch(**tavily_kwargs)
