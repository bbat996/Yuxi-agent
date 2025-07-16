"""
MCP工具配置文件
用于管理和分类所有可用的MCP工具
"""

from typing import Dict, List, Any
from .config_manager import get_mcp_config_manager

def get_tool_categories() -> Dict[str, Any]:
    """获取工具分类配置"""
    config_manager = get_mcp_config_manager()
    return config_manager.get_tool_categories()

def get_tool_details() -> Dict[str, Any]:
    """获取工具详细信息"""
    # 工具详细信息映射
    TOOL_DETAILS = {
        # 基础数学运算
        "add": {
            "name": "加法运算",
            "description": "返回两个数的和",
            "parameters": ["a: float", "b: float"],
            "return_type": "float",
            "category": "基础数学运算"
        },
        "sub": {
            "name": "减法运算", 
            "description": "返回两个数的差",
            "parameters": ["a: float", "b: float"],
            "return_type": "float",
            "category": "基础数学运算"
        },
        "multiply": {
            "name": "乘法运算",
            "description": "返回两个数的乘积",
            "parameters": ["a: float", "b: float"],
            "return_type": "float",
            "category": "基础数学运算"
        },
        "divide": {
            "name": "除法运算",
            "description": "返回两个数的商",
            "parameters": ["a: float", "b: float"],
            "return_type": "float",
            "category": "基础数学运算"
        },
        "power": {
            "name": "幂运算",
            "description": "返回base的exponent次方",
            "parameters": ["base: float", "exponent: float"],
            "return_type": "float",
            "category": "基础数学运算"
        },
        "sqrt": {
            "name": "平方根",
            "description": "返回数字的平方根",
            "parameters": ["number: float"],
            "return_type": "float",
            "category": "基础数学运算"
        },
        "convert_temperature": {
            "name": "温度转换",
            "description": "温度单位转换",
            "parameters": ["value: float", "from_unit: str", "to_unit: str"],
            "return_type": "dict",
            "category": "基础数学运算"
        },
        "convert_length": {
            "name": "长度转换",
            "description": "长度单位转换",
            "parameters": ["value: float", "from_unit: str", "to_unit: str"],
            "return_type": "dict",
            "category": "基础数学运算"
        },
        
        # 时间日期工具
        "get_time": {
            "name": "获取时间",
            "description": "获取指定时区的当前时间",
            "parameters": ["timezone: str = 'Asia/Shanghai'"],
            "return_type": "str",
            "category": "时间日期工具"
        },
        "get_date_info": {
            "name": "获取日期信息",
            "description": "获取日期的详细信息",
            "parameters": ["date_str: str = None", "format: str = '%Y-%m-%d'"],
            "return_type": "Dict[str, Any]",
            "category": "时间日期工具"
        },
        "calculate_date_difference": {
            "name": "计算日期差值",
            "description": "计算两个日期之间的差值",
            "parameters": ["date1: str", "date2: str", "format: str = '%Y-%m-%d'"],
            "return_type": "Dict[str, Any]",
            "category": "时间日期工具"
        },
        "add_days_to_date": {
            "name": "日期加减",
            "description": "在指定日期上增加天数",
            "parameters": ["date_str: str", "days: int", "format: str = '%Y-%m-%d'"],
            "return_type": "str",
            "category": "时间日期工具"
        },
        "get_week_info": {
            "name": "获取周信息",
            "description": "获取指定日期所在周的信息",
            "parameters": ["date_str: str = None", "format: str = '%Y-%m-%d'"],
            "return_type": "Dict[str, Any]",
            "category": "时间日期工具"
        },
        
        # 网络工具
        "get_weather": {
            "name": "查询天气",
            "description": "查询指定城市的天气信息",
            "parameters": ["city: str"],
            "return_type": "str",
            "category": "网络工具"
        },
        "check_url_status": {
            "name": "检查URL状态",
            "description": "检查URL的可访问性和状态",
            "parameters": ["url: str"],
            "return_type": "Dict[str, Any]",
            "category": "网络工具"
        },
        "get_ip_info": {
            "name": "获取IP信息",
            "description": "获取IP地址的详细信息",
            "parameters": ["ip: str = None"],
            "return_type": "Dict[str, Any]",
            "category": "网络工具"
        },
        "url_encode": {
            "name": "URL编码",
            "description": "对文本进行URL编码",
            "parameters": ["text: str"],
            "return_type": "str",
            "category": "网络工具"
        },
        "url_decode": {
            "name": "URL解码",
            "description": "对URL编码的文本进行解码",
            "parameters": ["text: str"],
            "return_type": "str",
            "category": "网络工具"
        },
        "http_get": {
            "name": "HTTP GET请求",
            "description": "发送HTTP GET请求",
            "parameters": ["url: str", "headers: Dict[str, str] = None", "timeout: int = 30"],
            "return_type": "Dict[str, Any]",
            "category": "网络工具"
        },
        "http_post": {
            "name": "HTTP POST请求",
            "description": "发送HTTP POST请求",
            "parameters": ["url: str", "data: Dict[str, Any] = None", "json_data: Dict[str, Any] = None", "headers: Dict[str, str] = None", "timeout: int = 30"],
            "return_type": "Dict[str, Any]",
            "category": "网络工具"
        },
        "validate_url": {
            "name": "验证URL",
            "description": "验证URL格式",
            "parameters": ["url: str"],
            "return_type": "Dict[str, Any]",
            "category": "网络工具"
        },
        
        # 文件操作工具
        "read_file": {
            "name": "读取文件",
            "description": "读取文件内容",
            "parameters": ["file_path: str", "encoding: str = 'utf-8'"],
            "return_type": "str",
            "category": "文件操作工具"
        },
        "write_file": {
            "name": "写入文件",
            "description": "写入文件内容",
            "parameters": ["file_path: str", "content: str", "encoding: str = 'utf-8'"],
            "return_type": "str",
            "category": "文件操作工具"
        },
        "list_directory": {
            "name": "列出目录",
            "description": "列出目录内容",
            "parameters": ["path: str = '.'"],
            "return_type": "List[Dict[str, Any]]",
            "category": "文件操作工具"
        },
        "get_file_info": {
            "name": "获取文件信息",
            "description": "获取文件详细信息",
            "parameters": ["file_path: str"],
            "return_type": "Dict[str, Any]",
            "category": "文件操作工具"
        },
        "create_directory": {
            "name": "创建目录",
            "description": "创建新目录",
            "parameters": ["dir_path: str"],
            "return_type": "str",
            "category": "文件操作工具"
        },
        "delete_file": {
            "name": "删除文件",
            "description": "删除指定文件",
            "parameters": ["file_path: str"],
            "return_type": "str",
            "category": "文件操作工具"
        },
        
        # 数据处理工具
        "json_parse": {
            "name": "JSON解析",
            "description": "解析JSON字符串",
            "parameters": ["json_str: str"],
            "return_type": "Dict[str, Any]",
            "category": "数据处理工具"
        },
        "json_stringify": {
            "name": "JSON序列化",
            "description": "将对象转换为JSON字符串",
            "parameters": ["obj: Dict[str, Any]", "indent: int = 2"],
            "return_type": "str",
            "category": "数据处理工具"
        },
        "text_to_base64": {
            "name": "Base64编码",
            "description": "将文本转换为Base64编码",
            "parameters": ["text: str", "encoding: str = 'utf-8'"],
            "return_type": "str",
            "category": "数据处理工具"
        },
        "base64_to_text": {
            "name": "Base64解码",
            "description": "将Base64编码转换为文本",
            "parameters": ["base64_str: str", "encoding: str = 'utf-8'"],
            "return_type": "str",
            "category": "数据处理工具"
        },
        "calculate_hash": {
            "name": "计算哈希",
            "description": "计算文本的哈希值",
            "parameters": ["text: str", "algorithm: str = 'md5'"],
            "return_type": "str",
            "category": "数据处理工具"
        },
        
        # 文本处理工具
        "text_search": {
            "name": "文本搜索",
            "description": "在文本中搜索匹配的模式",
            "parameters": ["text: str", "pattern: str", "case_sensitive: bool = False"],
            "return_type": "List[Dict[str, Any]]",
            "category": "文本处理工具"
        },
        "text_replace": {
            "name": "文本替换",
            "description": "替换文本中的模式",
            "parameters": ["text: str", "pattern: str", "replacement: str", "case_sensitive: bool = False"],
            "return_type": "str",
            "category": "文本处理工具"
        },
        "text_split": {
            "name": "文本分割",
            "description": "分割文本",
            "parameters": ["text: str", "delimiter: str = '\\n'", "max_splits: int = -1"],
            "return_type": "List[str]",
            "category": "文本处理工具"
        },
        "text_join": {
            "name": "文本连接",
            "description": "连接文本列表",
            "parameters": ["texts: List[str]", "delimiter: str = '\\n'"],
            "return_type": "str",
            "category": "文本处理工具"
        },
        "extract_numbers": {
            "name": "提取数字",
            "description": "从文本中提取数字",
            "parameters": ["text: str"],
            "return_type": "List[str]",
            "category": "文本处理工具"
        },
        "extract_urls": {
            "name": "提取URL",
            "description": "从文本中提取URL",
            "parameters": ["text: str"],
            "return_type": "List[str]",
            "category": "文本处理工具"
        },
        "count_words": {
            "name": "统计单词",
            "description": "统计文本中的单词数量",
            "parameters": ["text: str"],
            "return_type": "Dict[str, Any]",
            "category": "文本处理工具"
        },
        "text_case_convert": {
            "name": "大小写转换",
            "description": "转换文本大小写",
            "parameters": ["text: str", "case_type: str = 'lower'"],
            "return_type": "str",
            "category": "文本处理工具"
        },
        
        # 系统信息工具
        "get_system_info": {
            "name": "获取系统信息",
            "description": "获取系统基本信息",
            "parameters": [],
            "return_type": "Dict[str, Any]",
            "category": "系统信息工具"
        },
        "get_memory_info": {
            "name": "获取内存信息",
            "description": "获取内存使用情况",
            "parameters": [],
            "return_type": "Dict[str, Any]",
            "category": "系统信息工具"
        },
        "get_disk_info": {
            "name": "获取磁盘信息",
            "description": "获取磁盘使用情况",
            "parameters": ["path: str = '/'"],
            "return_type": "Dict[str, Any]",
            "category": "系统信息工具"
        },
        "get_cpu_info": {
            "name": "获取CPU信息",
            "description": "获取CPU使用情况",
            "parameters": [],
            "return_type": "Dict[str, Any]",
            "category": "系统信息工具"
        },
        "get_network_info": {
            "name": "获取网络信息",
            "description": "获取网络使用情况",
            "parameters": [],
            "return_type": "Dict[str, Any]",
            "category": "系统信息工具"
        },
        "get_process_info": {
            "name": "获取进程信息",
            "description": "获取指定进程信息",
            "parameters": ["pid: int = None"],
            "return_type": "Dict[str, Any]",
            "category": "系统信息工具"
        },
        "list_processes": {
            "name": "列出进程",
            "description": "列出系统进程",
            "parameters": ["limit: int = 10"],
            "return_type": "list",
            "category": "系统信息工具"
        },
        "get_environment_variables": {
            "name": "获取环境变量",
            "description": "获取系统环境变量",
            "parameters": [],
            "return_type": "Dict[str, str]",
            "category": "系统信息工具"
        },
        "get_current_working_directory": {
            "name": "获取工作目录",
            "description": "获取当前工作目录",
            "parameters": [],
            "return_type": "str",
            "category": "系统信息工具"
        },
        
        # 数据验证工具
        "validate_email": {
            "name": "验证邮箱",
            "description": "验证邮箱格式",
            "parameters": ["email: str"],
            "return_type": "Dict[str, Any]",
            "category": "数据验证工具"
        },
        "validate_phone": {
            "name": "验证手机号",
            "description": "验证手机号格式",
            "parameters": ["phone: str"],
            "return_type": "Dict[str, Any]",
            "category": "数据验证工具"
        }
    }
    
    return TOOL_DETAILS

def get_tools_by_category(category: str) -> List[str]:
    """根据分类获取工具列表"""
    config_manager = get_mcp_config_manager()
    return config_manager.get_tools_by_category(category)

def get_all_tools() -> List[str]:
    """获取所有工具列表"""
    config_manager = get_mcp_config_manager()
    return config_manager.get_all_tools()

def get_tool_info(tool_name: str) -> Dict[str, Any]:
    """获取工具详细信息"""
    tool_details = get_tool_details()
    return tool_details.get(tool_name, {})

def search_tools(keyword: str) -> List[str]:
    """搜索工具"""
    config_manager = get_mcp_config_manager()
    return config_manager.search_tools(keyword) 