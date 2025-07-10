/**
 * 模板管理API模块
 * 处理提示词模板和MCP技能的创建、查询、更新、删除等操作
 */
import { apiRequest, apiGet, apiPost, apiPut, apiDelete } from './base'

// =============================================================================
// 提示词模板相关API
// =============================================================================

/**
 * 获取提示词模板列表
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码
 * @param {number} params.page_size - 每页数量
 * @param {string} params.search - 搜索关键词
 * @param {string} params.category - 分类筛选
 * @param {boolean} params.only_mine - 只显示我的模板
 * @param {boolean} params.only_system - 只显示系统模板
 * @param {string} params.sort_by - 排序字段
 * @param {string} params.sort_order - 排序方向
 * @returns {Promise} API响应
 */
export const getPromptTemplates = (params = {}) => {
  return apiGet('/api/templates/prompts', params, true)
}

/**
 * 获取提示词模板详情
 * @param {string} templateId - 模板ID
 * @returns {Promise} API响应
 */
export const getPromptTemplate = (templateId) => {
  return apiGet(`/api/templates/prompts/${templateId}`, {}, true)
}

/**
 * 创建提示词模板
 * @param {Object} data - 模板数据
 * @param {string} data.name - 模板名称
 * @param {string} data.content - 模板内容
 * @param {string} data.category - 分类
 * @param {string} data.description - 描述
 * @param {Array} data.variables - 变量定义
 * @returns {Promise} API响应
 */
export const createPromptTemplate = (data) => {
  return apiPost('/api/templates/prompts', data, {}, true)
}

/**
 * 更新提示词模板
 * @param {string} templateId - 模板ID
 * @param {Object} data - 更新数据
 * @returns {Promise} API响应
 */
export const updatePromptTemplate = (templateId, data) => {
  return apiPut(`/api/templates/prompts/${templateId}`, data, {}, true)
}

/**
 * 删除提示词模板
 * @param {string} templateId - 模板ID
 * @returns {Promise} API响应
 */
export const deletePromptTemplate = (templateId) => {
  return apiDelete(`/api/templates/prompts/${templateId}`, {}, true)
}

/**
 * 标记模板使用
 * @param {string} templateId - 模板ID
 * @returns {Promise} API响应
 */
export const usePromptTemplate = (templateId) => {
  return apiPost(`/api/templates/prompts/${templateId}/use`, {}, {}, true)
}

// =============================================================================
// MCP技能相关API
// =============================================================================

/**
 * 获取MCP技能列表
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码
 * @param {number} params.page_size - 每页数量
 * @param {string} params.search - 搜索关键词
 * @param {string} params.category - 分类筛选
 * @param {boolean} params.only_verified - 只显示已验证的技能
 * @param {boolean} params.only_active - 只显示激活的技能
 * @param {string} params.sort_by - 排序字段
 * @param {string} params.sort_order - 排序方向
 * @returns {Promise} API响应
 */
export const getMCPSkills = (params = {}) => {
  return apiGet('/api/templates/mcp-skills', params, true)
}

/**
 * 获取MCP技能详情
 * @param {string} skillId - 技能ID
 * @returns {Promise} API响应
 */
export const getMCPSkill = (skillId) => {
  return apiGet(`/api/templates/mcp-skills/${skillId}`, {}, true)
}

/**
 * 注册MCP技能
 * @param {Object} data - 技能数据
 * @param {string} data.name - 技能名称
 * @param {string} data.description - 技能描述
 * @param {string} data.mcp_server - MCP服务器地址
 * @param {Object} data.mcp_config - MCP连接配置
 * @param {Object} data.tool_schema - 工具Schema定义
 * @param {Object} data.parameters - 默认参数配置
 * @param {string} data.category - 分类
 * @param {string} data.version - 版本号
 * @returns {Promise} API响应
 */
export const createMCPSkill = (data) => {
  return apiPost('/api/templates/mcp-skills', data, {}, true)
}

/**
 * 更新MCP技能
 * @param {string} skillId - 技能ID
 * @param {Object} data - 更新数据
 * @returns {Promise} API响应
 */
export const updateMCPSkill = (skillId, data) => {
  return apiPut(`/api/templates/mcp-skills/${skillId}`, data, {}, true)
}

/**
 * 删除MCP技能
 * @param {string} skillId - 技能ID
 * @returns {Promise} API响应
 */
export const deleteMCPSkill = (skillId) => {
  return apiDelete(`/api/templates/mcp-skills/${skillId}`, {}, true)
}

/**
 * 测试MCP技能
 * @param {string} skillId - 技能ID
 * @param {Object} testParams - 测试参数
 * @returns {Promise} API响应
 */
export const testMCPSkill = (skillId, testParams) => {
  return apiPost(`/api/templates/mcp-skills/${skillId}/test`, testParams, {}, true)
}

// =============================================================================
// 通用模板API
// =============================================================================

/**
 * 获取分类列表
 * @param {string} templateType - 模板类型 (prompt, mcp)
 * @returns {Promise} API响应
 */
export const getCategories = (templateType = 'prompt') => {
  return apiGet('/api/templates/categories', { template_type: templateType }, true)
}

/**
 * 获取模板统计信息
 * @returns {Promise} API响应
 */
export const getTemplateStats = () => {
  return apiGet('/api/templates/stats', {}, true)
}

// 模板API对象，包含所有模板相关的API方法
export const templateAPI = {
  // 提示词模板
  getPromptTemplates,
  getPromptTemplate,
  createPromptTemplate,
  updatePromptTemplate,
  deletePromptTemplate,
  usePromptTemplate,
  
  // MCP技能
  getMCPSkills,
  getMCPSkill,
  createMCPSkill,
  updateMCPSkill,
  deleteMCPSkill,
  testMCPSkill,
  
  // 通用
  getCategories,
  getTemplateStats
}

export default templateAPI 