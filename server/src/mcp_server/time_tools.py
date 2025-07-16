"""
时间工具模块
提供时间日期处理功能
"""

from mcp.server.fastmcp import FastMCP
from datetime import datetime, timedelta
import pytz
from typing import Dict, Any

mcp = FastMCP("time")

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

@mcp.tool()
def get_date_info(date_str: str = None, format: str = "%Y-%m-%d") -> Dict[str, Any]:
    """获取日期信息
    
    Args:
        date_str: 日期字符串，默认为今天
        format: 日期格式，默认为"%Y-%m-%d"
        
    Returns:
        包含日期信息的字典
    """
    try:
        if date_str:
            date_obj = datetime.strptime(date_str, format)
        else:
            date_obj = datetime.now()
        
        return {
            "date": date_obj.strftime("%Y-%m-%d"),
            "year": date_obj.year,
            "month": date_obj.month,
            "day": date_obj.day,
            "weekday": date_obj.strftime("%A"),
            "weekday_num": date_obj.weekday(),
            "is_weekend": date_obj.weekday() >= 5
        }
    except Exception as e:
        return {"error": f"解析日期时发生错误: {str(e)}"}

@mcp.tool()
def calculate_date_difference(date1: str, date2: str, format: str = "%Y-%m-%d") -> Dict[str, Any]:
    """计算两个日期之间的差值
    
    Args:
        date1: 第一个日期字符串
        date2: 第二个日期字符串
        format: 日期格式，默认为"%Y-%m-%d"
        
    Returns:
        包含差值信息的字典
    """
    try:
        d1 = datetime.strptime(date1, format)
        d2 = datetime.strptime(date2, format)
        diff = abs(d2 - d1)
        
        return {
            "days": diff.days,
            "hours": diff.total_seconds() / 3600,
            "minutes": diff.total_seconds() / 60,
            "seconds": diff.total_seconds()
        }
    except Exception as e:
        return {"error": f"计算日期差值时发生错误: {str(e)}"}

@mcp.tool()
def add_days_to_date(date_str: str, days: int, format: str = "%Y-%m-%d") -> str:
    """在指定日期上增加天数
    
    Args:
        date_str: 日期字符串
        days: 要增加的天数（可以是负数）
        format: 日期格式，默认为"%Y-%m-%d"
        
    Returns:
        计算后的日期字符串
    """
    try:
        date_obj = datetime.strptime(date_str, format)
        new_date = date_obj + timedelta(days=days)
        return new_date.strftime(format)
    except Exception as e:
        return f"计算日期时发生错误: {str(e)}"

@mcp.tool()
def get_week_info(date_str: str = None, format: str = "%Y-%m-%d") -> Dict[str, Any]:
    """获取指定日期所在周的信息
    
    Args:
        date_str: 日期字符串，默认为今天
        format: 日期格式，默认为"%Y-%m-%d"
        
    Returns:
        周信息字典
    """
    try:
        if date_str:
            date_obj = datetime.strptime(date_str, format)
        else:
            date_obj = datetime.now()
        
        # 计算本周的开始和结束
        start_of_week = date_obj - timedelta(days=date_obj.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        return {
            "current_date": date_obj.strftime(format),
            "week_start": start_of_week.strftime(format),
            "week_end": end_of_week.strftime(format),
            "week_number": date_obj.isocalendar()[1],
            "year": date_obj.year
        }
    except Exception as e:
        return {"error": f"获取周信息时发生错误: {str(e)}"} 