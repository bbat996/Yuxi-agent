import { apiGet, apiPost, apiPut, apiDelete } from './base.js'

/**
 * 提示词模板API
 */
export const promptApi = {
  /**
   * 获取所有提示词分类
   */
  getCategories() {
    return apiGet('/prompts/categories')
  },

  /**
   * 获取所有提示词模板
   */
  getAllTemplates() {
    return apiGet('/prompts/templates')
  },

  /**
   * 根据分类获取提示词模板
   * @param {string} category 分类键
   */
  getTemplatesByCategory(category) {
    return apiGet(`/prompts/templates/${category}`)
  },

  /**
   * 获取特定的提示词模板
   * @param {string} category 分类键
   * @param {string} templateKey 模板键
   */
  getTemplate(category, templateKey) {
    return apiGet(`/prompts/templates/${category}/${templateKey}`)
  },

  /**
   * 创建新的提示词模板
   * @param {string} category 分类键
   * @param {string} templateKey 模板键
   * @param {Object} template 模板数据
   */
  createTemplate(category, templateKey, template) {
    return apiPost(`/prompts/templates/${category}/${templateKey}`, template, {}, true)
  },

  /**
   * 更新提示词模板
   * @param {string} category 分类键
   * @param {string} templateKey 模板键
   * @param {Object} template 模板数据
   */
  updateTemplate(category, templateKey, template) {
    return apiPut(`/prompts/templates/${category}/${templateKey}`, template, {}, true)
  },

  /**
   * 删除提示词模板
   * @param {string} category 分类键
   * @param {string} templateKey 模板键
   */
  deleteTemplate(category, templateKey) {
    return apiDelete(`/prompts/templates/${category}/${templateKey}`, {}, true)
  },

  /**
   * 创建新的提示词分类
   * @param {Object} category 分类数据
   */
  createCategory(category) {
    return apiPost('/prompts/categories', category, {}, true)
  },

  /**
   * 删除提示词分类
   * @param {string} categoryKey 分类键
   */
  deleteCategory(categoryKey) {
    return apiDelete(`/prompts/categories/${categoryKey}`, {}, true)
  },

  /**
   * 搜索提示词模板
   * @param {string} query 搜索查询
   * @param {string} category 可选的分类过滤
   */
  searchTemplates(query, category = null) {
    const params = new URLSearchParams({ query })
    if (category) {
      params.append('category', category)
    }
    return apiGet(`/prompts/search?${params.toString()}`)
  },

  /**
   * 获取提示词模板统计信息
   */
  getStats() {
    return apiGet('/prompts/stats')
  }
}

export default promptApi 