from pathlib import Path
import yaml

# 项目路径常量
PROJECT_DIR = Path(__file__).parent.parent.parent

# 网站信息配置文件
SITE_INFO_PATH = Path(__file__).parent / "site_info.yaml"

# 导入配置实例
from config.app_config import config

def save_yaml(data, file_path):
    """保存数据为YAML文件"""
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, indent=2)

def load_yaml(file_path):
    """从YAML文件加载数据"""
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
