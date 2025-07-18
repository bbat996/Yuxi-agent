/**
 * 模板管理API模块
 * 处理提示词模板和MCP技能的创建、查询、更新、删除等操作
 */
import { apiRequest, apiGet, apiPost, apiPut, apiDelete } from './base'
import { skillApi } from './skill_api'

// =============================================================================
// 提示词模板相关API（只保留查询接口）
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
  return apiGet('/api/skills/prompts', params, true)
}

/**
 * 获取提示词模板详情
 * @param {string} templateId - 模板ID
 * @returns {Promise} API响应
 */
export const getPromptTemplate = (templateId) => {
  return apiGet(`/api/skills/prompts/${templateId}`, {}, true)
}

// =============================================================================
// MCP技能相关API
// =============================================================================

/**
 * 获取MCP技能列表
 * @param {Object} params - 查询参数
 * @param {string} params.category - 分类筛选
 * @param {string} params.server - 服务器筛选
 * @returns {Promise} API响应
 */
export const getMCPSkills = (params = {}) => {
  return skillApi.getSkillsList(params.category, params.server)
}

/**
 * 获取MCP技能详情
 * @param {string} skillId - 技能ID
 * @returns {Promise} API响应
 */
export const getMCPSkill = (skillId) => {
  return skillApi.getSkillDetail(skillId)
}

/**
 * 注册MCP技能（暂不支持创建，只能查看现有技能）
 * @param {Object} data - 技能数据
 * @returns {Promise} API响应
 */
export const createMCPSkill = (data) => {
  // 目前后端不支持创建MCP技能，只能查看现有技能
  return Promise.reject(new Error('暂不支持创建MCP技能，只能查看现有技能'))
}

/**
 * 更新MCP技能（暂不支持更新，只能查看现有技能）
 * @param {string} skillId - 技能ID
 * @param {Object} data - 更新数据
 * @returns {Promise} API响应
 */
export const updateMCPSkill = (skillId, data) => {
  // 目前后端不支持更新MCP技能，只能查看现有技能
  return Promise.reject(new Error('暂不支持更新MCP技能，只能查看现有技能'))
}

/**
 * 删除MCP技能（暂不支持删除，只能查看现有技能）
 * @param {string} skillId - 技能ID
 * @returns {Promise} API响应
 */
export const deleteMCPSkill = (skillId) => {
  // 目前后端不支持删除MCP技能，只能查看现有技能
  return Promise.reject(new Error('暂不支持删除MCP技能，只能查看现有技能'))
}

/**
 * 测试MCP技能
 * @param {string} skillId - 技能ID
 * @param {Object} testParams - 测试参数
 * @returns {Promise} API响应
 */
export const testMCPSkill = (skillId, testParams) => {
  return skillApi.testSkill(skillId, testParams)
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
  if (templateType === 'mcp') {
    return skillApi.getSkillCategories()
  }
  return apiGet('/api/skills/categories', { template_type: templateType }, true)
}

/**
 * 获取模板统计信息
 * @returns {Promise} API响应
 */
export const getTemplateStats = () => {
  return skillApi.getSkillsStats()
}

// 模板API对象，包含所有模板相关的API方法
export const templateAPI = {
  // 提示词模板（只保留查询）
  getPromptTemplates,
  getPromptTemplate,

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