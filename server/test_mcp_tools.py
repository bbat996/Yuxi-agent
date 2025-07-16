#!/usr/bin/env python3
"""
MCP工具测试脚本
用于测试所有MCP工具的功能
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agents.mcp_server.system_server import mcp
from src.agents.mcp_server.tools_config import get_all_tools, get_tool_categories


async def test_math_tools():
    """测试数学运算工具"""
    print("=== 测试数学运算工具 ===")
    
    # 测试加法
    result = mcp._tools["add"](5, 3)
    print(f"5 + 3 = {result}")
    
    # 测试乘法
    result = mcp._tools["multiply"](4, 7)
    print(f"4 * 7 = {result}")
    
    # 测试幂运算
    result = mcp._tools["power"](2, 8)
    print(f"2^8 = {result}")
    
    # 测试平方根
    result = mcp._tools["sqrt"](16)
    print(f"√16 = {result}")


async def test_time_tools():
    """测试时间日期工具"""
    print("\n=== 测试时间日期工具 ===")
    
    # 测试获取时间
    result = mcp._tools["get_time"]()
    print(f"当前时间: {result}")
    
    # 测试获取日期信息
    result = mcp._tools["get_date_info"]()
    print(f"日期信息: {result}")
    
    # 测试日期差值计算
    result = mcp._tools["calculate_date_difference"]("2024-01-01", "2024-12-31")
    print(f"日期差值: {result}")


async def test_network_tools():
    """测试网络工具"""
    print("\n=== 测试网络工具 ===")
    
    # 测试URL编码
    result = mcp.url_encode("Hello World!")
    print(f"URL编码: {result}")
    
    # 测试URL解码
    result = mcp.url_decode("Hello%20World%21")
    print(f"URL解码: {result}")
    
    # 测试天气查询（可能需要网络）
    try:
        result = mcp.get_weather("北京")
        print(f"北京天气: {result}")
    except Exception as e:
        print(f"天气查询失败: {e}")


async def test_data_processing_tools():
    """测试数据处理工具"""
    print("\n=== 测试数据处理工具 ===")
    
    # 测试JSON处理
    test_data = {"name": "张三", "age": 25, "city": "北京"}
    json_str = mcp.json_stringify(test_data)
    print(f"JSON字符串: {json_str}")
    
    parsed_data = mcp.json_parse(json_str)
    print(f"解析后的数据: {parsed_data}")
    
    # 测试Base64编码
    text = "Hello, MCP Tools!"
    encoded = mcp.text_to_base64(text)
    print(f"Base64编码: {encoded}")
    
    decoded = mcp.base64_to_text(encoded)
    print(f"Base64解码: {decoded}")
    
    # 测试哈希计算
    hash_result = mcp.calculate_hash("test string", "md5")
    print(f"MD5哈希: {hash_result}")


async def test_text_processing_tools():
    """测试文本处理工具"""
    print("\n=== 测试文本处理工具 ===")
    
    test_text = "Hello World! This is a test string. Hello again!"
    
    # 测试文本搜索
    search_results = mcp.text_search(test_text, r"Hello", case_sensitive=False)
    print(f"搜索'Hello'的结果: {search_results}")
    
    # 测试文本替换
    replaced_text = mcp.text_replace(test_text, r"Hello", "Hi", case_sensitive=False)
    print(f"替换后的文本: {replaced_text}")
    
    # 测试文本分割
    split_results = mcp.text_split(test_text, " ")
    print(f"按空格分割: {split_results[:3]}...")  # 只显示前3个
    
    # 测试文本连接
    joined_text = mcp.text_join(["Hello", "World", "!"], " ")
    print(f"连接后的文本: {joined_text}")


async def test_validation_tools():
    """测试数据验证工具"""
    print("\n=== 测试数据验证工具 ===")
    
    # 测试邮箱验证
    email_result = mcp.validate_email("test@example.com")
    print(f"邮箱验证: {email_result}")
    
    # 测试手机号验证
    phone_result = mcp.validate_phone("13812345678")
    print(f"手机号验证: {phone_result}")
    
    # 测试URL验证
    url_result = mcp.validate_url("https://www.example.com")
    print(f"URL验证: {url_result}")


async def test_conversion_tools():
    """测试数据转换工具"""
    print("\n=== 测试数据转换工具 ===")
    
    # 测试温度转换
    temp_result = mcp.convert_temperature(25, "celsius", "fahrenheit")
    print(f"温度转换: {temp_result}")
    
    # 测试长度转换
    length_result = mcp.convert_length(1000, "m", "km")
    print(f"长度转换: {length_result}")


async def test_system_tools():
    """测试系统信息工具"""
    print("\n=== 测试系统信息工具 ===")
    
    # 测试系统信息
    try:
        sys_info = mcp.get_system_info()
        print(f"系统信息: {sys_info}")
    except Exception as e:
        print(f"获取系统信息失败: {e}")
    
    # 测试内存信息
    try:
        mem_info = mcp.get_memory_info()
        print(f"内存信息: {mem_info}")
    except Exception as e:
        print(f"获取内存信息失败: {e}")


async def test_file_tools():
    """测试文件操作工具"""
    print("\n=== 测试文件操作工具 ===")
    
    test_file = "test_mcp_tools.txt"
    test_content = "这是一个测试文件\n用于测试MCP工具\nHello MCP!"
    
    try:
        # 测试写入文件
        write_result = mcp.write_file(test_file, test_content)
        print(f"写入文件: {write_result}")
        
        # 测试读取文件
        read_result = mcp.read_file(test_file)
        print(f"读取文件: {read_result}")
        
        # 测试获取文件信息
        file_info = mcp.get_file_info(test_file)
        print(f"文件信息: {file_info}")
        
        # 清理测试文件
        os.remove(test_file)
        print("测试文件已清理")
        
    except Exception as e:
        print(f"文件操作测试失败: {e}")


async def test_http_tools():
    """测试HTTP请求工具"""
    print("\n=== 测试HTTP请求工具 ===")
    
    try:
        # 测试GET请求
        get_result = mcp.http_get("https://httpbin.org/get")
        print(f"GET请求状态码: {get_result.get('status_code')}")
        
        # 测试POST请求
        post_result = mcp.http_post("https://httpbin.org/post", json_data={"test": "data"})
        print(f"POST请求状态码: {post_result.get('status_code')}")
        
    except Exception as e:
        print(f"HTTP请求测试失败: {e}")


async def show_tool_categories():
    """显示工具分类信息"""
    print("\n=== MCP工具分类信息 ===")
    categories = get_tool_categories()
    all_tools = get_all_tools()
    
    print(f"总工具数量: {len(all_tools)}")
    print(f"分类数量: {len(categories)}")
    print("\n工具分类:")
    
    for category_name, category_info in categories.items():
        print(f"  {category_name}: {category_info['description']} ({len(category_info['tools'])} 个工具)")
        for tool in category_info['tools']:
            print(f"    - {tool}")


async def main():
    """主测试函数"""
    print("开始测试MCP工具...")
    print("=" * 50)
    
    # 显示工具分类信息
    await show_tool_categories()
    
    # 测试各类工具
    await test_math_tools()
    await test_time_tools()
    await test_network_tools()
    await test_data_processing_tools()
    await test_text_processing_tools()
    await test_validation_tools()
    await test_conversion_tools()
    await test_system_tools()
    await test_file_tools()
    await test_http_tools()
    
    print("\n" + "=" * 50)
    print("MCP工具测试完成!")


if __name__ == "__main__":
    asyncio.run(main()) 