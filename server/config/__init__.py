import os
import json
import yaml
from pathlib import Path
from src.utils.logging_config import logger
from dotenv import load_dotenv
from .constant import CONFIG_PATH, MODELS_PATH, MODELS_PRIVATE_PATH, PROJECT_DIR, SELECTED_CONFIG_PATH, SITE_INFO_PATH

DEFAULT_MOCK_API = "this_is_mock_api_key_in_frontend"
# 加载 .env 文件
load_dotenv(str(Path(PROJECT_DIR) / "server" / ".env"))
print(f"load_dotenv: {Path(PROJECT_DIR) / 'server' / '.env'}")


class SimpleConfig(dict):

    def __key(self, key):
        return "" if key is None else key  # 目前忘记了这里为什么要 lower 了，只能说配置项最好不要有大写的

    def __str__(self):
        return json.dumps(self)

    def __setattr__(self, key, value):
        self[self.__key(key)] = value

    def __getattr__(self, key):
        return self.get(self.__key(key))

    def __getitem__(self, key):
        return self.get(self.__key(key))

    def __setitem__(self, key, value):
        return super().__setitem__(self.__key(key), value)

    def __dict__(self):
        return {k: v for k, v in self.items()}

    def update(self, other):
        for key, value in other.items():
            self[key] = value


class Config(SimpleConfig):

    def __init__(self):
        super().__init__()
        self._config_items = {}
        self.storage_dir = os.getenv("SAVE_DIR", "storage")
        self.config_file = str(Path(SELECTED_CONFIG_PATH))
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

        self._update_models_from_file()

        ### >>> 默认配置
        # 功能选项
        self.add_item("enable_reranker", default=False, des="是否开启重排序")
        self.add_item(
            "enable_web_search",
            default=False,
            des="是否开启网页搜索（注：现阶段会根据 TAVILY_API_KEY 自动开启，无法手动配置，将会在下个版本移除此配置项）",
        )  # noqa: E501

        # 模型配置
        ## 注意这里是模型名，而不是具体的模型路径，默认使用 HuggingFace 的路径
        ## 如果需要自定义本地模型路径，则在 src/.env 中配置 MODEL_DIR
        self.add_item("model_provider", default="siliconflow", des="模型提供商", choices=list(self.model_names.keys()))
        self.add_item("model_name", default="Qwen/Qwen3-32B", des="模型名称")

        self.add_item("embed_model", default="siliconflow/BAAI/bge-m3", des="Embedding 模型", choices=list(self.embed_model_names.keys()))
        self.add_item(
            "reranker", default="siliconflow/BAAI/bge-reranker-v2-m3", des="Re-Ranker 模型", choices=list(self.reranker_names.keys()))
        ### <<< 默认配置结束

        self.load()
        self.handle_self()
        
        # 初始化提供商启用状态
        self._init_provider_enabled_status()

    def _init_provider_enabled_status(self):
        """初始化提供商启用状态"""
        if not hasattr(self, 'provider_enabled_status'):
            self.provider_enabled_status = {}
        
        # 为所有模型提供商设置默认启用状态
        for provider in self.model_names.keys():
            if provider not in self.provider_enabled_status:
                # 默认启用，除非明确设置为False
                self.provider_enabled_status[provider] = True

    def get_provider_enabled_status(self, provider: str = None):
        """获取提供商启用状态"""
        if provider:
            return self.provider_enabled_status.get(provider, True)
        return self.provider_enabled_status

    def set_provider_enabled_status(self, provider: str, enabled: bool):
        """设置提供商启用状态"""
        if provider not in self.model_names:
            raise ValueError(f"模型提供商 {provider} 不存在")
        
        self.provider_enabled_status[provider] = enabled
        self.save()
        logger.info(f"模型提供商 {provider} 启用状态已设置为: {enabled}")

    def toggle_provider_status(self, provider: str, enabled: bool):
        """切换提供商启用状态"""
        return self.set_provider_enabled_status(provider, enabled)

    def add_item(self, key, default, des=None, choices=None):
        self.__setattr__(key, default)
        self._config_items[key] = {"default": default, "des": des, "choices": choices}

    def __dict__(self):
        blocklist = [
            "_config_items",
            "model_names",
            "model_provider_status",
            "embed_model_names",
            "reranker_names",
        ]
        result = {k: v for k, v in self.items() if k not in blocklist}
        # 添加provider_enabled_status到配置中
        if hasattr(self, 'provider_enabled_status'):
            result['provider_enabled_status'] = self.provider_enabled_status
        return result

    def _update_models_from_file(self):
        """
        从 models.yaml 和 models.private.yml 中更新 MODEL_NAMES
        """

        with open(Path(MODELS_PATH), encoding="utf-8") as f:
            _models = yaml.safe_load(f)

        # 尝试打开一个 models.private.yml 文件，用来覆盖 models.yaml 中的配置
        try:
            with open(Path(MODELS_PRIVATE_PATH), encoding="utf-8") as f:
                _models_private = yaml.safe_load(f)
        except FileNotFoundError:
            _models_private = {}

        self.model_names = {**_models["MODEL_NAMES"], **_models_private.get("MODEL_NAMES", {})}
        self.embed_model_names = {**_models["EMBED_MODEL_INFO"], **_models_private.get("EMBED_MODEL_INFO", {})}
        self.reranker_names = {**_models["RERANKER_LIST"], **_models_private.get("RERANKER_LIST", {})}

    def _save_models_to_file(self):
        _models = {
            "MODEL_NAMES": self.model_names,
            "EMBED_MODEL_INFO": self.embed_model_names,
            "RERANKER_LIST": self.reranker_names,
        }
        with open(Path(MODELS_PRIVATE_PATH), "w", encoding="utf-8") as f:
            yaml.dump(_models, f, indent=2, allow_unicode=True)

    def update_provider_config(self, provider: str, config_data: dict):
        """更新模型提供商配置"""
        if provider not in self.model_names:
            raise ValueError(f"模型提供商 {provider} 不存在")
        
        # 更新配置
        if "base_url" in config_data:
            self.model_names[provider]["base_url"] = config_data["base_url"]
        if "api_key" in config_data:
            # 将API key保存到环境变量
            env_key = self.model_names[provider].get("env", [None])[0]
            if env_key:
                os.environ[env_key] = config_data["api_key"]
            # 同步写入到配置，保证保存到文件
            self.model_names[provider]["api_key"] = config_data["api_key"]
        
        # 保存到配置文件
        self._save_models_to_file()
        logger.info(f"模型提供商 {provider} 配置已更新")

    def add_provider_model(self, provider: str, model_name: str):
        """为模型提供商添加模型"""
        if provider not in self.model_names:
            raise ValueError(f"模型提供商 {provider} 不存在")
        
        if "models" not in self.model_names[provider]:
            self.model_names[provider]["models"] = []
        
        if model_name not in self.model_names[provider]["models"]:
            self.model_names[provider]["models"].append(model_name)
            self._save_models_to_file()
            logger.info(f"模型 {model_name} 已添加到 {provider}")
            return True
        else:
            raise ValueError(f"模型 {model_name} 已存在于 {provider} 中")

    def remove_provider_model(self, provider: str, model_name: str):
        """从模型提供商删除模型"""
        if provider not in self.model_names:
            raise ValueError(f"模型提供商 {provider} 不存在")
        
        if "models" not in self.model_names[provider]:
            raise ValueError(f"模型提供商 {provider} 没有配置模型列表")
        
        if model_name in self.model_names[provider]["models"]:
            self.model_names[provider]["models"].remove(model_name)
            self._save_models_to_file()
            logger.info(f"模型 {model_name} 已从 {provider} 中删除")
            return True
        else:
            raise ValueError(f"模型 {model_name} 不存在于 {provider} 中")

    def reload_models_config(self):
        """重新加载模型配置"""
        self._update_models_from_file()
        self.handle_self()
        logger.info("模型配置已重新加载")

    def get_provider_config(self, provider: str):
        """获取模型提供商配置"""
        if provider not in self.model_names:
            raise ValueError(f"模型提供商 {provider} 不存在")
        
        provider_config = self.model_names[provider]
        return {
            "provider": provider,
            "name": provider_config.get("name", ""),
            "base_url": provider_config.get("base_url", ""),
            "default": provider_config.get("default", ""),
            "env": provider_config.get("env", []),
            "models": provider_config.get("models", []),
            "url": provider_config.get("url", "")
        }

    def handle_self(self):
        """
        处理配置
        """
        self.model_dir = os.environ.get("MODEL_DIR", "")

        if self.model_dir:
            if os.path.exists(self.model_dir):
                logger.debug(f"The model directory （{self.model_dir}） contains the following folders: {os.listdir(self.model_dir)}")
            else:
                logger.warning(
                    f"Warning: The model directory （{self.model_dir}） does not exist. If not configured, please ignore it. If configured, please check if the configuration is correct;"
                    "For example, the mapping in the docker-compose file"
                )

        # 检查模型提供商的环境变量
        conds = {}
        self.model_provider_status = {}
        for provider in self.model_names:
            conds[provider] = self.model_names[provider]["env"]
            conds_bool = [bool(os.getenv(_k)) for _k in conds[provider]]
            self.model_provider_status[provider] = all(conds_bool)

        if os.getenv("TAVILY_API_KEY"):
            self.enable_web_search = True

        self.valuable_model_provider = [k for k, v in self.model_provider_status.items() if v]
        assert len(self.valuable_model_provider) > 0, f"No model provider available, please check your `.env` file. API_KEY_LIST: {conds}"

    def load(self):
        """根据传入的文件覆盖掉默认配置"""
        logger.info(f"Loading config from {self.config_file}")
        if self.config_file is not None and os.path.exists(self.config_file):
            if self.config_file.endswith(".yaml"):
                with open(self.config_file) as f:
                    content = f.read()
                    if content:
                        local_config = yaml.safe_load(content)
                        self.update(local_config)
                        
                        # 加载provider_enabled_status
                        if 'provider_enabled_status' in local_config:
                            self.provider_enabled_status = local_config['provider_enabled_status']
                    else:
                        print(f"{self.config_file} is empty.")
            else:
                logger.warning(f"Unknown config file type {self.config_file}")

    def save(self):
        logger.info(f"Saving config to {self.config_file}")
        if self.config_file.endswith(".yaml"):
            with open(self.config_file, "w+") as f:
                yaml.dump(self.__dict__(), f, indent=2, allow_unicode=True)
        else:
            logger.warning(f"Unknown config file type {self.config_file}, save as yaml")
            with open(self.config_file, "w+") as f:
                yaml.dump(self.__dict__(), f, indent=2, allow_unicode=True)
        logger.info(f"Config file {self.config_file} saved")

    def dump_config(self):
        return json.loads(str(self))

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
