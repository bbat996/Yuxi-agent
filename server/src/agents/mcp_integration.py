"""
MCP技能集成模块

将MCP技能集成到智能体系统中，提供MCP工具的注册和使用功能。
"""

from typing import List, Dict, Any, Optional
from langchain_core.tools import BaseTool

from server.src.utils import logger
from server.src.mcp import get_mcp_registry, MCPToolAdapter


class MCPIntegration:
    """MCP技能集成类"""

    def __init__(self):
        self.registry = get_mcp_registry()
        self.adapter = MCPToolAdapter(self.registry)
        self._initialized = False

    async def initialize(self):
        """初始化MCP集成"""
        if self._initialized:
            return

        try:
            # 刷新技能列表
            await self.registry.refresh_skills(force=True)
            self._initialized = True
            logger.info("MCP集成初始化完成")

        except Exception as e:
            logger.error(f"MCP集成初始化失败: {e}")
            raise

    async def get_mcp_tools(self, mcp_skills: List[str]) -> List[BaseTool]:
        """
        获取MCP技能对应的工具列表

        Args:
            mcp_skills: MCP技能ID列表

        Returns:
            LangChain工具列表
        """
        if not self._initialized:
            await self.initialize()

        if not mcp_skills:
            return []

        try:
            tools = await self.adapter.get_tools_for_skills(mcp_skills)
            logger.debug(f"获取MCP工具: {len(tools)} 个工具，来自 {len(mcp_skills)} 个技能")
            return tools

        except Exception as e:
            logger.error(f"获取MCP工具失败: {e}")
            return []

    async def get_available_mcp_tools(self) -> Dict[str, Any]:
        """获取所有可用的MCP工具信息"""
        if not self._initialized:
            await self.initialize()

        try:
            tools_info = await self.adapter.get_available_tools()

            # 按技能分组
            grouped_tools = {}
            for tool_info in tools_info:
                skill_id = tool_info["skill_id"]
                if skill_id not in grouped_tools:
                    grouped_tools[skill_id] = {
                        "skill_name": tool_info["skill_name"],
                        "skill_id": skill_id,
                        "category": tool_info["category"],
                        "tools": [],
                    }

                grouped_tools[skill_id]["tools"].append(
                    {
                        "name": tool_info["tool_name"],
                        "description": tool_info["tool_description"],
                        "langchain_name": tool_info["langchain_name"],
                        "schema": tool_info["schema"],
                    }
                )

            return {
                "total_skills": len(grouped_tools),
                "total_tools": len(tools_info),
                "skills": list(grouped_tools.values()),
            }

        except Exception as e:
            logger.error(f"获取可用MCP工具失败: {e}")
            return {"total_skills": 0, "total_tools": 0, "skills": []}

    async def test_mcp_skill(self, skill_id: str) -> Dict[str, Any]:
        """测试MCP技能"""
        if not self._initialized:
            await self.initialize()

        return await self.registry.test_skill(skill_id)

    async def get_registry_status(self) -> Dict[str, Any]:
        """获取MCP注册表状态"""
        if not self._initialized:
            await self.initialize()

        return await self.registry.get_registry_status()

    async def refresh_skills(self):
        """刷新技能列表"""
        try:
            await self.registry.refresh_skills(force=True)
            self.adapter.clear_cache()  # 清空工具缓存
            logger.info("MCP技能列表已刷新")

        except Exception as e:
            logger.error(f"刷新MCP技能列表失败: {e}")
            raise

    async def shutdown(self):
        """关闭MCP集成"""
        try:
            await self.registry.shutdown()
            self.adapter.clear_cache()
            self._initialized = False
            logger.info("MCP集成已关闭")

        except Exception as e:
            logger.error(f"关闭MCP集成失败: {e}")


# 全局MCP集成实例
_mcp_integration = None


def get_mcp_integration() -> MCPIntegration:
    """获取全局MCP集成实例"""
    global _mcp_integration
    if _mcp_integration is None:
        _mcp_integration = MCPIntegration()
    return _mcp_integration


async def initialize_mcp_integration():
    """初始化全局MCP集成"""
    integration = get_mcp_integration()
    await integration.initialize()


async def get_mcp_tools_for_agent(mcp_skills: List[str]) -> List[BaseTool]:
    """为智能体获取MCP工具"""
    integration = get_mcp_integration()
    return await integration.get_mcp_tools(mcp_skills)
