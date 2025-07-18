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
   * 获取MCP服务器列表
   * @param {boolean} enabledOnly - 是否只返回已启用的服务器，可选
   * @param {string[]|string} categories - 分类key数组或单个分类key，可多选
   * @returns {Promise} - MCP服务器列表
   */
  getServers: async (enabledOnly = false, categories = []) => {
    checkAdminPermission()
    const params = new URLSearchParams()
    if (enabledOnly) params.append('enabled_only', 'true')
    
    // 如果是多个分类，并行请求后合并结果
    if (Array.isArray(categories) && categories.length > 0) {
      const requests = categories.map(cat => {
        const catParams = new URLSearchParams(params)
        catParams.append('category', cat)
        return apiGet(`/api/mcp/config/servers?${catParams.toString()}`, {}, true)
      })
      
      const responses = await Promise.all(requests)
      const merged = {}
      
      responses.forEach(res => {
        if (res.success && res.data && res.data.servers) {
          Object.assign(merged, res.data.servers)
        }
      })
      
      return { 
        success: true, 
        data: { 
          servers: merged,
          total: Object.keys(merged).length,
          enabled_only: enabledOnly,
          category: categories
        } 
      }
    }
    // 单个分类或无分类筛选
    else if (typeof categories === 'string' && categories) {
      params.append('category', categories)
    }
    
    const queryString = params.toString()
    const url = queryString ? `/api/mcp/config/servers?${queryString}` : '/api/mcp/config/servers'
    return apiGet(url, {}, true)
  },

  /**
   * 获取所有MCP分类
   * @returns {Promise} - 分类列表
   */
  getCategories: async () => {
    checkAdminPermission()
    return apiGet('/api/mcp/categories', {}, true)
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


// 导出所有API
export default {
  tools: mcpToolsApi,
  config: mcpConfigApi,
}