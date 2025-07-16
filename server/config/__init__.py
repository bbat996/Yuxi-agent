import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

# 配置文件路径常量
CONFIG_PATH = Path(__file__).parent / "base_config.yaml"
MODELS_PATH = Path(__file__).parent / "model_provider.yaml"
MODELS_PRIVATE_PATH = Path(__file__).parent / "model_provider.private.yml"
SITE_INFO_PATH = CONFIG_PATH / "site_info.yaml"  # 网站信息配置文件

# 模型提供商配置模型
class ModelProvider(BaseModel):
    name: str
    url: str
    base_url: str
    default: str
    env: List[str]
    models: List[str]

# Embedding 模型配置模型
class EmbedModel(BaseModel):
    name: str
    dimension: int
    base_url: str
    api_key: Optional[str] = None

# Reranker 模型配置模型
class RerankerModel(BaseModel):
    name: str
    base_url: str
    api_key: Optional[str] = None

# 模型配置集合
class ModelConfigs(BaseModel):
    MODEL_NAMES: Dict[str, ModelProvider]
    EMBED_MODEL_INFO: Dict[str, EmbedModel]
    RERANKER_LIST: Dict[str, RerankerModel]

# 主应用配置模型
class AppConfig(BaseSettings):
    # 基础配置
    config_file: Optional[str] = None
    storage_dir: str = Field(default="storage", description="存储目录")
    model_dir: str = Field(default="", description="模型目录")
    
    # 功能开关
    enable_reranker: bool = Field(default=False, description="是否开启重排序")
    enable_web_search: bool = Field(default=False, description="是否开启网页搜索")
    
    # Web搜索配置
    tavily_api_key: str = Field(default="", description="Tavily API Key")
    tavily_base_url: str = Field(default="https://api.tavily.com", description="Tavily API基础URL")
    
    # 模型配置
    model_provider: str = Field(default="openai", description="模型提供商")
    model_name: str = Field(default="gpt-4o-mini", description="模型名称")
    embed_model: str = Field(default="siliconflow/BAAI/bge-m3", description="Embedding 模型")
    reranker: str = Field(default="siliconflow/BAAI/bge-reranker-v2-m3", description="Re-Ranker 模型")
    
    # 提供商状态
    provider_enabled_status: Dict[str, bool] = Field(default_factory=dict)
    valuable_model_provider: List[str] = Field(default_factory=list)

    class Config:
        env_file = str(Path(__file__).parent.parent / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"

class Config:
    """配置管理器"""
    def __init__(self):
        self.config_path = CONFIG_PATH
        self.models_path = MODELS_PATH
        self.models_private_path = MODELS_PRIVATE_PATH
        
        # 加载模型配置
        self.model_configs = self._load_model_configs()
        
        # 加载应用配置
        self.app_config = self._load_app_config()
        
        # 初始化提供商状态
        self._init_provider_status()
    
    def _load_model_configs(self) -> ModelConfigs:
        """加载模型配置文件"""
        # 加载公共配置
        with open(self.models_path, "r", encoding="utf-8") as f:
            public_config = yaml.safe_load(f)
        
        # 尝试加载私有配置
        private_config = {}
        if self.models_private_path.exists():
            with open(self.models_private_path, "r", encoding="utf-8") as f:
                private_config = yaml.safe_load(f) or {}
        
        # 合并配置
        merged_config = {
            "MODEL_NAMES": {**public_config["MODEL_NAMES"], **private_config.get("MODEL_NAMES", {})},
            "EMBED_MODEL_INFO": {**public_config["EMBED_MODEL_INFO"], **private_config.get("EMBED_MODEL_INFO", {})},
            "RERANKER_LIST": {**public_config["RERANKER_LIST"], **private_config.get("RERANKER_LIST", {})}
        }
        
        return ModelConfigs(**merged_config)
    
    def _load_app_config(self) -> AppConfig:
        """加载应用配置"""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return AppConfig(**data)
        else:
            return AppConfig()
    
    def _init_provider_status(self):
        """初始化提供商启用状态"""
        if not self.app_config.provider_enabled_status:
            self.app_config.provider_enabled_status = {}
        
        # 为所有模型提供商设置默认启用状态
        for provider in self.model_configs.MODEL_NAMES.keys():
            if provider not in self.app_config.provider_enabled_status:
                self.app_config.provider_enabled_status[provider] = True
    
    def save(self):
        """保存应用配置到文件"""
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(self.app_config.dict(), f, allow_unicode=True, indent=2)
    
    def save_models(self):
        """保存模型配置到私有文件"""
        data = {
            "MODEL_NAMES": self.model_configs.MODEL_NAMES,
            "EMBED_MODEL_INFO": self.model_configs.EMBED_MODEL_INFO,
            "RERANKER_LIST": self.model_configs.RERANKER_LIST
        }
        with open(self.models_private_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, indent=2)
    
    def get_provider_config(self, provider: str) -> Optional[ModelProvider]:
        """获取模型提供商配置"""
        return self.model_configs.MODEL_NAMES.get(provider)
    
    def get_embed_model_config(self, model: str) -> Optional[EmbedModel]:
        """获取 Embedding 模型配置"""
        return self.model_configs.EMBED_MODEL_INFO.get(model)
    
    def get_reranker_config(self, model: str) -> Optional[RerankerModel]:
        """获取 Reranker 模型配置"""
        return self.model_configs.RERANKER_LIST.get(model)
    
    def update_provider_config(self, provider: str, config_data: dict):
        """更新模型提供商配置"""
        if provider not in self.model_configs.MODEL_NAMES:
            raise ValueError(f"模型提供商 {provider} 不存在")
        
        provider_config = self.model_configs.MODEL_NAMES[provider]
        
        # 更新配置
        if "base_url" in config_data:
            provider_config.base_url = config_data["base_url"]
        if "api_key" in config_data:
            # 将API key保存到环境变量
            env_key = provider_config.env[0] if provider_config.env else None
            if env_key:
                os.environ[env_key] = config_data["api_key"]
        
        self.save_models()
    
    def set_provider_enabled_status(self, provider: str, enabled: bool):
        """设置提供商启用状态"""
        if provider not in self.model_configs.MODEL_NAMES:
            raise ValueError(f"模型提供商 {provider} 不存在")
        
        self.app_config.provider_enabled_status[provider] = enabled
        self.save()
    
    # 属性访问器，保持向后兼容
    @property
    def model_names(self):
        return self.model_configs.MODEL_NAMES
    
    @property
    def embed_model_names(self):
        return self.model_configs.EMBED_MODEL_INFO
    
    @property
    def reranker_names(self):
        return self.model_configs.RERANKER_LIST
    
    # 代理 AppConfig 的属性访问
    def __getattr__(self, name):
        if hasattr(self.app_config, name):
            return getattr(self.app_config, name)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
    
    def __setattr__(self, name, value):
        if name in ['config_path', 'models_path', 'models_private_path', 'model_configs', 'app_config']:
            super().__setattr__(name, value)
        elif hasattr(self.app_config, name):
            setattr(self.app_config, name, value)
        else:
            super().__setattr__(name, value)

# 创建全局配置实例
config = Config()
