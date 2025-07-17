/**
 * 发布渠道API模块
 * 处理智能体的发布渠道、API接口和网站嵌入等功能
 */
import { apiRequest, apiGet, apiPost, apiPut, apiDelete } from './base'

/**
 * 获取智能体的发布配置
 * @param {string} agentId - 智能体ID
 * @returns {Promise} API响应
 */
export const getPublishConfig = (agentId) => {
  return apiGet(`/api/agents/${agentId}/publish`, {}, true)
}

/**
 * 更新智能体的发布配置
 * @param {string} agentId - 智能体ID
 * @param {Object} config - 发布配置
 * @returns {Promise} API响应
 */
export const updatePublishConfig = (agentId, config) => {
  return apiPut(`/api/agents/${agentId}/publish`, config, {}, true)
}

/**
 * 获取智能体的渠道列表
 * @param {string} agentId - 智能体ID
 * @returns {Promise} API响应
 */
export const getChannels = (agentId) => {
  return apiGet(`/api/agents/${agentId}/channels`, {}, true)
}

/**
 * 创建智能体渠道
 * @param {string} agentId - 智能体ID
 * @param {Object} channelData - 渠道数据
 * @returns {Promise} API响应
 */
export const createChannel = (agentId, channelData) => {
  return apiPost(`/api/agents/${agentId}/channels`, channelData, {}, true)
}

/**
 * 更新智能体渠道
 * @param {string} agentId - 智能体ID
 * @param {string} channelId - 渠道ID
 * @param {Object} channelData - 渠道数据
 * @returns {Promise} API响应
 */
export const updateChannel = (agentId, channelId, channelData) => {
  return apiPut(`/api/agents/${agentId}/channels/${channelId}`, channelData, {}, true)
}

/**
 * 删除智能体渠道
 * @param {string} agentId - 智能体ID
 * @param {string} channelId - 渠道ID
 * @returns {Promise} API响应
 */
export const deleteChannel = (agentId, channelId) => {
  return apiDelete(`/api/agents/${agentId}/channels/${channelId}`, {}, true)
}

/**
 * 更新渠道状态
 * @param {string} agentId - 智能体ID
 * @param {string} channelId - 渠道ID
 * @param {string} status - 状态 (active/inactive)
 * @returns {Promise} API响应
 */
export const updateChannelStatus = (agentId, channelId, status) => {
  return apiPut(`/api/agents/${agentId}/channels/${channelId}/status`, { status }, {}, true)
}

/**
 * 获取API设置
 * @param {string} agentId - 智能体ID
 * @returns {Promise} API响应
 */
export const getApiSettings = (agentId) => {
  return apiGet(`/api/agents/${agentId}/api-settings`, {}, true)
}

/**
 * 更新API设置
 * @param {string} agentId - 智能体ID
 * @param {Object} settings - API设置
 * @returns {Promise} API响应
 */
export const updateApiSettings = (agentId, settings) => {
  return apiPut(`/api/agents/${agentId}/api-settings`, settings, {}, true)
}

/**
 * 重新生成API密钥
 * @param {string} agentId - 智能体ID
 * @returns {Promise} API响应
 */
export const regenerateApiKey = (agentId) => {
  return apiPost(`/api/agents/${agentId}/api-settings/regenerate-key`, {}, {}, true)
}

/**
 * 获取嵌入设置
 * @param {string} agentId - 智能体ID
 * @returns {Promise} API响应
 */
export const getEmbedSettings = (agentId) => {
  return apiGet(`/api/agents/${agentId}/embed-settings`, {}, true)
}

/**
 * 更新嵌入设置
 * @param {string} agentId - 智能体ID
 * @param {Object} settings - 嵌入设置
 * @returns {Promise} API响应
 */
export const updateEmbedSettings = (agentId, settings) => {
  return apiPut(`/api/agents/${agentId}/embed-settings`, settings, {}, true)
}

/**
 * 获取渠道访问统计
 * @param {string} agentId - 智能体ID
 * @param {Object} params - 查询参数
 * @param {string} params.channel_id - 渠道ID
 * @param {string} params.start_date - 开始日期
 * @param {string} params.end_date - 结束日期
 * @returns {Promise} API响应
 */
export const getChannelStats = (agentId, params = {}) => {
  const queryString = new URLSearchParams(params).toString()
  const url = queryString
    ? `/api/agents/${agentId}/channel-stats?${queryString}`
    : `/api/agents/${agentId}/channel-stats`
  return apiGet(url, {}, true)
}

// 发布渠道API对象，包含所有发布渠道相关的API方法
export const publishAPI = {
  getPublishConfig,
  updatePublishConfig,
  getChannels,
  createChannel,
  updateChannel,
  deleteChannel,
  updateChannelStatus,
  getApiSettings,
  updateApiSettings,
  regenerateApiKey,
  getEmbedSettings,
  updateEmbedSettings,
  getChannelStats
};
