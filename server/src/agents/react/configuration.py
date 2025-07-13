from dataclasses import dataclass

from server.src.agents.registry import Configuration


@dataclass(kw_only=True)
class ReActConfiguration(Configuration):
    """配置"""

    pass
