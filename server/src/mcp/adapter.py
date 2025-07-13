"""
MCP工具适配器

将MCP技能转换为LangChain工具，使其能够在智能体中使用。
"""

import json
from typing import Dict, Any, List, Optional, Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from server.src.utils import logger
from .registry import MCPSkillRegistry
from .client import MCPServerError


class MCPToolAdapter:
    """MCP工具适配器"""

    def __init__(self, registry: MCPSkillRegistry):
        self.registry = registry
        self._tool_cache: Dict[str, BaseTool] = {}

    async def get_tools_for_skill(self, skill_id: str) -> List[BaseTool]:
        """获取技能对应的所有工具"""
        tools = []

        try:
            # 获取技能信息
            skill_data = await self.registry.get_skill(skill_id)
            if not skill_data:
                logger.warning(f"技能不存在: {skill_id}")
                return []

            # 获取技能提供的工具列表
            mcp_tools = await self.registry.get_skill_tools(skill_id)

            for mcp_tool in mcp_tools:
                tool = await self._create_langchain_tool(skill_id, mcp_tool)
                if tool:
                    tools.append(tool)

            logger.debug(f"为技能 {skill_id} 创建了 {len(tools)} 个工具")
            return tools

        except Exception as e:
            logger.error(f"获取MCP技能工具失败 {skill_id}: {e}")
            return []

    async def get_tools_for_skills(self, skill_ids: List[str]) -> List[BaseTool]:
        """获取多个技能对应的所有工具"""
        all_tools = []

        for skill_id in skill_ids:
            tools = await self.get_tools_for_skill(skill_id)
            all_tools.extend(tools)

        return all_tools

    async def _create_langchain_tool(self, skill_id: str, mcp_tool: Dict[str, Any]) -> Optional[BaseTool]:
        """创建LangChain工具"""
        try:
            tool_name = mcp_tool.get("name")
            if not tool_name:
                logger.warning(f"MCP工具缺少名称: {mcp_tool}")
                return None

            # 生成唯一的工具键
            tool_key = f"{skill_id}_{tool_name}"

            # 检查缓存
            if tool_key in self._tool_cache:
                return self._tool_cache[tool_key]

            # 创建工具
            tool = self._create_tool_class(skill_id, mcp_tool)
            self._tool_cache[tool_key] = tool

            return tool

        except Exception as e:
            logger.error(f"创建LangChain工具失败 {skill_id}/{mcp_tool.get('name')}: {e}")
            return None

    def _create_tool_class(self, skill_id: str, mcp_tool: Dict[str, Any]) -> BaseTool:
        """动态创建工具类"""
        tool_name = mcp_tool.get("name")
        tool_description = mcp_tool.get("description", f"MCP工具: {tool_name}")
        tool_schema = mcp_tool.get("inputSchema", {})

        # 创建参数模型
        args_schema = self._create_args_schema(tool_schema)

        class MCPTool(BaseTool):
            name: str = f"mcp_{skill_id}_{tool_name}"
            description: str = tool_description
            args_schema: Type[BaseModel] = args_schema

            def __init__(self, registry: MCPSkillRegistry, skill_id: str, tool_name: str):
                super().__init__()
                self.registry = registry
                self.skill_id = skill_id
                self.tool_name = tool_name

            async def _arun(self, **kwargs) -> str:
                """异步执行工具"""
                try:
                    # 调用MCP技能
                    result = await self.registry.call_skill(self.skill_id, self.tool_name, kwargs)

                    # 格式化返回结果
                    if isinstance(result, dict):
                        if "content" in result:
                            return str(result["content"])
                        elif "text" in result:
                            return str(result["text"])
                        else:
                            return json.dumps(result, ensure_ascii=False, indent=2)
                    else:
                        return str(result)

                except MCPServerError as e:
                    error_msg = f"MCP技能调用失败: {e}"
                    logger.error(error_msg)
                    return error_msg
                except Exception as e:
                    error_msg = f"工具执行错误: {e}"
                    logger.error(error_msg)
                    return error_msg

            def _run(self, **kwargs) -> str:
                """同步执行工具（不推荐）"""
                import asyncio

                try:
                    loop = asyncio.get_event_loop()
                    return loop.run_until_complete(self._arun(**kwargs))
                except Exception as e:
                    return f"同步调用错误: {e}"

        return MCPTool(self.registry, skill_id, tool_name)

    def _create_args_schema(self, tool_schema: Dict[str, Any]) -> Type[BaseModel]:
        """根据MCP工具Schema创建参数模型"""
        properties = tool_schema.get("properties", {})
        required = tool_schema.get("required", [])

        # 动态创建字段
        fields = {}

        for prop_name, prop_def in properties.items():
            prop_type = prop_def.get("type", "string")
            prop_description = prop_def.get("description", "")
            prop_default = prop_def.get("default")

            # 转换类型
            python_type = self._convert_json_type(prop_type)

            # 检查是否必需
            is_required = prop_name in required

            if is_required and prop_default is None:
                field_info = Field(description=prop_description)
            else:
                field_info = Field(default=prop_default, description=prop_description)

            fields[prop_name] = (python_type, field_info)

        # 如果没有字段，创建一个空的模型
        if not fields:
            fields["_dummy"] = (Optional[str], Field(default=None, description="占位符"))

        # 动态创建模型
        return type(
            "MCPToolArgs",
            (BaseModel,),
            {
                "__annotations__": {name: field_type for name, (field_type, _) in fields.items()},
                **{name: field_info for name, (_, field_info) in fields.items()},
            },
        )

    def _convert_json_type(self, json_type: str) -> Type:
        """转换JSON Schema类型到Python类型"""
        type_mapping = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": List[Any],
            "object": Dict[str, Any],
        }

        return type_mapping.get(json_type, str)

    def clear_cache(self):
        """清空工具缓存"""
        self._tool_cache.clear()
        logger.info("MCP工具缓存已清空")

    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """获取所有可用的MCP工具信息"""
        tools_info = []

        skills = await self.registry.get_skills()

        for skill in skills:
            skill_id = skill["skill_id"]
            skill_name = skill["name"]

            try:
                mcp_tools = await self.registry.get_skill_tools(skill_id)

                for mcp_tool in mcp_tools:
                    tool_info = {
                        "skill_id": skill_id,
                        "skill_name": skill_name,
                        "tool_name": mcp_tool.get("name"),
                        "tool_description": mcp_tool.get("description"),
                        "langchain_name": f"mcp_{skill_id}_{mcp_tool.get('name')}",
                        "schema": mcp_tool.get("inputSchema", {}),
                        "category": skill.get("category", "其他"),
                    }
                    tools_info.append(tool_info)

            except Exception as e:
                logger.error(f"获取技能工具信息失败 {skill_id}: {e}")

        return tools_info

    async def test_tool(self, skill_id: str, tool_name: str, test_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """测试MCP工具"""
        if test_params is None:
            test_params = {}

        try:
            # 获取工具
            tools = await self.get_tools_for_skill(skill_id)
            target_tool = None

            for tool in tools:
                if tool.name.endswith(f"_{tool_name}"):
                    target_tool = tool
                    break

            if not target_tool:
                return {
                    "success": False,
                    "error": f"工具不存在: {tool_name}",
                    "timestamp": __import__("datetime").datetime.now().isoformat(),
                }

            # 执行工具
            start_time = __import__("datetime").datetime.now()
            result = await target_tool._arun(**test_params)
            end_time = __import__("datetime").datetime.now()

            response_time = (end_time - start_time).total_seconds() * 1000

            return {
                "success": True,
                "result": result,
                "response_time": response_time,
                "timestamp": end_time.isoformat(),
            }

        except Exception as e:
            return {"success": False, "error": str(e), "timestamp": __import__("datetime").datetime.now().isoformat()}
