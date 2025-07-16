import { apiGet, apiPost } from './base.js'
import { checkAdminPermission, checkUserPermission } from '../utils/auth.js'

// MCP工具管理API
export const mcpToolsApi = {
  /**
   * 获取MCP工具分类列表
   * @returns {Promise} - 工具分类信息
   */
  getCategories: async () => {
    checkAdminPermission()
    return apiGet('/api/mcp/tools/categories', {}, true)
  },

  /**
   * 获取MCP工具列表
   * @param {string} category - 工具分类（服务器名称），可选
   * @param {string} server - 服务器名称，可选
   * @returns {Promise} - 工具列表
   */
  getToolsList: async (category = null, server = null) => {
    checkAdminPermission()
    const params = new URLSearchParams()
    if (category) params.append('category', category)
    if (server) params.append('server', server)
    const queryString = params.toString()
    const url = queryString ? `/api/mcp/tools/list?${queryString}` : '/api/mcp/tools/list'
    return apiGet(url, {}, true)
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
   * @param {string} categoryName - 分类名称（服务器名称）
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
    const params = new URLSearchParams()
    params.append('count', count)
    if (category) params.append('category', category)
    return apiGet(`/api/mcp/tools/random?${params.toString()}`, {}, true)
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
   * @param {boolean} enabledOnly - 是否只返回已启用的服务器，可选
   * @returns {Promise} - MCP服务器列表
   */
  getServers: async (enabledOnly = false) => {
    checkAdminPermission()
    const params = enabledOnly ? '?enabled_only=true' : ''
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
   * 切换MCP服务器启用状态
   * @param {string} serverName - 服务器名称
   * @param {boolean} enabled - 是否启用
   * @returns {Promise} - 切换结果
   */
  toggleServerStatus: async (serverName, enabled) => {
    checkAdminPermission()
    return apiPost(`/api/mcp/config/servers/${encodeURIComponent(serverName)}/toggle`, { enabled }, {}, true)
  },

  /**
   * 添加外部MCP服务器
   * @param {Object} serverConfig - 服务器配置
   * @returns {Promise} - 添加结果
   */
  addExternalServer: async (serverConfig) => {
    checkAdminPermission()
    return apiPost('/api/mcp/config/servers/external', serverConfig, {}, true)
  },

  /**
   * 更新MCP服务器配置
   * @param {string} serverName - 服务器名称
   * @param {Object} serverConfig - 服务器配置
   * @returns {Promise} - 更新结果
   */
  updateServerConfig: async (serverName, serverConfig) => {
    checkAdminPermission()
    return apiPost(`/api/mcp/config/servers/${encodeURIComponent(serverName)}/update`, serverConfig, {}, true)
  },

  /**
   * 删除MCP服务器
   * @param {string} serverName - 服务器名称
   * @returns {Promise} - 删除结果
   */
  deleteServer: async (serverName) => {
    checkAdminPermission()
    return apiPost(`/api/mcp/config/servers/${encodeURIComponent(serverName)}/delete`, {}, {}, true)
  }
}

// 技能管理API
export const skillsApi = {
  /**
   * 获取技能分类列表
   * @returns {Promise} - 技能分类信息
   */
  getCategories: async () => {
    checkUserPermission()
    return apiGet('/api/skills/categories', {}, true)
  },

  /**
   * 获取技能列表
   * @param {string} category - 技能分类，可选
   * @param {string} server - 服务器名称，可选
   * @returns {Promise} - 技能列表
   */
  getSkillsList: async (category = null, server = null) => {
    checkUserPermission()
    const params = new URLSearchParams()
    if (category) params.append('category', category)
    if (server) params.append('server', server)
    const queryString = params.toString()
    const url = queryString ? `/api/skills/list?${queryString}` : '/api/skills/list'
    return apiGet(url, {}, true)
  },

  /**
   * 搜索技能
   * @param {string} keyword - 搜索关键词
   * @returns {Promise} - 匹配的技能列表
   */
  searchSkills: async (keyword) => {
    checkUserPermission()
    return apiGet(`/api/skills/search?keyword=${encodeURIComponent(keyword)}`, {}, true)
  },

  /**
   * 获取指定技能的详细信息
   * @param {string} skillId - 技能ID（格式：skill_工具名）
   * @returns {Promise} - 技能详细信息
   */
  getSkillDetail: async (skillId) => {
    checkUserPermission()
    return apiGet(`/api/skills/${encodeURIComponent(skillId)}`, {}, true)
  },

  /**
   * 测试技能功能
   * @param {string} skillId - 技能ID
   * @param {Object} testParams - 测试参数
   * @returns {Promise} - 测试结果
   */
  testSkill: async (skillId, testParams) => {
    checkUserPermission()
    return apiPost(`/api/skills/${encodeURIComponent(skillId)}/test`, testParams, {}, true)
  },

  /**
   * 获取技能统计信息
   * @returns {Promise} - 技能统计信息
   */
  getSkillsStats: async () => {
    checkUserPermission()
    return apiGet('/api/skills/stats', {}, true)
  }
}

// 导出所有API
export default {
  tools: mcpToolsApi,
  config: mcpConfigApi,
  skills: skillsApi
} 