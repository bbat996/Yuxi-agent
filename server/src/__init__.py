from concurrent.futures import ThreadPoolExecutor  # noqa: E402
from config import config  # noqa: E402
from src.core.lightrag_based_kb import LightRagBasedKB  # noqa: E402

executor = ThreadPoolExecutor()
knowledge_base = LightRagBasedKB()

# from src.core import GraphDatabase  # noqa: E402
# graph_base = GraphDatabase()
graph_base = None
