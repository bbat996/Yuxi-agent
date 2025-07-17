import { apiGet, apiPost, apiPut, apiDelete } from './base.js'

/**
 * 提示词模板API
 */
export const promptApi = {
  /**
   * 获取所有提示词模板
   */
  getAllTemplates() {
    return apiGet('/prompts/templates')
  },

}

export default promptApi 