from pydantic import BaseModel, Field
from typing import List, Optional

class ModelParameters(BaseModel):
    """模型参数"""
    temperature: float = Field(0.7, description="模型温度")
    max_tokens: int = Field(2048, description="最大token数")

class RetrievalParams(BaseModel):
    """知识库检索参数"""
    top_k: int = Field(5, description="返回最相似的k个结果")
    similarity_threshold: float = Field(0.8, description="相似度阈值")

class AgentConfig(BaseModel):
    """智能体配置"""
    name: str = Field(..., description="智能体名称")
    description: str = Field(..., description="智能体描述")
    system_prompt: str = Field(..., description="系统提示")
    provider: str = Field(..., description="模型提供商")
    model_name: str = Field(..., description="模型名称")
    model_parameters: ModelParameters = Field(default_factory=ModelParameters, description="模型参数")
    tools: Optional[List[str]] = Field([], description="工具配置")
    mcp_skills: Optional[List[str]] = Field([], description="MCP技能配置")
    knowledge_databases: Optional[List[str]] = Field([], description="知识库配置")
    retrieval_params: RetrievalParams = Field(default_factory=RetrievalParams, description="知识库检索参数")
