"""
网络工具模块
提供网络相关功能
"""

from mcp.server.fastmcp import FastMCP
import requests
import urllib.parse
import aiohttp
import asyncio
from typing import Dict, Any, Optional

mcp = FastMCP("network")

@mcp.tool()
def get_weather(city: str) -> str:
    """查询指定城市的天气信息
    
    Args:
        city: 城市名称，如"北京"、"上海"等
        
    Returns:
        天气信息字符串
    """
    try:
        # 使用免费的天气API
        url = f"http://wttr.in/{city}?format=3"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.text.strip()
        else:
            return f"无法获取{city}的天气信息"
    except Exception as e:
        return f"查询天气时发生错误: {str(e)}"

@mcp.tool()
def check_url_status(url: str) -> Dict[str, Any]:
    """检查URL的状态
    
    Args:
        url: 要检查的URL
        
    Returns:
        包含状态信息的字典
    """
    try:
        response = requests.get(url, timeout=10, allow_redirects=True)
        return {
            "url": url,
            "status_code": response.status_code,
            "status_text": response.reason,
            "content_length": len(response.content),
            "content_type": response.headers.get("content-type", ""),
            "is_accessible": response.status_code < 400
        }
    except Exception as e:
        return {
            "url": url,
            "error": str(e),
            "is_accessible": False
        }

@mcp.tool()
def get_ip_info(ip: str = None) -> Dict[str, Any]:
    """获取IP地址信息
    
    Args:
        ip: IP地址，默认为当前IP
        
    Returns:
        IP信息字典
    """
    try:
        if not ip:
            # 获取本机IP
            response = requests.get("https://api.ipify.org?format=json", timeout=10)
            ip = response.json()["ip"]
        
        # 获取IP详细信息
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "ip": ip,
                "country": data.get("country"),
                "region": data.get("regionName"),
                "city": data.get("city"),
                "isp": data.get("isp"),
                "timezone": data.get("timezone"),
                "lat": data.get("lat"),
                "lon": data.get("lon")
            }
        else:
            return {"ip": ip, "error": "无法获取IP信息"}
    except Exception as e:
        return {"ip": ip, "error": str(e)}

@mcp.tool()
def url_encode(text: str) -> str:
    """对文本进行URL编码
    
    Args:
        text: 要编码的文本
        
    Returns:
        URL编码后的文本
    """
    try:
        return urllib.parse.quote(text)
    except Exception as e:
        return f"URL编码失败: {str(e)}"

@mcp.tool()
def url_decode(text: str) -> str:
    """对URL编码的文本进行解码
    
    Args:
        text: 要解码的文本
        
    Returns:
        解码后的文本
    """
    try:
        return urllib.parse.unquote(text)
    except Exception as e:
        return f"URL解码失败: {str(e)}"

@mcp.tool()
def http_get(url: str, headers: Dict[str, str] = None, timeout: int = 30) -> Dict[str, Any]:
    """发送HTTP GET请求
    
    Args:
        url: 请求URL
        headers: 请求头
        timeout: 超时时间（秒）
        
    Returns:
        响应信息
    """
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content": response.text,
            "content_length": len(response.content),
            "url": response.url
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def http_post(url: str, data: Dict[str, Any] = None, json_data: Dict[str, Any] = None, 
              headers: Dict[str, str] = None, timeout: int = 30) -> Dict[str, Any]:
    """发送HTTP POST请求
    
    Args:
        url: 请求URL
        data: 表单数据
        json_data: JSON数据
        headers: 请求头
        timeout: 超时时间（秒）
        
    Returns:
        响应信息
    """
    try:
        response = requests.post(url, data=data, json=json_data, headers=headers, timeout=timeout)
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content": response.text,
            "content_length": len(response.content),
            "url": response.url
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def validate_url(url: str) -> Dict[str, Any]:
    """验证URL格式
    
    Args:
        url: 要验证的URL
        
    Returns:
        验证结果
    """
    try:
        result = urllib.parse.urlparse(url)
        is_valid = all([result.scheme, result.netloc])
        
        return {
            "url": url,
            "is_valid": is_valid,
            "scheme": result.scheme,
            "netloc": result.netloc,
            "path": result.path,
            "query": result.query,
            "fragment": result.fragment
        }
    except Exception as e:
        return {
            "url": url,
            "is_valid": False,
            "error": str(e)
        }

if __name__ == "__main__":
    mcp.run()