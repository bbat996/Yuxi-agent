/**
 * 智能体管理API模块
 * 处理智能体的创建、查询、更新、删除等操作
 */
import { apiRequest, apiGet, apiPost, apiPut, apiDelete } from './base'
import { useUserStore } from '@/stores/user'

/**
 * 获取智能体列表
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码
 * @param {number} params.page_size - 每页数量
 * @param {string} params.search - 搜索关键词
 * @param {string} params.agent_type - 智能体类型
 * @param {boolean} params.only_mine - 只显示我的智能体
 * @param {boolean} params.only_public - 只显示公开智能体
 * @param {string} params.sort_by - 排序字段
 * @param {string} params.sort_order - 排序方向
 * @returns {Promise} API响应
 */
export const getAgents = (params = {}) => {
  // Filter out undefined and null values
  const filteredParams = Object.fromEntries(
    Object.entries(params).filter(([_, value]) => value !== undefined && value !== null)
  )
  const queryString = new URLSearchParams(filteredParams).toString()
  const url = queryString ? `/agents?${queryString}` : '/agents'
  return apiGet(url, {}, true)
}

/**
 * 获取智能体详情
 * @param {string} agentId - 智能体ID
 * @returns {Promise} API响应
 */
export const getAgent = (agentId) => {
  return apiGet(`/api/agents/${agentId}`, {}, true)
}

/**
 * 创建智能体
 * @param {Object} agentData - 智能体数据
 * @param {string} agentData.name - 智能体名称
 * @param {string} agentData.description - 智能体描述
 * @param {string} agentData.system_prompt - 系统提示词
 * @param {Object} agentData.llm_config - 语言模型配置
 * @param {string} agentData.llm_config.provider - 模型提供商
 * @param {string} agentData.llm_config.model - 模型名称
 * @param {Object} agentData.llm_config.config - 模型参数配置
 * @param {Object} agentData.knowledge_config - 知识库配置
 * @param {boolean} agentData.knowledge_config.enabled - 是否启用知识库
 * @param {Array} agentData.knowledge_config.databases - 知识库数据库列表
 * @param {Object} agentData.knowledge_config.retrieval_config - 检索配置
 * @param {number} agentData.knowledge_config.retrieval_config.top_k - 检索返回的文档数量
 * @param {number} agentData.knowledge_config.retrieval_config.similarity_threshold - 相似度阈值
 * @param {Object} agentData.mcp_config - MCP配置
 * @param {boolean} agentData.mcp_config.enabled - 是否启用MCP服务
 * @param {Array} agentData.mcp_config.servers - MCP服务器列表
 * @param {Array} agentData.tools - 工具列表
 * @returns {Promise} API响应
 */
export const createAgent = (agentData) => {
  return apiPost('/api/agents', agentData, {}, true)
}

/**
 * 更新智能体
 * @param {string} agentId - 智能体ID
 * @param {Object} agentData - 更新的智能体数据
 * @returns {Promise} API响应
 */
export const updateAgent = (agentId, agentData) => {
  return apiPut(`/api/agents/${agentId}`, agentData, {}, true)
}

/**
 * 删除智能体
 * @param {string} agentId - 智能体ID
 * @returns {Promise} API响应
 */
export const deleteAgent = (agentId) => {
  return apiDelete(`/api/agents/${agentId}`, {}, true)
}

/**
 * 复制智能体
 * @param {string} agentId - 源智能体ID
 * @param {Object} options - 复制选项
 * @param {string} options.new_name - 新智能体名称
 * @returns {Promise} API响应
 */
export const duplicateAgent = (agentId, options = {}) => {
  return apiPost(`/api/agents/${agentId}/duplicate`, options, {}, true)
}

/**
 * 获取智能体实例状态
 * @param {string} agentId - 智能体ID
 * @returns {Promise} API响应
 */
export const getAgentInstance = (agentId) => {
  return apiGet(`/api/agents/${agentId}/instance`, {}, true)
}

/**
 * 创建智能体实例
 * @param {string} agentId - 智能体ID
 * @param {Object} config - 实例配置覆盖
 * @param {Object} config.llm_config - 语言模型配置覆盖
 * @param {Object} config.knowledge_config - 知识库配置覆盖
 * @param {Object} config.mcp_config - MCP配置覆盖
 * @param {Array} config.tools - 工具列表覆盖
 * @returns {Promise} API响应
 */
export const createAgentInstance = (agentId, config = {}) => {
  return apiPost(`/api/agents/${agentId}/instance`, config, {}, true)
}

/**
 * 更新智能体实例配置
 * @param {string} agentId - 智能体ID
 * @param {Object} config - 实例配置
 * @returns {Promise} API响应
 */
export const updateAgentInstance = (agentId, config) => {
  return apiPut(`/api/agents/${agentId}/instance`, config, {}, true)
}

/**
 * 删除智能体实例
 * @param {string} agentId - 智能体ID
 * @returns {Promise} API响应
 */
export const deleteAgentInstance = (agentId) => {
  return apiDelete(`/api/agents/${agentId}/instance`, {}, true)
}

/**
 * 测试智能体配置
 * @param {Object} agentData - 智能体配置数据
 * @param {string} testMessage - 测试消息
 * @returns {Promise} API响应
 */
export const testAgent = (agentData, testMessage) => {
  return apiPost('/api/agents/test', {
    agent_config: agentData,
    test_message: testMessage
  }, {}, true)
}

/**
 * 获取智能体使用统计
 * @param {string} agentId - 智能体ID
 * @param {Object} params - 查询参数
 * @param {string} params.start_date - 开始日期
 * @param {string} params.end_date - 结束日期
 * @returns {Promise} API响应
 */
export const getAgentStats = (agentId, params = {}) => {
  const queryString = new URLSearchParams(params).toString()
  const url = queryString
    ? `/api/agents/${agentId}/stats?${queryString}`
    : `/api/agents/${agentId}/stats`
  return apiGet(url, {}, true)
}

/**
 * 导出智能体配置
 * @param {string} agentId - 智能体ID
 * @returns {Promise} API响应
 */
export const exportAgent = (agentId) => {
  return apiGet(`/api/agents/${agentId}/export`, {}, true)
}

/**
 * 导入智能体配置
 * @param {Object} agentConfig - 智能体配置
 * @returns {Promise} API响应
 */
export const importAgent = (agentConfig) => {
  return apiPost('/api/agents/import', agentConfig, {}, true)
}

/**
 * 分享智能体
 * @param {string} agentId - 智能体ID
 * @param {Object} shareConfig - 分享配置
 * @param {boolean} shareConfig.is_public - 是否公开
 * @param {Array} shareConfig.shared_users - 分享给的用户ID列表
 * @returns {Promise} API响应
 */
export const shareAgent = (agentId, shareConfig) => {
  return apiPost(`/api/agents/${agentId}/share`, shareConfig, {}, true)
}

/**
 * 取消分享智能体
 * @param {string} agentId - 智能体ID
 * @returns {Promise} API响应
 */
export const unshareAgent = (agentId) => {
  return apiDelete(`/api/agents/${agentId}/share`, {}, true)
}

/**
 * 上传智能体头像
 * @param {FormData} formData - 包含头像文件的FormData
 * @param {string} agentId - 智能体ID
 * @returns {Promise} API响应
 */
export const uploadAgentAvatar = async (formData, agentId) => {
  const userStore = useUserStore()
  const authHeaders = userStore.getAuthHeaders()

  return fetch(`/api/agents/${agentId}/avatar`, {
    method: 'POST',
    headers: {
      ...authHeaders
    },
    body: formData
  }).then(res => {
    if (!res.ok) {
      throw new Error(`头像上传失败: ${res.status} ${res.statusText}`)
    }
    return res.json()
  })
}

// 智能体API对象，包含所有智能体相关的API方法
export const agentAPI = {
  getAgents,
  getAgent,
  createAgent,
  updateAgent,
  deleteAgent,
  duplicateAgent,
  getAgentInstance,
  createAgentInstance,
  updateAgentInstance,
  deleteAgentInstance,
  testAgent,
  getAgentStats,
  exportAgent,
  importAgent,
  shareAgent,
  unshareAgent,
  uploadAgentAvatar
}
