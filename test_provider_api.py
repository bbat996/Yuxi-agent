#!/usr/bin/env python3
"""
测试供应商配置API的脚本
"""

import requests
import json

# 配置
BASE_URL = "http://localhost:8000"
ADMIN_TOKEN = "your_admin_token_here"  # 需要替换为实际的admin token

headers = {
    "Authorization": f"Bearer {ADMIN_TOKEN}",
    "Content-Type": "application/json"
}

def test_get_provider_config():
    """测试获取供应商配置"""
    print("=== 测试获取供应商配置 ===")
    
    providers = ["openai", "deepseek", "zhipu"]
    
    for provider in providers:
        try:
            response = requests.get(f"{BASE_URL}/api/chat/provider/{provider}/config", headers=headers)
            print(f"获取 {provider} 配置: {response.status_code}")
            if response.status_code == 200:
                print(f"配置内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            else:
                print(f"错误: {response.text}")
        except Exception as e:
            print(f"请求失败: {e}")
        print()

def test_update_provider_config():
    """测试更新供应商配置"""
    print("=== 测试更新供应商配置 ===")
    
    provider = "openai"
    config_data = {
        "base_url": "https://api.openai.com/v1",
        "api_key": "test_api_key_123"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat/provider/{provider}/config", 
            headers=headers,
            json=config_data
        )
        print(f"更新 {provider} 配置: {response.status_code}")
        if response.status_code == 200:
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    print()

def test_add_provider_model():
    """测试添加模型"""
    print("=== 测试添加模型 ===")
    
    provider = "openai"
    model_name = "gpt-4-turbo-test"
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat/provider/{provider}/models/add", 
            headers=headers,
            json=model_name
        )
        print(f"添加模型 {model_name} 到 {provider}: {response.status_code}")
        if response.status_code == 200:
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    print()

def test_remove_provider_model():
    """测试删除模型"""
    print("=== 测试删除模型 ===")
    
    provider = "openai"
    model_name = "gpt-4-turbo-test"
    
    try:
        response = requests.delete(
            f"{BASE_URL}/api/chat/provider/{provider}/models/{model_name}", 
            headers=headers
        )
        print(f"删除模型 {model_name} 从 {provider}: {response.status_code}")
        if response.status_code == 200:
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    print()

def test_provider_connection():
    """测试供应商连接"""
    print("=== 测试供应商连接 ===")
    
    provider = "openai"
    config_data = {
        "base_url": "https://api.openai.com/v1",
        "api_key": "test_api_key_123"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat/provider/{provider}/test", 
            headers=headers,
            json=config_data
        )
        print(f"测试 {provider} 连接: {response.status_code}")
        if response.status_code == 200:
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    print()

if __name__ == "__main__":
    print("开始测试供应商配置API...")
    print("注意: 请确保后端服务正在运行，并替换ADMIN_TOKEN为实际的admin token")
    print()
    
    # 测试各个API
    test_get_provider_config()
    test_update_provider_config()
    test_add_provider_model()
    test_remove_provider_model()
    test_provider_connection()
    
    print("测试完成!") 