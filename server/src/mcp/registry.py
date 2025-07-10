"""
MCP技能注册表

管理MCP技能的注册、查询和连接管理。
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from server.src.utils import logger
from server.db_manager import DBManager
from server.models.agent_models import MCPSkill
from .client import MCPClient, MCPConnectionError, MCPServerError

class MCPSkillRegistry:
    """MCP技能注册表"""
    
    def __init__(self):
        self._clients: Dict[str, MCPClient] = {}  # skill_id -> MCPClient
        self._skill_cache: Dict[str, Dict[str, Any]] = {}  # 技能缓存
        self._last_refresh = None
        self._cache_ttl = timedelta(minutes=5)  # 缓存5分钟
        self.db_manager = None
        
    def _init_db_manager(self):
        """延迟初始化数据库管理器"""
        if self.db_manager is None:
            self.db_manager = DBManager()
    
    async def refresh_skills(self, force: bool = False):
        """刷新技能列表"""
        now = datetime.now()
        
        # 检查是否需要刷新缓存
        if not force and self._last_refresh:
            if now - self._last_refresh < self._cache_ttl:
                return
        
        self._init_db_manager()
        
        try:
            with self.db_manager.get_session_context() as session:
                # 获取所有激活的MCP技能
                skills = session.query(MCPSkill).filter(
                    MCPSkill.is_active == True
                ).all()
                
                # 更新技能缓存
                new_cache = {}
                
                for skill in skills:
                    skill_data = skill.to_dict()
                    new_cache[skill.skill_id] = skill_data
                    
                    # 检查是否需要创建新的客户端
                    if skill.skill_id not in self._clients:
                        try:
                            client = MCPClient(skill.mcp_config)
                            await client.connect()
                            self._clients[skill.skill_id] = client
                            logger.info(f"MCP技能连接成功: {skill.name}")
                        except Exception as e:
                            logger.error(f"MCP技能连接失败 {skill.name}: {e}")
                            continue
                
                # 移除不再需要的客户端
                removed_skills = set(self._skill_cache.keys()) - set(new_cache.keys())
                for skill_id in removed_skills:
                    if skill_id in self._clients:
                        await self._clients[skill_id].disconnect()
                        del self._clients[skill_id]
                        logger.info(f"MCP技能连接已移除: {skill_id}")
                
                self._skill_cache = new_cache
                self._last_refresh = now
                
                logger.info(f"MCP技能注册表已刷新，共 {len(self._skill_cache)} 个技能")
                
        except Exception as e:
            logger.error(f"刷新MCP技能列表失败: {e}")
    
    async def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """获取技能信息"""
        await self.refresh_skills()
        return self._skill_cache.get(skill_id)
    
    async def get_skills(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取技能列表"""
        await self.refresh_skills()
        
        skills = list(self._skill_cache.values())
        
        if category:
            skills = [skill for skill in skills if skill.get("category") == category]
        
        return skills
    
    async def get_client(self, skill_id: str) -> Optional[MCPClient]:
        """获取技能对应的MCP客户端"""
        await self.refresh_skills()
        return self._clients.get(skill_id)
    
    async def call_skill(self, skill_id: str, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用MCP技能
        
        Args:
            skill_id: 技能ID
            tool_name: 工具名称
            parameters: 工具参数
            
        Returns:
            调用结果
        """
        client = await self.get_client(skill_id)
        if not client:
            raise MCPServerError(f"MCP技能不可用: {skill_id}")
        
        start_time = datetime.now()
        success = False
        
        try:
            result = await client.call_tool(tool_name, parameters)
            success = True
            return result
            
        except Exception as e:
            logger.error(f"调用MCP技能失败 {skill_id}/{tool_name}: {e}")
            raise
            
        finally:
            # 更新统计信息
            await self._update_skill_stats(skill_id, start_time, success)
    
    async def _update_skill_stats(self, skill_id: str, start_time: datetime, success: bool):
        """更新技能使用统计"""
        try:
            self._init_db_manager()
            
            with self.db_manager.get_session_context() as session:
                skill = session.query(MCPSkill).filter(
                    MCPSkill.skill_id == skill_id
                ).first()
                
                if skill:
                    # 更新使用次数
                    skill.usage_count = (skill.usage_count or 0) + 1
                    
                    # 更新响应时间
                    response_time = (datetime.now() - start_time).total_seconds() * 1000
                    if skill.avg_response_time is None:
                        skill.avg_response_time = response_time
                    else:
                        # 移动平均
                        skill.avg_response_time = (skill.avg_response_time * 0.8) + (response_time * 0.2)
                    
                    # 更新成功率
                    if skill.success_rate is None:
                        skill.success_rate = 100.0 if success else 0.0
                    else:
                        # 移动平均
                        current_success = 100.0 if success else 0.0
                        skill.success_rate = (skill.success_rate * 0.9) + (current_success * 0.1)
                    
                    skill.updated_at = datetime.utcnow()
                    session.commit()
                    
        except Exception as e:
            logger.error(f"更新MCP技能统计失败: {e}")
    
    async def test_skill(self, skill_id: str) -> Dict[str, Any]:
        """测试MCP技能连接"""
        client = await self.get_client(skill_id)
        if not client:
            return {
                "success": False,
                "error": "技能不可用",
                "timestamp": datetime.now().isoformat()
            }
        
        start_time = datetime.now()
        
        try:
            # 检查连接状态
            is_connected = await client.ping()
            
            if not is_connected:
                return {
                    "success": False,
                    "error": "连接失败",
                    "timestamp": datetime.now().isoformat()
                }
            
            # 获取工具列表进行测试
            tools = await client.list_tools()
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "success": True,
                "connection_status": "connected",
                "response_time": response_time,
                "available_tools": len(tools),
                "tools": [tool.get("name") for tool in tools],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "success": False,
                "error": str(e),
                "response_time": response_time,
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_skill_tools(self, skill_id: str) -> List[Dict[str, Any]]:
        """获取技能提供的工具列表"""
        client = await self.get_client(skill_id)
        if not client:
            return []
        
        try:
            return await client.list_tools()
        except Exception as e:
            logger.error(f"获取MCP技能工具列表失败 {skill_id}: {e}")
            return []
    
    async def register_skill_from_db(self, skill_id: str):
        """从数据库注册技能"""
        skill_data = await self.get_skill(skill_id)
        if not skill_data:
            raise ValueError(f"技能不存在: {skill_id}")
        
        if skill_id in self._clients:
            # 已经注册，先断开旧连接
            await self._clients[skill_id].disconnect()
        
        try:
            client = MCPClient(skill_data["mcp_config"])
            await client.connect()
            self._clients[skill_id] = client
            logger.info(f"MCP技能重新注册成功: {skill_data['name']}")
            
        except Exception as e:
            logger.error(f"MCP技能注册失败 {skill_data['name']}: {e}")
            raise
    
    async def unregister_skill(self, skill_id: str):
        """注销技能"""
        if skill_id in self._clients:
            await self._clients[skill_id].disconnect()
            del self._clients[skill_id]
            logger.info(f"MCP技能已注销: {skill_id}")
        
        if skill_id in self._skill_cache:
            del self._skill_cache[skill_id]
    
    async def get_registry_status(self) -> Dict[str, Any]:
        """获取注册表状态"""
        await self.refresh_skills()
        
        total_skills = len(self._skill_cache)
        connected_skills = len(self._clients)
        
        # 获取分类统计
        categories = {}
        for skill in self._skill_cache.values():
            category = skill.get("category", "其他")
            categories[category] = categories.get(category, 0) + 1
        
        return {
            "total_skills": total_skills,
            "connected_skills": connected_skills,
            "categories": categories,
            "last_refresh": self._last_refresh.isoformat() if self._last_refresh else None,
            "cache_ttl_seconds": self._cache_ttl.total_seconds()
        }
    
    async def shutdown(self):
        """关闭所有连接"""
        logger.info("正在关闭MCP技能注册表...")
        
        for skill_id, client in self._clients.items():
            try:
                await client.disconnect()
            except Exception as e:
                logger.error(f"关闭MCP客户端失败 {skill_id}: {e}")
        
        self._clients.clear()
        self._skill_cache.clear()
        
        logger.info("MCP技能注册表已关闭") 