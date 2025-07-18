import { apiGet, apiPost, apiPut, apiDelete } from './base'

/**
 * 网站配置管理API
 * 权限要求: 超级管理员
 */

export const siteConfigApi = {
  /**
   * 获取所有网站配置
   * @param {Object} params - 查询参数
   * @param {string} params.category - 配置分类
   * @param {boolean} params.public_only - 是否只获取公开配置
   * @returns {Promise} - 配置列表
   */
  getConfigs: (params = {}) => {
    const queryString = new URLSearchParams(params).toString()
    const url = queryString ? `/api/site-config/?${queryString}` : '/api/site-config/'
    return apiGet(url, {}, true)
  },

  /**
   * 获取公开的网站配置（无需认证）
   * @returns {Promise} - 公开配置
   */
  getPublicConfigs: () => apiGet('/api/site-config/public'),

  /**
   * 更新单个网站配置
   * @param {string} configKey - 配置键
   * @param {string} configValue - 配置值
   * @returns {Promise} - 更新结果
   */
  updateConfig: (configKey, configValue) => 
    apiPut(`/api/site-config/${configKey}`, {
      config_key: configKey,
      config_value: configValue
    }, {}, true),

  /**
   * 批量更新网站配置
   * @param {Array} configs - 配置数组
   * @param {string} configs[].config_key - 配置键
   * @param {string} configs[].config_value - 配置值
   * @returns {Promise} - 更新结果
   */
  batchUpdateConfigs: (configs) => 
    apiPut('/api/site-config/batch', { configs }, {}, true),

  /**
   * 初始化默认网站配置
   * @returns {Promise} - 初始化结果
   */
  initializeConfigs: () => apiPost('/api/site-config/initialize', {}, {}, true),

  /**
   * 删除网站配置
   * @param {string} configKey - 配置键
   * @returns {Promise} - 删除结果
   */
  deleteConfig: (configKey) => apiDelete(`/api/site-config/${configKey}`, {}, true),

  /**
   * 获取配置分类
   * @returns {Promise} - 分类列表
   */
  getCategories: () => apiGet('/api/site-config/categories', {}, true)
} 