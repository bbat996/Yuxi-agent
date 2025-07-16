# MCP服务器模块

本目录包含了模块化的MCP（Model Context Protocol）服务器实现，将不同业务功能的工具拆分为独立的模块。

## 目录结构

```
mcp_server/
├── __init__.py
├── README.md
├── config_manager.py      # 配置管理器
├── tools_config.py        # 工具配置
├── math_tools.py          # 数学工具模块
├── time_tools.py          # 时间工具模块
├── network_tools.py       # 网络工具模块
├── file_tools.py          # 文件工具模块
├── text_tools.py          # 文本工具模块
└── system_tools.py        # 系统工具模块
```

## 模块说明

### 1. 数学工具模块 (math_tools.py)
提供基础数学运算和单位转换功能：
- 基础运算：加法、减法、乘法、除法、幂运算、平方根
- 单位转换：温度转换、长度转换

### 2. 时间工具模块 (time_tools.py)
提供时间日期处理功能：
- 时间获取：获取指定时区的当前时间
- 日期信息：获取日期详细信息、计算日期差值
- 日期操作：日期加减、获取周信息

### 3. 网络工具模块 (network_tools.py)
提供网络相关功能：
- 天气查询：查询指定城市的天气信息
- URL操作：检查URL状态、URL编码/解码、验证URL
- HTTP请求：GET/POST请求
- IP信息：获取IP地址详细信息

### 4. 文件工具模块 (file_tools.py)
提供文件和目录操作功能：
- 文件操作：读取、写入、删除文件
- 目录操作：列出目录、创建目录、获取文件信息
- 数据处理：JSON解析/序列化、Base64编码/解码、哈希计算

### 5. 文本工具模块 (text_tools.py)
提供文本处理功能：
- 文本搜索：正则表达式搜索、文本替换
- 文本分割：按分隔符分割、连接文本列表
- 数据提取：提取数字、提取URL
- 文本分析：统计单词、大小写转换
- 数据验证：验证邮箱、验证手机号

### 6. 系统工具模块 (system_tools.py)
提供系统信息和监控功能：
- 系统信息：获取系统基本信息、CPU信息、内存信息
- 磁盘信息：获取磁盘使用情况
- 网络信息：获取网络使用情况
- 进程管理：获取进程信息、列出进程
- 环境信息：获取环境变量、工作目录

## 配置管理

### 配置文件位置
配置文件位于 `server/config/mcp_server.yaml`

### 配置结构
```yaml
# 内置服务器配置
builtin_servers:
  math:
    enabled: true
    name: "Math Tools Server"
    description: "数学计算工具服务器"
    server_type: "builtin"
    module_path: "src.mcp_server.math_tools"
    class_name: "mcp"
    tools:
      basic_math:
        enabled: true
        description: "基础数学运算"
        tools:
          - "add"
          - "sub"
          # ...

# 外部服务器配置
external_servers:
  # 外部服务器配置...

# 全局配置
global_config:
  default_servers: ["math", "time", "network", "file", "text", "system"]
  connection_timeout: 30
  max_connections: 10
  log_level: "INFO"

# 工具分类配置
tool_categories:
  基础数学运算:
    description: "基本的数学计算工具"
    servers: ["math"]
    tools:
      - "add"
      - "sub"
      # ...
```

## API接口

### MCP工具接口
- `GET /api/mcp/tools/categories` - 获取工具分类列表
- `GET /api/mcp/tools/list` - 获取工具列表
- `GET /api/mcp/tools/search` - 搜索工具
- `GET /api/mcp/tools/{tool_name}` - 获取工具详情
- `GET /api/mcp/tools/overview` - 获取工具概览
- `GET /api/mcp/tools/category/{category_name}` - 获取分类工具
- `GET /api/mcp/tools/random` - 获取随机工具

### MCP配置接口
- `GET /api/mcp/config/summary` - 获取配置摘要
- `GET /api/mcp/config/servers` - 获取服务器列表
- `GET /api/mcp/config/servers/{server_name}` - 获取服务器详情
- `POST /api/mcp/config/reload` - 重新加载配置
- `GET /api/mcp/config/validate` - 验证配置

### 技能管理接口
- `GET /api/skills/categories` - 获取技能分类
- `GET /api/skills/list` - 获取技能列表
- `GET /api/skills/search` - 搜索技能
- `GET /api/skills/{skill_id}` - 获取技能详情
- `POST /api/skills/{skill_id}/test` - 测试技能
- `GET /api/skills/stats` - 获取技能统计

## 使用方法

### 1. 启动服务器
```bash
cd server
python main.py
```

### 2. 配置MCP服务器
编辑 `config/mcp_server.yaml` 文件，启用或禁用相应的服务器模块。

### 3. 调用工具
通过API接口调用相应的工具功能，或通过MCP协议直接调用。

## 扩展新模块

### 1. 创建新模块文件
```python
# example_tools.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("example")

@mcp.tool()
def example_function(param: str) -> str:
    """示例工具函数"""
    return f"Hello {param}"
```

### 2. 更新配置文件
在 `config/mcp_server.yaml` 中添加新模块配置：
```yaml
builtin_servers:
  example:
    enabled: true
    name: "Example Tools Server"
    description: "示例工具服务器"
    server_type: "builtin"
    module_path: "src.mcp_server.example_tools"
    class_name: "mcp"
    tools:
      example_category:
        enabled: true
        description: "示例工具"
        tools:
          - "example_function"
```

### 3. 更新工具配置
在 `tools_config.py` 中添加工具详细信息。

## 注意事项

1. 所有工具函数都应该包含适当的错误处理
2. 工具函数应该返回可序列化的数据类型
3. 配置文件修改后需要重新加载配置
4. 新增模块需要确保依赖包已安装
5. 工具函数应该包含清晰的文档字符串

## 依赖包

主要依赖包：
- `mcp>=0.1.0` - MCP协议支持
- `fastapi` - Web框架
- `psutil>=5.9.0` - 系统信息
- `pytz>=2024.1` - 时区处理
- `requests>=2.31.0` - HTTP请求
- `pyyaml>=6.0.2` - YAML配置 