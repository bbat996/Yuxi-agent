from mcp.server.fastmcp import FastMCP
import requests
from datetime import datetime
import pytz

mcp = FastMCP("system")

@mcp.tool()
def add(a: float, b: float) -> float:
    """返回两个数的和"""
    return a + b

@mcp.tool()
def sub(a: float, b: float) -> float:
    """返回两个数的差"""
    return a - b

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
def get_time(timezone: str = "Asia/Shanghai") -> str:
    """获取指定时区的当前时间
    
    Args:
        timezone: 时区名称，默认为"Asia/Shanghai"
        
    Returns:
        当前时间字符串
    """
    try:
        tz = pytz.timezone(timezone)
        current_time = datetime.now(tz)
        return current_time.strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception as e:
        return f"获取时间时发生错误: {str(e)}"

if __name__ == "__main__":
    mcp.run()