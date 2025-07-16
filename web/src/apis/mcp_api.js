import { apiGet, apiPost, apiPut, apiDelete } from './base'
import { useUserStore } from '@/stores/user'

/**
 * MCP工具管理API模块
 * 只有管理员和超级管理员可以访问的API
 * 权限要求: admin 或 superadmin
 *
 * 注意: 请确保在使用这些API之前检查用户是否具有管理员权限
 */

// 检查当前用户是否有管理员权限
const checkAdminPermission = () => {
  const userStore = useUserStore()
  if (!userStore.isAdmin) {
    throw new Error('需要管理员权限')
  }
  return true
}

// MCP工具管理API
export const mcpToolsApi = {
  /**
   * 获取MCP工具分类列表
   * @returns {Promise} - 工具分类信息
   */
  getToolCategories: async () => {
    checkAdminPermission()
    return apiGet('/api/mcp/tools/categories', {}, true)
  },

  /**
   * 获取MCP工具列表
   * @param {string} category - 工具分类，可选
   * @returns {Promise} - 工具列表
   */
  getToolsList: async (category = null) => {
    checkAdminPermission()
    const params = category ? `?category=${encodeURIComponent(category)}` : ''
    return apiGet(`/api/mcp/tools/list${params}`, {}, true)
  },

  /**
   * 搜索MCP工具
   * @param {string} keyword - 搜索关键词
   * @returns {Promise} - 匹配的工具列表
   */
  searchTools: async (keyword) => {
    checkAdminPermission()
    return apiGet(`/api/mcp/tools/search?keyword=${encodeURIComponent(keyword)}`, {}, true)
  },

  /**
   * 获取指定MCP工具的详细信息
   * @param {string} toolName - 工具名称
   * @returns {Promise} - 工具详细信息
   */
  getToolDetail: async (toolName) => {
    checkAdminPermission()
    return apiGet(`/api/mcp/tools/${encodeURIComponent(toolName)}`, {}, true)
  },

  /**
   * 获取MCP工具概览信息
   * @returns {Promise} - 工具概览信息
   */
  getToolsOverview: async () => {
    checkAdminPermission()
    return apiGet('/api/mcp/tools/overview', {}, true)
  },

  /**
   * 获取指定分类的MCP工具列表
   * @param {string} categoryName - 分类名称
   * @returns {Promise} - 该分类下的工具列表
   */
  getToolsByCategory: async (categoryName) => {
    checkAdminPermission()
    return apiGet(`/api/mcp/tools/category/${encodeURIComponent(categoryName)}`, {}, true)
  },

  /**
   * 获取随机的MCP工具列表
   * @param {number} count - 返回的工具数量
   * @param {string} category - 限制在指定分类内，可选
   * @returns {Promise} - 随机工具列表
   */
  getRandomTools: async (count = 5, category = null) => {
    checkAdminPermission()
    let params = `?count=${count}`
    if (category) {
      params += `&category=${encodeURIComponent(category)}`
    }
    return apiGet(`/api/mcp/tools/random${params}`, {}, true)
  }
}

// MCP配置管理API
export const mcpConfigApi = {
  /**
   * 获取MCP配置摘要信息
   * @returns {Promise} - MCP配置摘要
   */
  getConfigSummary: async () => {
    checkAdminPermission()
    return apiGet('/api/mcp/config/summary', {}, true)
  },

  /**
   * 获取MCP服务器列表
   * @param {string} serverType - 服务器类型：builtin或external，可选
   * @returns {Promise} - MCP服务器列表
   */
  getServers: async (serverType = null) => {
    checkAdminPermission()
    const params = serverType ? `?server_type=${serverType}` : ''
    return apiGet(`/api/mcp/config/servers${params}`, {}, true)
  },

  /**
   * 获取指定MCP服务器的详细信息
   * @param {string} serverName - 服务器名称
   * @returns {Promise} - 服务器详细信息
   */
  getServerDetail: async (serverName) => {
    checkAdminPermission()
    return apiGet(`/api/mcp/config/servers/${encodeURIComponent(serverName)}`, {}, true)
  },

  /**
   * 重新加载MCP配置
   * @returns {Promise} - 重新加载结果
   */
  reloadConfig: async () => {
    checkAdminPermission()
    return apiPost('/api/mcp/config/reload', {}, {}, true)
  },

  /**
   * 验证MCP配置
   * @returns {Promise} - 配置验证结果
   */
  validateConfig: async () => {
    checkAdminPermission()
    return apiGet('/api/mcp/config/validate', {}, true)
  }
}

// 技能管理API（管理员权限）
export const skillManagementApi = {
  /**
   * 获取技能分类列表
   * @returns {Promise} - 技能分类信息
   */
  getSkillCategories: async () => {
    checkAdminPermission()
    return apiGet('/api/skills/categories', {}, true)
  },

  /**
   * 获取技能列表
   * @param {string} category - 技能分类，可选
   * @param {string} server - 服务器名称，可选
   * @returns {Promise} - 技能列表
   */
  getSkillsList: async (category = null, server = null) => {
    checkAdminPermission()
    let params = ''
    if (category) {
      params += `?category=${encodeURIComponent(category)}`
    }
    if (server) {
      params += params ? `&server=${encodeURIComponent(server)}` : `?server=${encodeURIComponent(server)}`
    }
    return apiGet(`/api/skills/list${params}`, {}, true)
  },

  /**
   * 搜索技能
   * @param {string} keyword - 搜索关键词
   * @returns {Promise} - 匹配的技能列表
   */
  searchSkills: async (keyword) => {
    checkAdminPermission()
    return apiGet(`/api/skills/search?keyword=${encodeURIComponent(keyword)}`, {}, true)
  },

  /**
   * 获取指定技能的详细信息
   * @param {string} skillId - 技能ID（格式：skill_工具名）
   * @returns {Promise} - 技能详细信息
   */
  getSkillDetail: async (skillId) => {
    checkAdminPermission()
    return apiGet(`/api/skills/${encodeURIComponent(skillId)}`, {}, true)
  },

  /**
   * 测试技能功能
   * @param {string} skillId - 技能ID
   * @param {Object} testParams - 测试参数
   * @returns {Promise} - 测试结果
   */
  testSkill: async (skillId, testParams) => {
    checkAdminPermission()
    return apiPost(`/api/skills/${encodeURIComponent(skillId)}/test`, testParams, {}, true)
  },

  /**
   * 获取技能统计信息
   * @returns {Promise} - 技能统计信息
   */
  getSkillsStats: async () => {
    checkAdminPermission()
    return apiGet('/api/skills/stats', {}, true)
  }
}

// 导出所有API
export default {
  mcpToolsApi,
  mcpConfigApi,
  skillManagementApi
} 