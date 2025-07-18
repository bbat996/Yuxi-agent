import { apiGet, apiPost, apiPut, apiDelete } from './base'

/**
 * 技能管理API模块
 * 需要用户认证才能访问的API
 * 权限要求: 任何已登录用户（普通用户、管理员、超级管理员）
 *
 * 注意: 请确保在使用这些API之前检查用户是否已登录
 */

// 技能管理API（普通用户权限）
export const skillApi = {
  /**
   * 获取技能分类列表
   * @returns {Promise} - 技能分类信息
   */
  getSkillCategories: async () => {
    return apiGet('/api/skills/categories', {}, true)
  },

  /**
   * 获取技能列表
   * @param {string} category - 技能分类，可选
   * @param {string} server - 服务器名称，可选
   * @returns {Promise} - 技能列表
   */
  getSkillsList: async (category = null, server = null) => {
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
   * 获取指定技能的详细信息
   * @param {string} skillId - 技能ID（格式：skill_工具名）
   * @returns {Promise} - 技能详细信息
   */
  getSkillDetail: async (skillId) => {
    return apiGet(`/api/skills/${encodeURIComponent(skillId)}`, {}, true)
  },

  /**
   * 测试技能功能
   * @param {string} skillId - 技能ID
   * @param {Object} testParams - 测试参数
   * @returns {Promise} - 测试结果
   */
  testSkill: async (skillId, testParams) => {
    return apiPost(`/api/skills/${encodeURIComponent(skillId)}/test`, testParams, {}, true)
  },

  /**
   * 获取技能统计信息
   * @returns {Promise} - 技能统计信息
   */
  getSkillsStats: async () => {
    return apiGet('/api/skills/stats', {}, true)
  }
}

// 导出所有API
export default {
  skillApi
} 