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


# 模型提供商配置模型
class ModelProvider(BaseModel):
    name: str
    url: str
    base_url: str
    default: str
    env: List[str]
    models: List[str]
    api_key: Optional[str] = None

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
    # 配置路径
    config_path: Path = Field(default=CONFIG_PATH)
    models_path: Path = Field(default=MODELS_PATH)
    models_private_path: Path = Field(default=MODELS_PRIVATE_PATH)
    
    # 模型配置
    model_configs: Optional[ModelConfigs] = None
    
    # 基础配置
    config_file: Optional[str] = None
    storage_dir: str = Field(default="storage", description="存储目录")
    model_dir: str = Field(default="", description="模型目录")
    
    # 功能开关
    enable_reranker: bool = Field(default=False, description="是否开启重排序")
    enable_web_search: bool = Field(default=False, description="是否开启网页搜索")
    enable_knowledge_base: bool = Field(default=True, description="是否开启知识库")
    enable_agent_management: bool = Field(default=True, description="是否开启智能体管理")
    
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
    
    # 自定义模型
    custom_models: List[dict] = Field(default_factory=list)

    class Config:
        env_file = str(Path(__file__).parent.parent / ".env")
        env_file_encoding = "utf-8"
        extra = "allow"  # 允许任意字段


    """配置管理器"""
    def __init__(self):
        # 调用父类的__init__方法初始化属性
        super().__init__()
        
        # 加载模型配置
        self.model_configs = self._load_model_configs()
        
        # 加载应用配置
        self._load_app_config()
        
        # 初始化提供商状态
        self._init_provider_status()
        print("AppConfig initialization complete")
    
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
        
        # 合并配置：以公共配置为基础，私有配置只覆盖API key等敏感信息
        merged_config = {
            "MODEL_NAMES": {},
            "EMBED_MODEL_INFO": {},
            "RERANKER_LIST": {}
        }
        
        # 处理 MODEL_NAMES：以公共配置为准，只从私有配置获取API key
        for provider_name, provider_config in public_config["MODEL_NAMES"].items():
            merged_provider = provider_config.copy()
            if provider_name in private_config.get("MODEL_NAMES", {}):
                private_provider = private_config["MODEL_NAMES"][provider_name]
                # 只覆盖API key，保持其他配置与公共配置一致
                if "api_key" in private_provider:
                    merged_provider["api_key"] = private_provider["api_key"]
            merged_config["MODEL_NAMES"][provider_name] = merged_provider
        
        # 处理 EMBED_MODEL_INFO：以公共配置为准，只从私有配置获取API key
        for model_name, model_config in public_config["EMBED_MODEL_INFO"].items():
            merged_model = model_config.copy()
            if model_name in private_config.get("EMBED_MODEL_INFO", {}):
                private_model = private_config["EMBED_MODEL_INFO"][model_name]
                # 只覆盖API key，保持其他配置与公共配置一致
                if "api_key" in private_model:
                    merged_model["api_key"] = private_model["api_key"]
            merged_config["EMBED_MODEL_INFO"][model_name] = merged_model
        
        # 处理 RERANKER_LIST：以公共配置为准，只从私有配置获取API key
        for reranker_name, reranker_config in public_config["RERANKER_LIST"].items():
            merged_reranker = reranker_config.copy()
            if reranker_name in private_config.get("RERANKER_LIST", {}):
                private_reranker = private_config["RERANKER_LIST"][reranker_name]
                # 只覆盖API key，保持其他配置与公共配置一致
                if "api_key" in private_reranker:
                    merged_reranker["api_key"] = private_reranker["api_key"]
            merged_config["RERANKER_LIST"][reranker_name] = merged_reranker
        
        return ModelConfigs(**merged_config)
    
    def _load_app_config(self):
        """加载应用配置"""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            # 处理 tavily_api_key 和 tavily_base_url
            if "tavily_api_key" in data and (data["tavily_api_key"] is None or str(data["tavily_api_key"]).strip() == ""):
                data["tavily_api_key"] = None
            if "tavily_base_url" in data and (data["tavily_base_url"] is None or str(data["tavily_base_url"]).strip() == ""):
                data["tavily_base_url"] = None
            
            # 直接将配置项设置为实例属性
            for key, value in data.items():
                # 跳过路径相关属性，这些已经在__init__中初始化
                if key not in ['config_path', 'models_path', 'models_private_path']:
                    setattr(self, key, value)
    
    def _init_provider_status(self):
        """初始化提供商启用状态"""
        if not self.provider_enabled_status:
            self.provider_enabled_status = {}
        
        # 为所有模型提供商设置默认启用状态
        for provider in self.model_configs.MODEL_NAMES.keys():
            if provider not in self.provider_enabled_status:
                self.provider_enabled_status[provider] = True
    
    def save(self):
        """保存应用配置到文件"""
        # 收集所有AppConfig类型的属性
        config_data = {}
        for key in AppConfig.__annotations__.keys():
            if hasattr(self, key):
                config_data[key] = getattr(self, key)
        
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, allow_unicode=True, indent=2)
    
    def save_models(self):
        """保存模型配置到私有文件"""
        # 只保存API key等敏感信息到私有配置文件
        data = {
            "MODEL_NAMES": {},
            "EMBED_MODEL_INFO": {},
            "RERANKER_LIST": {}
        }
        
        # 保存模型提供商的API key
        for provider_name, provider_config in self.model_configs.MODEL_NAMES.items():
            if hasattr(provider_config, 'api_key') and provider_config.api_key:
                data["MODEL_NAMES"][provider_name] = {
                    "api_key": provider_config.api_key
                }
        
        # 保存embedding模型的API key
        for model_name, model_config in self.model_configs.EMBED_MODEL_INFO.items():
            if hasattr(model_config, 'api_key') and model_config.api_key:
                data["EMBED_MODEL_INFO"][model_name] = {
                    "api_key": model_config.api_key
                }
        
        # 保存reranker模型的API key
        for reranker_name, reranker_config in self.model_configs.RERANKER_LIST.items():
            if hasattr(reranker_config, 'api_key') and reranker_config.api_key:
                data["RERANKER_LIST"][reranker_name] = {
                    "api_key": reranker_config.api_key
                }
        
        with open(self.models_private_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, indent=2)
    
    def _save_models_to_file(self):
        """保存模型配置到私有文件（向后兼容别名）"""
        self.save_models()
    
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
            # 将API key保存到配置文件中
            provider_config.api_key = config_data["api_key"]
        
        # 保存到私有配置文件
        self.save_models()
    
    def set_provider_enabled_status(self, provider: str, enabled: bool):
        """设置提供商启用状态"""
        if provider not in self.model_configs.MODEL_NAMES:
            raise ValueError(f"模型提供商 {provider} 不存在")
        
        self.provider_enabled_status[provider] = enabled
        self.save()
    
    def add_provider_model(self, provider: str, model_name: str):
        """为模型提供商添加模型"""
        if provider not in self.model_configs.MODEL_NAMES:
            raise ValueError(f"模型提供商 {provider} 不存在")
        
        if model_name not in self.model_configs.MODEL_NAMES[provider].models:
            self.model_configs.MODEL_NAMES[provider].models.append(model_name)
            self.save_models()
    
    def remove_provider_model(self, provider: str, model_name: str):
        """从模型提供商删除模型"""
        if provider not in self.model_configs.MODEL_NAMES:
            raise ValueError(f"模型提供商 {provider} 不存在")
        
        if model_name in self.model_configs.MODEL_NAMES[provider].models:
            self.model_configs.MODEL_NAMES[provider].models.remove(model_name)
            self.save_models()
    
    def toggle_provider_status(self, provider: str, enabled: bool):
        """切换模型提供商启用状态"""
        self.set_provider_enabled_status(provider, enabled)
    
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
    
    # 代理 AppConfig 的属性访问 - 现在直接使用实例属性
    def __setattr__(self, name, value):
        super().__setattr__(name, value)
    
    def dump_config(self):
        """导出配置信息，包含配置项元数据"""
        # 收集所有AppConfig类型的属性
        config_data = {}
        for key in AppConfig.__annotations__.keys():
            if hasattr(self, key):
                config_data[key] = getattr(self, key)
        
        # 添加模型配置数据，兼容前端需求
        config_data["model_names"] = self.model_configs.MODEL_NAMES
        config_data["embed_model_names"] = self.model_configs.EMBED_MODEL_INFO
        config_data["reranker_names"] = self.model_configs.RERANKER_LIST
        
        # 添加模型提供商状态信息
        model_provider_status = {}
        for provider in self.model_configs.MODEL_NAMES.keys():
            provider_config = self.model_configs.MODEL_NAMES[provider]
            
            # 优先检查配置文件中是否已配置 api_key
            if hasattr(provider_config, 'api_key') and provider_config.api_key:
                model_provider_status[provider] = True
            else:
                # 如果没有配置文件中的 api_key，则检查环境变量
                env_key = provider_config.env[0] if provider_config.env else None
                if env_key:
                    model_provider_status[provider] = bool(os.getenv(env_key))
                else:
                    model_provider_status[provider] = True  # 如果没有环境变量要求，默认可用
        
        config_data["model_provider_status"] = model_provider_status
        
        # 添加配置项元数据
        config_data["_config_items"] = {
            "model_provider": {
                "des": "模型提供商",
                "choices": list(self.model_configs.MODEL_NAMES.keys())
            },
            "model_name": {
                "des": "模型名称",
                "choices": []
            },
            "embed_model": {
                "des": "Embedding 模型",
                "choices": list(self.model_configs.EMBED_MODEL_INFO.keys())
            },
            "reranker": {
                "des": "Re-Ranker 模型",
                "choices": list(self.model_configs.RERANKER_LIST.keys())
            },
            "enable_reranker": {
                "des": "是否开启重排序"
            },
            "enable_web_search": {
                "des": "是否开启网页搜索"
            },
            "tavily_api_key": {
                "des": "Tavily API Key"
            },
            "tavily_base_url": {
                "des": "Tavily API基础URL"
            },
            "storage_dir": {
                "des": "存储目录"
            },
            "model_dir": {
                "des": "模型目录"
            }
        }
        
        # 根据当前选择的模型提供商更新模型名称选项
        current_provider = config_data.get("model_provider", "openai")
        if current_provider in self.model_configs.MODEL_NAMES:
            config_data["_config_items"]["model_name"]["choices"] = self.model_configs.MODEL_NAMES[current_provider].models
        
        return config_data
    
    def update(self, items: dict):
        """批量更新配置"""
        for key, value in items.items():
            if key in AppConfig.__annotations__:
                setattr(self, key, value)
    


# 创建全局配置实例
config = AppConfig()
