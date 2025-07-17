import yaml
from pathlib import Path
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# 模型配置
class ModelConfig(BaseModel):
    provider: str = ""
    model: str = ""
    config: Dict[str, Any] = {"temperature": 0.7, "max_tokens": 2048}

# 知识库检索配置
class RetrievalConfig(BaseModel):
    top_k: int = 3
    similarity_threshold: float = 0.5

# 知识库配置
class KnowledgeConfig(BaseModel):
    enabled: bool = False
    databases: List[str] = []
    retrieval_config: RetrievalConfig = RetrievalConfig()

# MCP配置
class McpConfig(BaseModel):
    enabled: bool = False
    servers: List[str] = []

# 智能体配置
class AgentConfig(BaseModel):
    name: str = ""
    description: str = ""
    system_prompt: str = ""
    model_config: ModelConfig = ModelConfig()
    knowledge_config: KnowledgeConfig = KnowledgeConfig()
    mcp_config: McpConfig = McpConfig()
    tools: List[str] = []
    
    def save_to_yaml(self, agents_dir: str = None):
        """将智能体配置保存为YAML文件
        
        Args:
            agents_dir: 保存目录路径，默认为 server/config/agents
        
        Returns:
            保存的文件路径
        """
        # 如果未指定目录，使用默认的agents目录
        if agents_dir is None:
            agents_dir = Path(__file__).parent / "agents"
        else:
            agents_dir = Path(agents_dir)
            
        # 确保目录存在
        agents_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名，使用智能体名称作为文件名，添加.private.yaml后缀
        file_name = f"{self.name}.private.yaml"
        file_path = agents_dir / file_name
        
        # 将配置转换为字典
        config_dict = self.model_dump()
        
        # 保存为YAML文件
        print('save to yaml', file_path)
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(config_dict, f, allow_unicode=True, indent=2)
            
        return str(file_path)

    @staticmethod
    def load_from_yaml(file_path: str):
        """从YAML文件加载智能体配置
        
        Args:
            file_path: YAML文件路径
        
        Returns:
            AgentConfig: 加载的智能体配置
        """
        with open(file_path, "r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f)
        return AgentConfig(**config_dict)

if __name__ == "__main__":
    # 创建一个测试智能体
    agent = AgentConfig(
        name="test_agent",
        description="This is a test agent",
        system_prompt="You are a helpful assistant.",
        model_config=ModelConfig(
            provider="openai",
            model="gpt-3.5-turbo",
            config={"temperature": 0.7, "max_tokens": 2048}
        ),
        knowledge_config=KnowledgeConfig(
            enabled=True,
            databases=["db1", "db2"],
            retrieval_config=RetrievalConfig(top_k=5, similarity_threshold=0.8)
        ),
        mcp_config=McpConfig(
            enabled=True,
            servers=["skill1", "skill2"]
        ),
        tools=["tool1", "tool2"]
    )
    
    # Save the agent to a YAML file
    saved_path = agent.save_to_yaml()
    print(f"Agent configuration saved to: {saved_path}")

    # Load the agent from the YAML file
    loaded_agent = AgentConfig.load_from_yaml(saved_path)
    print("\nLoaded agent configuration:")
    print(loaded_agent)
