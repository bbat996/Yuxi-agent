"""
系统工具模块
提供系统信息和监控功能
"""

from mcp.server.fastmcp import FastMCP
import os
import platform
import psutil
from typing import Dict, Any

mcp = FastMCP("system")

@mcp.tool()
def get_system_info() -> Dict[str, Any]:
    """获取系统信息
    
    Returns:
        系统信息字典
    """
    try:
        return {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "architecture": platform.architecture()[0]
        }
    except Exception as e:
        return {"error": f"获取系统信息失败: {str(e)}"}

@mcp.tool()
def get_memory_info() -> Dict[str, Any]:
    """获取内存信息
    
    Returns:
        内存信息字典
    """
    try:
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "free": memory.free,
            "percent": memory.percent,
            "swap_total": swap.total,
            "swap_used": swap.used,
            "swap_free": swap.free,
            "swap_percent": swap.percent
        }
    except Exception as e:
        return {"error": f"获取内存信息失败: {str(e)}"}

@mcp.tool()
def get_disk_info(path: str = "/") -> Dict[str, Any]:
    """获取磁盘信息
    
    Args:
        path: 磁盘路径，默认为根目录
        
    Returns:
        磁盘信息字典
    """
    try:
        disk = psutil.disk_usage(path)
        disk_io = psutil.disk_io_counters()
        
        return {
            "path": path,
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent,
            "read_count": disk_io.read_count if disk_io else 0,
            "write_count": disk_io.write_count if disk_io else 0,
            "read_bytes": disk_io.read_bytes if disk_io else 0,
            "write_bytes": disk_io.write_bytes if disk_io else 0
        }
    except Exception as e:
        return {"error": f"获取磁盘信息失败: {str(e)}"}

@mcp.tool()
def get_cpu_info() -> Dict[str, Any]:
    """获取CPU信息
    
    Returns:
        CPU信息字典
    """
    try:
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_freq = psutil.cpu_freq()
        
        return {
            "cpu_count": cpu_count,
            "cpu_percent": cpu_percent,
            "cpu_freq_current": cpu_freq.current if cpu_freq else 0,
            "cpu_freq_min": cpu_freq.min if cpu_freq else 0,
            "cpu_freq_max": cpu_freq.max if cpu_freq else 0
        }
    except Exception as e:
        return {"error": f"获取CPU信息失败: {str(e)}"}

@mcp.tool()
def get_network_info() -> Dict[str, Any]:
    """获取网络信息
    
    Returns:
        网络信息字典
    """
    try:
        network_io = psutil.net_io_counters()
        network_addrs = psutil.net_if_addrs()
        
        return {
            "bytes_sent": network_io.bytes_sent,
            "bytes_recv": network_io.bytes_recv,
            "packets_sent": network_io.packets_sent,
            "packets_recv": network_io.packets_recv,
            "interfaces": list(network_addrs.keys())
        }
    except Exception as e:
        return {"error": f"获取网络信息失败: {str(e)}"}

@mcp.tool()
def get_process_info(pid: int = None) -> Dict[str, Any]:
    """获取进程信息
    
    Args:
        pid: 进程ID，默认为当前进程
        
    Returns:
        进程信息字典
    """
    try:
        if pid is None:
            process = psutil.Process()
        else:
            process = psutil.Process(pid)
        
        return {
            "pid": process.pid,
            "name": process.name(),
            "status": process.status(),
            "cpu_percent": process.cpu_percent(),
            "memory_percent": process.memory_percent(),
            "memory_info": process.memory_info()._asdict(),
            "create_time": process.create_time(),
            "num_threads": process.num_threads()
        }
    except Exception as e:
        return {"error": f"获取进程信息失败: {str(e)}"}

@mcp.tool()
def list_processes(limit: int = 10) -> list:
    """列出进程列表
    
    Args:
        limit: 返回的进程数量限制
        
    Returns:
        进程列表
    """
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # 按CPU使用率排序
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        return processes[:limit]
    except Exception as e:
        return [{"error": f"获取进程列表失败: {str(e)}"}]

@mcp.tool()
def get_environment_variables() -> Dict[str, str]:
    """获取环境变量
    
    Returns:
        环境变量字典
    """
    try:
        return dict(os.environ)
    except Exception as e:
        return {"error": f"获取环境变量失败: {str(e)}"}

@mcp.tool()
def get_current_working_directory() -> str:
    """获取当前工作目录
    
    Returns:
        当前工作目录路径
    """
    try:
        return os.getcwd()
    except Exception as e:
        return f"获取工作目录失败: {str(e)}" 
    
    
if __name__ == "__main__":
    mcp.run()