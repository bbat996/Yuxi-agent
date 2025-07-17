from pathlib import Path

# 项目路径常量
PROJECT_DIR = Path(__file__).parent.parent.parent

# 网站信息配置文件
SITE_INFO_PATH = Path(__file__).parent / "site_info.yaml"

# 导入配置实例
from config.app_config import config
