import os
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
import yaml
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).parent.parent.parent
CONFIG_PATH = PROJECT_DIR / "server/config"

SELECTED_CONFIG_PATH = CONFIG_PATH / "base_config.yaml"  # 当前选中的配置文件
SITE_INFO_PATH = CONFIG_PATH / "site_info.yaml"  # 网站信息配置文件
MODELS_PATH = CONFIG_PATH / "model_provider.yaml"  # 模型配置文件
MODELS_PRIVATE_PATH = CONFIG_PATH / "model_provider.private.yml"  # 模型私有配置文件

# 延迟导入logger以避免循环导入
def get_logger():
    from src.utils.logging_config import logger
    return logger

DEFAULT_MOCK_API = "this_is_mock_api_key_in_frontend"

# 加载 .env 文件
load_dotenv(str(Path(PROJECT_DIR) / "server" / ".env"))
print(f"load_dotenv: {Path(PROJECT_DIR) / 'server' / '.env'}")


class ModelProviderConfig(BaseModel):
    """模型提供商配置"""
    name: str = ""
    base_url: str = ""
    api_key: str = ""
    env: List[str] = Field(default_factory=list)
    models: List[str] = Field(default_factory=list)
    url: str = ""
    default: str = ""


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
    
    # 内部状态（不保存到文件）
    model_provider_status: Dict[str, bool] = Field(default_factory=dict)
    valuable_model_provider: List[str] = Field(default_factory=list)
    
    # 配置项元数据
    _config_items: Dict[str, Dict] = Field(default_factory=dict)
    
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
    
    def add_item(self, key: str, default: Any, des: str = None, choices: List = None):
        """添加配置项"""
        setattr(self, key, default)
        self._config_items[key] = {"default": default, "des": des, "choices": choices}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，排除内部状态"""
        exclude_fields = {
            'model_provider_status', 'valuable_model_provider', 'model_dir', '_config_items'
        }
        return {k: v for k, v in self.dict().items() if k not in exclude_fields}


class Config:
    """配置管理器 - 保持向后兼容的接口"""
    _instance = None
    _initialized = False
    _config: Optional[AppConfig] = None
    _model_names: Dict[str, Dict] = None
    _embed_model_names: Dict[str, Any] = None
    _reranker_names: Dict[str, Any] = None
    _config_items: Dict[str, Dict] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._config_items = {}
        self.storage_dir = os.getenv("SAVE_DIR", "storage")
        self.config_file = str(Path(SELECTED_CONFIG_PATH))
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        
        self._update_models_from_file()
        self._init_config()
        self.load()
        self.handle_self()
        self._init_provider_enabled_status()
        
        self._initialized = True
    
    def _init_config(self):
        """初始化配置"""
        # 创建AppConfig实例
        self._config = AppConfig()
        
        # 添加默认配置项
        self.add_item("enable_reranker", default=False, des="是否开启重排序")
        self.add_item("enable_web_search", default=False, des="是否开启网页搜索")
        self.add_item("tavily_api_key", default="", des="Tavily API Key")
        self.add_item("tavily_base_url", default="https://api.tavily.com", des="Tavily API基础URL")
        self.add_item("model_provider", default="openai", des="模型提供商", choices=list(self._model_names.keys()))
        self.add_item("model_name", default="gpt-4o-mini", des="模型名称")
        self.add_item("embed_model", default="siliconflow/BAAI/bge-m3", des="Embedding 模型", choices=list(self._embed_model_names.keys()))
        self.add_item("reranker", default="siliconflow/BAAI/bge-reranker-v2-m3", des="Re-Ranker 模型", choices=list(self._reranker_names.keys()))
    
    def _update_models_from_file(self):
        """从 models.yaml 和 models.private.yml 中更新 MODEL_NAMES"""
        with open(Path(MODELS_PATH), encoding="utf-8") as f:
            _models = yaml.safe_load(f)

        # 尝试打开一个 models.private.yml 文件，用来覆盖 models.yaml 中的配置
        try:
            with open(Path(MODELS_PRIVATE_PATH), encoding="utf-8") as f:
                _models_private = yaml.safe_load(f)
        except FileNotFoundError:
            _models_private = {}

        self._model_names = {**_models["MODEL_NAMES"], **_models_private.get("MODEL_NAMES", {})}
        self._embed_model_names = {**_models["EMBED_MODEL_INFO"], **_models_private.get("EMBED_MODEL_INFO", {})}
        self._reranker_names = {**_models["RERANKER_LIST"], **_models_private.get("RERANKER_LIST", {})}
    
    def _save_models_to_file(self):
        """保存模型配置到文件"""
        _models = {
            "MODEL_NAMES": self._model_names,
            "EMBED_MODEL_INFO": self._embed_model_names,
            "RERANKER_LIST": self._reranker_names,
        }
        with open(Path(MODELS_PRIVATE_PATH), "w", encoding="utf-8") as f:
            yaml.dump(_models, f, indent=2, allow_unicode=True)
    
    def _init_provider_enabled_status(self):
        """初始化提供商启用状态"""
        if not hasattr(self._config, "provider_enabled_status") or self._config.provider_enabled_status is None:
            self._config.provider_enabled_status = {}

        # 确保model_names已经初始化
        if not hasattr(self, "_model_names") or self._model_names is None:
            get_logger().warning("model_names not initialized, skipping provider_enabled_status initialization")
            return

        # 为所有模型提供商设置默认启用状态
        for provider in self._model_names.keys():
            if provider not in self._config.provider_enabled_status:
                # 默认启用，除非明确设置为False
                self._config.provider_enabled_status[provider] = True
    
    def get_provider_enabled_status(self, provider: str = None):
        """获取提供商启用状态"""
        # 确保provider_enabled_status是字典类型
        if not hasattr(self._config, "provider_enabled_status") or self._config.provider_enabled_status is None:
            self._config.provider_enabled_status = {}

        if provider:
            return self._config.provider_enabled_status.get(provider, True)
        return self._config.provider_enabled_status

    def set_provider_enabled_status(self, provider: str, enabled: bool):
        """设置提供商启用状态"""
        if provider not in self._model_names:
            raise ValueError(f"模型提供商 {provider} 不存在")

        self._config.provider_enabled_status[provider] = enabled
        self.save()
        get_logger().info(f"模型提供商 {provider} 启用状态已设置为: {enabled}")

    def toggle_provider_status(self, provider: str, enabled: bool):
        """切换提供商启用状态"""
        return self.set_provider_enabled_status(provider, enabled)
    
    def add_item(self, key, default, des=None, choices=None):
        """添加配置项"""
        setattr(self._config, key, default)
        self._config_items[key] = {"default": default, "des": des, "choices": choices}
    
    def __getattr__(self, key):
        """获取配置值"""
        if hasattr(self._config, key):
            return getattr(self._config, key)
        return super().__getattr__(key)
    
    def __setattr__(self, key, value):
        """设置配置值"""
        if key.startswith('_') or key in ['_instance', '_initialized', '_config', '_model_names', '_embed_model_names', '_reranker_names', '_config_items']:
            super().__setattr__(key, value)
        else:
            setattr(self._config, key, value)
    
    def __getitem__(self, key):
        """字典式访问"""
        return getattr(self._config, key)
    
    def __setitem__(self, key, value):
        """字典式设置"""
        setattr(self._config, key, value)
    
    def get(self, key, default=None):
        """获取配置值"""
        return getattr(self._config, key, default)
    
    def update(self, other):
        """更新配置"""
        for key, value in other.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
    
    def __dict__(self):
        """转换为字典"""
        blocklist = [
            "_config_items",
            "model_names",
            "model_provider_status",
            "embed_model_names",
            "reranker_names",
        ]
        result = {k: v for k, v in self._config.dict().items() if k not in blocklist}
        # 添加provider_enabled_status到配置中
        if hasattr(self._config, "provider_enabled_status"):
            result["provider_enabled_status"] = self._config.provider_enabled_status
        return result
    
    def update_provider_config(self, provider: str, config_data: dict):
        """更新模型提供商配置"""
        if provider not in self._model_names:
            raise ValueError(f"模型提供商 {provider} 不存在")

        # 更新配置
        if "base_url" in config_data:
            self._model_names[provider]["base_url"] = config_data["base_url"]
        if "api_key" in config_data:
            # 将API key保存到环境变量
            env_key = self._model_names[provider].get("env", [None])[0]
            if env_key:
                os.environ[env_key] = config_data["api_key"]
            # 同步写入到配置，保证保存到文件
            self._model_names[provider]["api_key"] = config_data["api_key"]

        # 保存到配置文件
        self._save_models_to_file()
        get_logger().info(f"模型提供商 {provider} 配置已更新")

    def add_provider_model(self, provider: str, model_name: str):
        """为模型提供商添加模型"""
        if provider not in self._model_names:
            raise ValueError(f"模型提供商 {provider} 不存在")

        if "models" not in self._model_names[provider]:
            self._model_names[provider]["models"] = []

        if model_name not in self._model_names[provider]["models"]:
            self._model_names[provider]["models"].append(model_name)
            self._save_models_to_file()
            get_logger().info(f"模型 {model_name} 已添加到 {provider}")
            return True
        else:
            raise ValueError(f"模型 {model_name} 已存在于 {provider} 中")

    def remove_provider_model(self, provider: str, model_name: str):
        """从模型提供商删除模型"""
        if provider not in self._model_names:
            raise ValueError(f"模型提供商 {provider} 不存在")

        if "models" not in self._model_names[provider]:
            raise ValueError(f"模型提供商 {provider} 没有配置模型列表")

        if model_name in self._model_names[provider]["models"]:
            self._model_names[provider]["models"].remove(model_name)
            self._save_models_to_file()
            get_logger().info(f"模型 {model_name} 已从 {provider} 中删除")
            return True
        else:
            raise ValueError(f"模型 {model_name} 不存在于 {provider} 中")

    def reload_models_config(self):
        """重新加载模型配置"""
        self._update_models_from_file()
        self.handle_self()
        get_logger().info("模型配置已重新加载")

    def get_provider_config(self, provider: str):
        """获取模型提供商配置"""
        if provider not in self._model_names:
            raise ValueError(f"模型提供商 {provider} 不存在")

        provider_config = self._model_names[provider]
        return {
            "provider": provider,
            "name": provider_config.get("name", ""),
            "base_url": provider_config.get("base_url", ""),
            "default": provider_config.get("default", ""),
            "env": provider_config.get("env", []),
            "models": provider_config.get("models", []),
            "url": provider_config.get("url", ""),
        }

    def handle_self(self):
        """处理配置"""
        self._config.model_dir = os.environ.get("MODEL_DIR", "")

        if self._config.model_dir:
            if os.path.exists(self._config.model_dir):
                get_logger().debug(f"The model directory （{self._config.model_dir}） contains the following folders: {os.listdir(self._config.model_dir)}")
            else:
                get_logger().warning(
                    f"Warning: The model directory （{self._config.model_dir}） does not exist. If not configured, please ignore it. If configured, please check if the configuration is correct;"
                    "For example, the mapping in the docker-compose file"
                )

        # 检查模型提供商的环境变量
        conds = {}
        self._config.model_provider_status = {}
        for provider in self._model_names:
            conds[provider] = self._model_names[provider]["env"]
            conds_bool = [bool(os.getenv(_k)) for _k in conds[provider]]
            self._config.model_provider_status[provider] = all(conds_bool)

        # 处理Tavily配置
        if os.getenv("TAVILY_API_KEY"):
            self._config.tavily_api_key = os.getenv("TAVILY_API_KEY")
            # 如果配置了API Key但enable_web_search为False，则自动启用
            if not self._config.enable_web_search:
                self._config.enable_web_search = True
                get_logger().info("检测到TAVILY_API_KEY环境变量，自动启用网页搜索功能")

        # 如果配置了tavily_api_key，同步到环境变量
        if hasattr(self._config, "tavily_api_key") and self._config.tavily_api_key:
            os.environ["TAVILY_API_KEY"] = self._config.tavily_api_key

        self._config.valuable_model_provider = [k for k, v in self._config.model_provider_status.items() if v]
        assert len(self._config.valuable_model_provider) > 0, f"No model provider available, please check your `.env` file. API_KEY_LIST: {conds}"

    def load(self):
        """根据传入的文件覆盖掉默认配置"""
        get_logger().info(f"Loading config from {self.config_file}")
        if self.config_file is not None and os.path.exists(self.config_file):
            if self.config_file.endswith(".yaml"):
                with open(self.config_file) as f:
                    content = f.read()
                    if content:
                        local_config = yaml.safe_load(content)
                        self.update(local_config)

                        # 加载provider_enabled_status
                        if "provider_enabled_status" in local_config:
                            loaded_status = local_config["provider_enabled_status"]
                            # 确保provider_enabled_status是字典类型，避免None值
                            if loaded_status is not None:
                                self._config.provider_enabled_status = loaded_status
                            else:
                                self._config.provider_enabled_status = {}
                    else:
                        print(f"{self.config_file} is empty.")
            else:
                get_logger().warning(f"Unknown config file type {self.config_file}")

    def save(self):
        """保存配置到文件"""
        get_logger().info(f"Saving config to {self.config_file}")
        config_dict = self._config.to_dict()
        
        if self.config_file.endswith(".yaml"):
            with open(self.config_file, "w+") as f:
                yaml.dump(config_dict, f, indent=2, allow_unicode=True)
        else:
            get_logger().warning(f"Unknown config file type {self.config_file}, save as yaml")
            with open(self.config_file, "w+") as f:
                yaml.dump(config_dict, f, indent=2, allow_unicode=True)
        get_logger().info(f"Config file {self.config_file} saved")

    def dump_config(self):
        """导出配置"""
        return json.loads(self._config.json())

    def compare_custom_models(self, value):
        """
        比较 custom_models 中的 api_key，如果输入的 api_key 与当前的 api_key 相同，则不修改
        如果输入的 api_key 为 DEFAULT_MOCK_API，则使用当前的 api_key
        """
        current_models_dict = {model["custom_id"]: model.get("api_key") for model in self.get("custom_models", [])}

        for i, model in enumerate(value):
            input_custom_id = model.get("custom_id")
            input_api_key = model.get("api_key")

            if input_custom_id in current_models_dict:
                current_api_key = current_models_dict[input_custom_id]
                if input_api_key == DEFAULT_MOCK_API or input_api_key == current_api_key:
                    value[i]["api_key"] = current_api_key

        return value
    
    # 属性访问器，保持向后兼容
    @property
    def model_names(self):
        return self._model_names
    
    @property
    def embed_model_names(self):
        return self._embed_model_names
    
    @property
    def reranker_names(self):
        return self._reranker_names


# 创建全局配置实例
config = Config()
