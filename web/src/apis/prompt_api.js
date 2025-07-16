import { request } from './base.js'

/**
 * 提示词模板API
 */
export const promptApi = {
  /**
   * 获取所有提示词分类
   */
  getCategories() {
    return request.get('/prompts/categories')
  },

  /**
   * 获取所有提示词模板
   */
  getAllTemplates() {
    return request.get('/prompts/templates')
  },

  /**
   * 根据分类获取提示词模板
   * @param {string} category 分类键
   */
  getTemplatesByCategory(category) {
    return request.get(`/prompts/templates/${category}`)
  },

  /**
   * 获取特定的提示词模板
   * @param {string} category 分类键
   * @param {string} templateKey 模板键
   */
  getTemplate(category, templateKey) {
    return request.get(`/prompts/templates/${category}/${templateKey}`)
  },

  /**
   * 创建新的提示词模板
   * @param {string} category 分类键
   * @param {string} templateKey 模板键
   * @param {Object} template 模板数据
   */
  createTemplate(category, templateKey, template) {
    return request.post(`/prompts/templates/${category}/${templateKey}`, template)
  },

  /**
   * 更新提示词模板
   * @param {string} category 分类键
   * @param {string} templateKey 模板键
   * @param {Object} template 模板数据
   */
  updateTemplate(category, templateKey, template) {
    return request.put(`/prompts/templates/${category}/${templateKey}`, template)
  },

  /**
   * 删除提示词模板
   * @param {string} category 分类键
   * @param {string} templateKey 模板键
   */
  deleteTemplate(category, templateKey) {
    return request.delete(`/prompts/templates/${category}/${templateKey}`)
  },

  /**
   * 创建新的提示词分类
   * @param {Object} category 分类数据
   */
  createCategory(category) {
    return request.post('/prompts/categories', category)
  },

  /**
   * 删除提示词分类
   * @param {string} categoryKey 分类键
   */
  deleteCategory(categoryKey) {
    return request.delete(`/prompts/categories/${categoryKey}`)
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
    return request.get(`/prompts/search?${params.toString()}`)
  },

  /**
   * 获取提示词模板统计信息
   */
  getStats() {
    return request.get('/prompts/stats')
  }
}

export default promptApi 