from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.parent
CONFIG_PATH = PROJECT_DIR / "server/config"

SELECTED_CONFIG_PATH = CONFIG_PATH / "selected_config.yaml"  # 当前选中的配置文件

SITE_INFO_PATH = CONFIG_PATH / "site_info.yaml"  # 网站信息配置文件
MODELS_PATH = CONFIG_PATH / "model_provider.yaml"  # 模型配置文件
MODELS_PRIVATE_PATH = CONFIG_PATH / "model_provider.private.yml"  # 模型私有配置文件






