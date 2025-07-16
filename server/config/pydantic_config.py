import os
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from pydantic import BaseModel, Field, validator
from pydantic.settings import BaseSettings
import yaml
from dotenv import load_dotenv

# 延迟导入logger以避免循环导入
def get_logger():
    from src.utils.logging_config import logger
    return logger

PROJECT_DIR = Path(__file__).parent.parent.parent
CONFIG_PATH = PROJECT_DIR / "server/config"
SELECTED_CONFIG_PATH = CONFIG_PATH / "base_config.yaml"
MODELS_PATH = CONFIG_PATH / "model_provider.yaml"
MODELS_PRIVATE_PATH = CONFIG_PATH / "model_provider.private.yml"

# 加载 .env 文件
load_dotenv(str(Path(PROJECT_DIR) / "server" / ".env"))


class ModelProviderConfig(BaseModel):
    """模型提供商配置"""
    name: str
    base_url: str = ""
    api_key: str = ""
    env: List[str] = []
    models: List[str] = []
    url: str = ""
    default: str = ""


class ModelConfig(BaseModel):
    """模型相关配置"""
    model_names: Dict[str, ModelProviderConfig] = Field(default_factory=dict)
    embed_model_names: Dict[str, Any] = Field(default_factory=dict)
    reranker_names: Dict[str, Any] = Field(default_factory=dict)


class AppConfig(BaseSettings):
    """应用配置类"""
    
    # 功能选项
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
    
    # 提供商启用状态
    provider_enabled_status: Dict[str, bool] = Field(default_factory=dict)
    
    # 存储配置
    storage_dir: str = Field(default="storage", description="存储目录")
    model_dir: str = Field(default="", description="模型目录")
    
    # 内部状态
    model_provider_status: Dict[str, bool] = Field(default_factory=dict)
    valuable_model_provider: List[str] = Field(default_factory=list)
    
    class Config:
        env_file = str(Path(PROJECT_DIR) / "server" / ".env")
        env_file_encoding = 'utf-8'
    
    @validator('tavily_api_key')
    def sync_tavily_env(cls, v):
        """同步Tavily API Key到环境变量"""
        if v:
            os.environ["TAVILY_API_KEY"] = v
            get_logger().info("Tavily API Key已同步到环境变量")
        return v
    
    @validator('enable_web_search')
    def auto_enable_web_search(cls, v, values):
        """如果检测到Tavily API Key，自动启用网页搜索"""
        if not v and os.getenv("TAVILY_API_KEY"):
            get_logger().info("检测到TAVILY_API_KEY环境变量，自动启用网页搜索功能")
            return True
        return v


class ConfigManager:
    """配置管理器"""
    _instance = None
    _config: Optional[AppConfig] = None
    _model_config: Optional[ModelConfig] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._load_model_config()
            self._config = self._load_app_config()
            self._post_init()
    
    def _load_model_config(self):
        """加载模型配置"""
        with open(Path(MODELS_PATH), encoding="utf-8") as f:
            _models = yaml.safe_load(f)
        
        try:
            with open(Path(MODELS_PRIVATE_PATH), encoding="utf-8") as f:
                _models_private = yaml.safe_load(f)
        except FileNotFoundError:
            _models_private = {}
        
        model_names = {**_models["MODEL_NAMES"], **_models_private.get("MODEL_NAMES", {})}
        embed_model_names = {**_models["EMBED_MODEL_INFO"], **_models_private.get("EMBED_MODEL_INFO", {})}
        reranker_names = {**_models["RERANKER_LIST"], **_models_private.get("RERANKER_LIST", {})}
        
        self._model_config = ModelConfig(
            model_names=model_names,
            embed_model_names=embed_model_names,
            reranker_names=reranker_names
        )
    
    def _load_app_config(self) -> AppConfig:
        """加载应用配置"""
        # 从环境变量和默认值创建配置
        config = AppConfig()
        
        # 从YAML文件加载配置
        if SELECTED_CONFIG_PATH.exists():
            with open(SELECTED_CONFIG_PATH, 'r', encoding='utf-8') as f:
                yaml_config = yaml.safe_load(f) or {}
                # 更新配置
                for key, value in yaml_config.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
        
        return config
    
    def _post_init(self):
        """初始化后处理"""
        # 设置模型目录
        self._config.model_dir = os.environ.get("MODEL_DIR", "")
        
        # 检查模型提供商状态
        self._check_provider_status()
        
        # 初始化提供商启用状态
        self._init_provider_enabled_status()
        
        # 验证配置
        self._validate_config()
    
    def _check_provider_status(self):
        """检查模型提供商状态"""
        conds = {}
        self._config.model_provider_status = {}
        
        for provider, provider_config in self._model_config.model_names.items():
            env_keys = provider_config.get("env", [])
            conds[provider] = env_keys
            conds_bool = [bool(os.getenv(_k)) for _k in env_keys]
            self._config.model_provider_status[provider] = all(conds_bool)
        
        self._config.valuable_model_provider = [
            k for k, v in self._config.model_provider_status.items() if v
        ]
        
        if not self._config.valuable_model_provider:
            raise ValueError(f"No model provider available, please check your `.env` file. API_KEY_LIST: {conds}")
    
    def _init_provider_enabled_status(self):
        """初始化提供商启用状态"""
        for provider in self._model_config.model_names.keys():
            if provider not in self._config.provider_enabled_status:
                self._config.provider_enabled_status[provider] = True
    
    def _validate_config(self):
        """验证配置"""
        # 验证模型提供商是否存在
        if self._config.model_provider not in self._model_config.model_names:
            raise ValueError(f"模型提供商 {self._config.model_provider} 不存在")
        
        # 验证模型目录
        if self._config.model_dir and not os.path.exists(self._config.model_dir):
            get_logger().warning(
                f"Warning: The model directory ({self._config.model_dir}) does not exist. "
                "If not configured, please ignore it. If configured, please check if the configuration is correct."
            )
    
    def save(self):
        """保存配置到文件"""
        config_dict = self._config.dict(exclude={
            'model_provider_status', 'valuable_model_provider', 'model_dir'
        })
        
        with open(SELECTED_CONFIG_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, indent=2, allow_unicode=True)
        
        get_logger().info(f"Config saved to {SELECTED_CONFIG_PATH}")
    
    def reload(self):
        """重新加载配置"""
        self._load_model_config()
        self._config = self._load_app_config()
        self._post_init()
        get_logger().info("Configuration reloaded")
    
    # 属性访问器
    @property
    def config(self) -> AppConfig:
        return self._config
    
    @property
    def model_names(self) -> Dict[str, ModelProviderConfig]:
        return self._model_config.model_names
    
    @property
    def embed_model_names(self) -> Dict[str, Any]:
        return self._model_config.embed_model_names
    
    @property
    def reranker_names(self) -> Dict[str, Any]:
        return self._model_config.reranker_names
    
    # 便捷方法
    def get(self, key: str, default=None):
        """获取配置值"""
        return getattr(self._config, key, default)
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        if hasattr(self._config, key):
            setattr(self._config, key, value)
        else:
            raise AttributeError(f"Configuration key '{key}' does not exist")
    
    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """获取模型提供商配置"""
        if provider not in self._model_config.model_names:
            raise ValueError(f"模型提供商 {provider} 不存在")
        
        provider_config = self._model_config.model_names[provider]
        return {
            "provider": provider,
            "name": provider_config.get("name", ""),
            "base_url": provider_config.get("base_url", ""),
            "default": provider_config.get("default", ""),
            "env": provider_config.get("env", []),
            "models": provider_config.get("models", []),
            "url": provider_config.get("url", ""),
        }
    
    def update_provider_config(self, provider: str, config_data: dict):
        """更新模型提供商配置"""
        if provider not in self._model_config.model_names:
            raise ValueError(f"模型提供商 {provider} 不存在")
        
        provider_config = self._model_config.model_names[provider]
        
        if "base_url" in config_data:
            provider_config["base_url"] = config_data["base_url"]
        if "api_key" in config_data:
            env_key = provider_config.get("env", [None])[0]
            if env_key:
                os.environ[env_key] = config_data["api_key"]
            provider_config["api_key"] = config_data["api_key"]
        
        self._save_models_to_file()
        get_logger().info(f"模型提供商 {provider} 配置已更新")
    
    def _save_models_to_file(self):
        """保存模型配置到文件"""
        _models = {
            "MODEL_NAMES": self._model_config.model_names,
            "EMBED_MODEL_INFO": self._model_config.embed_model_names,
            "RERANKER_LIST": self._model_config.reranker_names,
        }
        with open(Path(MODELS_PRIVATE_PATH), "w", encoding="utf-8") as f:
            yaml.dump(_models, f, indent=2, allow_unicode=True)


# 创建全局配置实例
config_manager = ConfigManager()

# 为了保持向后兼容，提供config属性
config = config_manager.config 