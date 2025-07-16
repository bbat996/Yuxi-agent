#!/usr/bin/env python3
"""
简化的MCP工具测试脚本
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agents.mcp_server.tools_config import get_all_tools, get_tool_categories


def test_tool_categories():
    """测试工具分类功能"""
    print("=== 测试工具分类功能 ===")
    
    categories = get_tool_categories()
    all_tools = get_all_tools()
    
    print(f"总工具数量: {len(all_tools)}")
    print(f"分类数量: {len(categories)}")
    print("\n工具分类:")
    
    for category_name, category_info in categories.items():
        print(f"  {category_name}: {category_info['description']} ({len(category_info['tools'])} 个工具)")
        for tool in category_info['tools']:
            print(f"    - {tool}")


def test_individual_tools():
    """测试个别工具的功能"""
    print("\n=== 测试个别工具功能 ===")
    
    # 导入一些基础工具进行测试
    import json
    import hashlib
    import base64
    import re
    from datetime import datetime
    
    # 测试JSON处理
    test_data = {"name": "张三", "age": 25, "city": "北京"}
    json_str = json.dumps(test_data, ensure_ascii=False)
    print(f"JSON字符串: {json_str}")
    
    parsed_data = json.loads(json_str)
    print(f"解析后的数据: {parsed_data}")
    
    # 测试Base64编码
    text = "Hello, MCP Tools!"
    encoded = base64.b64encode(text.encode('utf-8')).decode('ascii')
    print(f"Base64编码: {encoded}")
    
    decoded = base64.b64decode(encoded).decode('utf-8')
    print(f"Base64解码: {decoded}")
    
    # 测试哈希计算
    hash_obj = hashlib.md5()
    hash_obj.update("test string".encode('utf-8'))
    hash_result = hash_obj.hexdigest()
    print(f"MD5哈希: {hash_result}")
    
    # 测试正则表达式
    test_text = "Hello World! This is a test string. Hello again!"
    matches = list(re.finditer(r"Hello", test_text, re.IGNORECASE))
    print(f"搜索'Hello'的结果数量: {len(matches)}")
    
    # 测试时间处理
    current_time = datetime.now()
    print(f"当前时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试数学运算
    result = 5 + 3
    print(f"5 + 3 = {result}")
    
    result = 4 * 7
    print(f"4 * 7 = {result}")
    
    result = 2 ** 8
    print(f"2^8 = {result}")
    
    result = 16 ** 0.5
    print(f"√16 = {result}")


def test_api_endpoints():
    """测试API端点（模拟）"""
    print("\n=== 测试API端点（模拟） ===")
    
    # 模拟API响应
    api_endpoints = [
        "/api/mcp/tools/categories",
        "/api/mcp/tools/list",
        "/api/mcp/tools/search?keyword=计算",
        "/api/mcp/tools/overview",
        "/api/mcp/tools/add"
    ]
    
    print("可用的API端点:")
    for endpoint in api_endpoints:
        print(f"  GET {endpoint}")


def main():
    """主测试函数"""
    print("开始测试MCP工具...")
    print("=" * 50)
    
    test_tool_categories()
    test_individual_tools()
    test_api_endpoints()
    
    print("\n" + "=" * 50)
    print("MCP工具测试完成!")
    print("\n注意: 这是简化测试，实际工具需要通过MCP协议调用")


if __name__ == "__main__":
    main() 