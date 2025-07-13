"""
MCP客户端实现

提供与MCP服务器的连接和通信功能。
"""

import asyncio
import json
import aiohttp
import subprocess
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import uuid

from server.src.utils import logger


class MCPConnectionError(Exception):
    """MCP连接错误"""

    pass


class MCPServerError(Exception):
    """MCP服务器错误"""

    pass


class MCPClient:
    """MCP客户端"""

    def __init__(self, server_config: Dict[str, Any]):
        """
        初始化MCP客户端

        Args:
            server_config: MCP服务器配置
                {
                    "type": "http" | "stdio" | "sse",
                    "url": "http://localhost:3000" (for http/sse),
                    "command": ["python", "server.py"] (for stdio),
                    "env": {},  # 环境变量
                    "timeout": 30,  # 超时时间
                    "headers": {}  # HTTP头部（仅HTTP）
                }
        """
        self.config = server_config
        self.session = None
        self.process = None
        self.is_connected = False
        self.request_id = 0

    async def connect(self) -> bool:
        """连接到MCP服务器"""
        try:
            if self.config["type"] == "http":
                await self._connect_http()
            elif self.config["type"] == "stdio":
                await self._connect_stdio()
            elif self.config["type"] == "sse":
                await self._connect_sse()
            else:
                raise MCPConnectionError(f"不支持的MCP服务器类型: {self.config['type']}")

            self.is_connected = True
            logger.info(f"MCP客户端连接成功: {self.config}")
            return True

        except Exception as e:
            logger.error(f"MCP客户端连接失败: {e}")
            raise MCPConnectionError(f"连接MCP服务器失败: {e}")

    async def disconnect(self):
        """断开MCP服务器连接"""
        try:
            if self.session:
                await self.session.close()
                self.session = None

            if self.process:
                self.process.terminate()
                await asyncio.sleep(1)  # 等待进程终止
                if self.process.poll() is None:
                    self.process.kill()
                self.process = None

            self.is_connected = False
            logger.info("MCP客户端连接已断开")

        except Exception as e:
            logger.error(f"断开MCP连接时出错: {e}")

    async def _connect_http(self):
        """连接HTTP类型的MCP服务器"""
        timeout = aiohttp.ClientTimeout(total=self.config.get("timeout", 30))
        headers = self.config.get("headers", {})

        self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)

        # 测试连接
        async with self.session.get(f"{self.config['url']}/health") as response:
            if response.status != 200:
                raise MCPConnectionError(f"MCP服务器健康检查失败: {response.status}")

    async def _connect_stdio(self):
        """连接STDIO类型的MCP服务器"""
        env = self.config.get("env", {})

        self.process = await asyncio.create_subprocess_exec(
            *self.config["command"],
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        # 等待进程启动
        await asyncio.sleep(1)

        if self.process.poll() is not None:
            stderr = await self.process.stderr.read()
            raise MCPConnectionError(f"MCP服务器进程启动失败: {stderr.decode()}")

    async def _connect_sse(self):
        """连接SSE类型的MCP服务器"""
        # SSE连接实现
        # 这里先简化实现，后续可以扩展
        await self._connect_http()

    def _get_next_request_id(self) -> str:
        """获取下一个请求ID"""
        self.request_id += 1
        return str(self.request_id)

    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用MCP工具

        Args:
            tool_name: 工具名称
            parameters: 工具参数

        Returns:
            工具执行结果
        """
        if not self.is_connected:
            raise MCPConnectionError("MCP客户端未连接")

        request_data = {
            "jsonrpc": "2.0",
            "id": self._get_next_request_id(),
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": parameters},
        }

        try:
            if self.config["type"] == "http":
                return await self._call_tool_http(request_data)
            elif self.config["type"] == "stdio":
                return await self._call_tool_stdio(request_data)
            else:
                raise MCPServerError(f"不支持的调用方式: {self.config['type']}")

        except Exception as e:
            logger.error(f"调用MCP工具失败: {e}")
            raise MCPServerError(f"调用MCP工具失败: {e}")

    async def _call_tool_http(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """通过HTTP调用MCP工具"""
        async with self.session.post(f"{self.config['url']}/jsonrpc", json=request_data) as response:
            if response.status != 200:
                raise MCPServerError(f"HTTP请求失败: {response.status}")

            result = await response.json()

            if "error" in result:
                raise MCPServerError(f"MCP工具调用错误: {result['error']}")

            return result.get("result", {})

    async def _call_tool_stdio(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """通过STDIO调用MCP工具"""
        if not self.process:
            raise MCPConnectionError("STDIO进程未启动")

        # 发送请求
        request_json = json.dumps(request_data) + "\n"
        self.process.stdin.write(request_json.encode())
        await self.process.stdin.drain()

        # 读取响应
        response_line = await self.process.stdout.readline()
        if not response_line:
            raise MCPServerError("从MCP服务器读取响应失败")

        try:
            result = json.loads(response_line.decode().strip())
        except json.JSONDecodeError as e:
            raise MCPServerError(f"解析MCP响应失败: {e}")

        if "error" in result:
            raise MCPServerError(f"MCP工具调用错误: {result['error']}")

        return result.get("result", {})

    async def list_tools(self) -> List[Dict[str, Any]]:
        """获取MCP服务器上可用的工具列表"""
        if not self.is_connected:
            raise MCPConnectionError("MCP客户端未连接")

        request_data = {"jsonrpc": "2.0", "id": self._get_next_request_id(), "method": "tools/list", "params": {}}

        try:
            if self.config["type"] == "http":
                result = await self._call_tool_http(request_data)
            elif self.config["type"] == "stdio":
                result = await self._call_tool_stdio(request_data)
            else:
                raise MCPServerError(f"不支持的调用方式: {self.config['type']}")

            return result.get("tools", [])

        except Exception as e:
            logger.error(f"获取MCP工具列表失败: {e}")
            raise MCPServerError(f"获取MCP工具列表失败: {e}")

    async def get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
        """获取特定工具的Schema"""
        tools = await self.list_tools()

        for tool in tools:
            if tool.get("name") == tool_name:
                return tool

        raise MCPServerError(f"工具不存在: {tool_name}")

    async def ping(self) -> bool:
        """检查MCP服务器连接状态"""
        try:
            if not self.is_connected:
                return False

            if self.config["type"] == "http":
                async with self.session.get(f"{self.config['url']}/health") as response:
                    return response.status == 200
            elif self.config["type"] == "stdio":
                return self.process and self.process.poll() is None

            return True

        except Exception:
            return False

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.disconnect()
