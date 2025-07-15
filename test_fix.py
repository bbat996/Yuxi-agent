#!/usr/bin/env python3
"""
测试修复后的添加模型API
"""

import requests
import json

# 配置
BASE_URL = "http://localhost:8000"

def test_add_model_api():
    """测试添加模型API"""
    print("=== 测试添加模型API ===")
    
    # 注意：这里需要有效的admin token
    headers = {
        "Content-Type": "application/json"
        # "Authorization": "Bearer your_admin_token_here"
    }
    
    provider = "openai"
    model_name = "gpt-4-turbo-test"
    
    try:
        # 测试直接发送字符串
        response = requests.post(
            f"{BASE_URL}/api/chat/provider/{provider}/models/add", 
            headers=headers,
            json=model_name  # 直接发送字符串
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            print("✅ API调用成功")
        elif response.status_code == 422:
            print("❌ 请求格式错误")
        elif response.status_code == 401:
            print("❌ 需要认证")
        else:
            print(f"❌ 其他错误: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")

if __name__ == "__main__":
    test_add_model_api() 