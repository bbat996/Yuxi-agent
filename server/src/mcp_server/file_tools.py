"""
文件工具模块
提供文件和目录操作功能
"""

from mcp.server.fastmcp import FastMCP
import os
import json
import hashlib
import base64
from pathlib import Path
from typing import List, Dict, Any

mcp = FastMCP("file")

@mcp.tool()
def read_file(file_path: str, encoding: str = "utf-8") -> str:
    """读取文件内容
    
    Args:
        file_path: 文件路径
        encoding: 文件编码，默认为"utf-8"
        
    Returns:
        文件内容
    """
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except Exception as e:
        return f"读取文件失败: {str(e)}"

@mcp.tool()
def write_file(file_path: str, content: str, encoding: str = "utf-8") -> str:
    """写入文件内容
    
    Args:
        file_path: 文件路径
        content: 要写入的内容
        encoding: 文件编码，默认为"utf-8"
        
    Returns:
        操作结果
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        return f"文件写入成功: {file_path}"
    except Exception as e:
        return f"写入文件失败: {str(e)}"

@mcp.tool()
def list_directory(path: str = ".") -> List[Dict[str, Any]]:
    """列出目录内容
    
    Args:
        path: 目录路径，默认为当前目录
        
    Returns:
        目录内容列表
    """
    try:
        items = []
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            stat = os.stat(item_path)
            
            items.append({
                "name": item,
                "path": item_path,
                "is_file": os.path.isfile(item_path),
                "is_directory": os.path.isdir(item_path),
                "size": stat.st_size,
                "modified": stat.st_mtime
            })
        
        return items
    except Exception as e:
        return [{"error": f"列出目录失败: {str(e)}"}]

@mcp.tool()
def get_file_info(file_path: str) -> Dict[str, Any]:
    """获取文件信息
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件信息字典
    """
    try:
        if not os.path.exists(file_path):
            return {"error": "文件不存在"}
        
        stat = os.stat(file_path)
        
        return {
            "path": file_path,
            "name": os.path.basename(file_path),
            "size": stat.st_size,
            "is_file": os.path.isfile(file_path),
            "is_directory": os.path.isdir(file_path),
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "accessed": stat.st_atime,
            "permissions": oct(stat.st_mode)[-3:]
        }
    except Exception as e:
        return {"error": f"获取文件信息失败: {str(e)}"}

@mcp.tool()
def json_parse(json_str: str) -> Dict[str, Any]:
    """解析JSON字符串
    
    Args:
        json_str: JSON字符串
        
    Returns:
        解析后的对象
    """
    try:
        return json.loads(json_str)
    except Exception as e:
        return {"error": f"JSON解析失败: {str(e)}"}

@mcp.tool()
def json_stringify(obj: Dict[str, Any], indent: int = 2) -> str:
    """将对象转换为JSON字符串
    
    Args:
        obj: 要转换的对象
        indent: 缩进空格数
        
    Returns:
        JSON字符串
    """
    try:
        return json.dumps(obj, indent=indent, ensure_ascii=False)
    except Exception as e:
        return f"JSON序列化失败: {str(e)}"

@mcp.tool()
def text_to_base64(text: str, encoding: str = "utf-8") -> str:
    """将文本转换为Base64编码
    
    Args:
        text: 要转换的文本
        encoding: 文本编码
        
    Returns:
        Base64编码字符串
    """
    try:
        bytes_data = text.encode(encoding)
        return base64.b64encode(bytes_data).decode('ascii')
    except Exception as e:
        return f"Base64编码失败: {str(e)}"

@mcp.tool()
def base64_to_text(base64_str: str, encoding: str = "utf-8") -> str:
    """将Base64编码转换为文本
    
    Args:
        base64_str: Base64编码字符串
        encoding: 目标文本编码
        
    Returns:
        解码后的文本
    """
    try:
        bytes_data = base64.b64decode(base64_str)
        return bytes_data.decode(encoding)
    except Exception as e:
        return f"Base64解码失败: {str(e)}"

@mcp.tool()
def calculate_hash(text: str, algorithm: str = "md5") -> str:
    """计算文本的哈希值
    
    Args:
        text: 要计算哈希的文本
        algorithm: 哈希算法 (md5, sha1, sha256, sha512)
        
    Returns:
        哈希值
    """
    try:
        algorithms = {
            "md5": hashlib.md5,
            "sha1": hashlib.sha1,
            "sha256": hashlib.sha256,
            "sha512": hashlib.sha512
        }
        
        if algorithm not in algorithms:
            return f"不支持的哈希算法: {algorithm}"
        
        hash_func = algorithms[algorithm]
        return hash_func(text.encode('utf-8')).hexdigest()
    except Exception as e:
        return f"计算哈希失败: {str(e)}"

@mcp.tool()
def create_directory(dir_path: str) -> str:
    """创建目录
    
    Args:
        dir_path: 目录路径
        
    Returns:
        操作结果
    """
    try:
        os.makedirs(dir_path, exist_ok=True)
        return f"目录创建成功: {dir_path}"
    except Exception as e:
        return f"创建目录失败: {str(e)}"

@mcp.tool()
def delete_file(file_path: str) -> str:
    """删除文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        操作结果
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return f"文件删除成功: {file_path}"
        else:
            return f"文件不存在: {file_path}"
    except Exception as e:
        return f"删除文件失败: {str(e)}" 
    
if __name__ == "__main__":
    mcp.run()
    