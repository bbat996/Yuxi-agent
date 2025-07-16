"""
数学工具模块
提供基础数学运算功能
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("math")

@mcp.tool()
def add(a: float, b: float) -> float:
    """返回两个数的和"""
    return a + b

@mcp.tool()
def sub(a: float, b: float) -> float:
    """返回两个数的差"""
    return a - b

@mcp.tool()
def multiply(a: float, b: float) -> float:
    """返回两个数的乘积"""
    return a * b

@mcp.tool()
def divide(a: float, b: float) -> float:
    """返回两个数的商"""
    if b == 0:
        raise ValueError("除数不能为零")
    return a / b

@mcp.tool()
def power(base: float, exponent: float) -> float:
    """返回base的exponent次方"""
    return base ** exponent

@mcp.tool()
def sqrt(number: float) -> float:
    """返回数字的平方根"""
    if number < 0:
        raise ValueError("不能计算负数的平方根")
    return number ** 0.5

@mcp.tool()
def convert_temperature(value: float, from_unit: str, to_unit: str) -> dict:
    """温度单位转换
    
    Args:
        value: 要转换的值
        from_unit: 原始单位 (celsius, fahrenheit, kelvin)
        to_unit: 目标单位 (celsius, fahrenheit, kelvin)
        
    Returns:
        转换结果
    """
    units = from_unit.lower(), to_unit.lower()
    
    # 先转换为摄氏度
    if units[0] == "celsius":
        celsius = value
    elif units[0] == "fahrenheit":
        celsius = (value - 32) * 5/9
    elif units[0] == "kelvin":
        celsius = value - 273.15
    else:
        raise ValueError(f"不支持的原始单位: {from_unit}")
    
    # 从摄氏度转换为目标单位
    if units[1] == "celsius":
        result = celsius
    elif units[1] == "fahrenheit":
        result = celsius * 9/5 + 32
    elif units[1] == "kelvin":
        result = celsius + 273.15
    else:
        raise ValueError(f"不支持的目标单位: {to_unit}")
    
    return {
        "value": round(result, 4),
        "from_unit": from_unit,
        "to_unit": to_unit,
        "original_value": value
    }

@mcp.tool()
def convert_length(value: float, from_unit: str, to_unit: str) -> dict:
    """长度单位转换
    
    Args:
        value: 要转换的值
        from_unit: 原始单位 (m, km, cm, mm, mile, yard, foot, inch)
        to_unit: 目标单位 (m, km, cm, mm, mile, yard, foot, inch)
        
    Returns:
        转换结果
    """
    # 转换为米
    to_meter = {
        "m": 1,
        "km": 1000,
        "cm": 0.01,
        "mm": 0.001,
        "mile": 1609.344,
        "yard": 0.9144,
        "foot": 0.3048,
        "inch": 0.0254
    }
    
    from_unit = from_unit.lower()
    to_unit = to_unit.lower()
    
    if from_unit not in to_meter:
        raise ValueError(f"不支持的原始单位: {from_unit}")
    if to_unit not in to_meter:
        raise ValueError(f"不支持的目标单位: {to_unit}")
    
    # 先转换为米
    meters = value * to_meter[from_unit]
    # 再转换为目标单位
    result = meters / to_meter[to_unit]
    
    return {
        "value": round(result, 6),
        "from_unit": from_unit,
        "to_unit": to_unit,
        "original_value": value
    } 