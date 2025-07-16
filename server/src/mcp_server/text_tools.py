"""
文本工具模块
提供文本处理功能
"""

from mcp.server.fastmcp import FastMCP
import re
from typing import List, Dict, Any

mcp = FastMCP("text")

@mcp.tool()
def text_search(text: str, pattern: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
    """在文本中搜索匹配的模式
    
    Args:
        text: 要搜索的文本
        pattern: 搜索模式（正则表达式）
        case_sensitive: 是否区分大小写
        
    Returns:
        匹配结果列表
    """
    try:
        flags = 0 if case_sensitive else re.IGNORECASE
        matches = list(re.finditer(pattern, text, flags))
        
        results = []
        for match in matches:
            results.append({
                "match": match.group(),
                "start": match.start(),
                "end": match.end(),
                "span": match.span()
            })
        
        return results
    except Exception as e:
        return [{"error": f"搜索失败: {str(e)}"}]

@mcp.tool()
def text_replace(text: str, pattern: str, replacement: str, case_sensitive: bool = False) -> str:
    """替换文本中的模式
    
    Args:
        text: 要处理的文本
        pattern: 要替换的模式（正则表达式）
        replacement: 替换内容
        case_sensitive: 是否区分大小写
        
    Returns:
        替换后的文本
    """
    try:
        flags = 0 if case_sensitive else re.IGNORECASE
        return re.sub(pattern, replacement, text, flags=flags)
    except Exception as e:
        return f"替换失败: {str(e)}"

@mcp.tool()
def text_split(text: str, delimiter: str = "\n", max_splits: int = -1) -> List[str]:
    """分割文本
    
    Args:
        text: 要分割的文本
        delimiter: 分割符，默认为换行符
        max_splits: 最大分割次数，-1表示不限制
        
    Returns:
        分割后的文本列表
    """
    try:
        if max_splits == -1:
            return text.split(delimiter)
        else:
            return text.split(delimiter, max_splits)
    except Exception as e:
        return [f"分割失败: {str(e)}"]

@mcp.tool()
def text_join(texts: List[str], delimiter: str = "\n") -> str:
    """连接文本列表
    
    Args:
        texts: 要连接的文本列表
        delimiter: 连接符，默认为换行符
        
    Returns:
        连接后的文本
    """
    try:
        return delimiter.join(texts)
    except Exception as e:
        return f"连接失败: {str(e)}"

@mcp.tool()
def validate_email(email: str) -> Dict[str, Any]:
    """验证邮箱格式
    
    Args:
        email: 要验证的邮箱地址
        
    Returns:
        验证结果
    """
    try:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        is_valid = bool(re.match(pattern, email))
        
        return {
            "email": email,
            "is_valid": is_valid,
            "pattern_matched": is_valid
        }
    except Exception as e:
        return {
            "email": email,
            "is_valid": False,
            "error": str(e)
        }

@mcp.tool()
def validate_phone(phone: str) -> Dict[str, Any]:
    """验证手机号格式
    
    Args:
        phone: 要验证的手机号
        
    Returns:
        验证结果
    """
    try:
        # 中国手机号格式
        pattern = r'^1[3-9]\d{9}$'
        is_valid = bool(re.match(pattern, phone))
        
        return {
            "phone": phone,
            "is_valid": is_valid,
            "pattern_matched": is_valid,
            "country": "China"
        }
    except Exception as e:
        return {
            "phone": phone,
            "is_valid": False,
            "error": str(e)
        }

@mcp.tool()
def extract_numbers(text: str) -> List[str]:
    """从文本中提取数字
    
    Args:
        text: 要处理的文本
        
    Returns:
        提取的数字列表
    """
    try:
        pattern = r'\d+(?:\.\d+)?'
        numbers = re.findall(pattern, text)
        return numbers
    except Exception as e:
        return [f"提取失败: {str(e)}"]

@mcp.tool()
def extract_urls(text: str) -> List[str]:
    """从文本中提取URL
    
    Args:
        text: 要处理的文本
        
    Returns:
        提取的URL列表
    """
    try:
        pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        urls = re.findall(pattern, text)
        return urls
    except Exception as e:
        return [f"提取失败: {str(e)}"]

@mcp.tool()
def count_words(text: str) -> Dict[str, Any]:
    """统计文本中的单词数量
    
    Args:
        text: 要统计的文本
        
    Returns:
        统计结果
    """
    try:
        # 移除标点符号，分割单词
        words = re.findall(r'\b\w+\b', text.lower())
        
        # 统计词频
        word_count = {}
        for word in words:
            word_count[word] = word_count.get(word, 0) + 1
        
        return {
            "total_words": len(words),
            "unique_words": len(word_count),
            "word_frequency": word_count,
            "most_common": sorted(word_count.items(), key=lambda x: x[1], reverse=True)[:10]
        }
    except Exception as e:
        return {"error": f"统计失败: {str(e)}"}

@mcp.tool()
def text_case_convert(text: str, case_type: str = "lower") -> str:
    """转换文本大小写
    
    Args:
        text: 要转换的文本
        case_type: 转换类型 (lower, upper, title, capitalize)
        
    Returns:
        转换后的文本
    """
    try:
        case_functions = {
            "lower": str.lower,
            "upper": str.upper,
            "title": str.title,
            "capitalize": str.capitalize
        }
        
        if case_type not in case_functions:
            return f"不支持的转换类型: {case_type}"
        
        return case_functions[case_type](text)
    except Exception as e:
        return f"转换失败: {str(e)}" 