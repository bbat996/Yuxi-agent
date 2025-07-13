from dotenv import load_dotenv
from server.config import PROJECT_DIR

load_dotenv(f"{PROJECT_DIR}/server/.env")

from concurrent.futures import ThreadPoolExecutor  # noqa: E402

executor = ThreadPoolExecutor()

from server.config import Config  # noqa: E402

config = Config()

from server.src.core.lightrag_based_kb import LightRagBasedKB  # noqa: E402

knowledge_base = LightRagBasedKB()

# from server.src.core import GraphDatabase  # noqa: E402
# graph_base = GraphDatabase()
graph_base = None
