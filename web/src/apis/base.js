import { useUserStore } from '@/stores/user'
import { message } from 'ant-design-vue'

/**
 * 基础API请求封装
 * 提供统一的请求方法，自动处理认证头和错误
 */

/**
 * 获取认证头
 * @returns {Object} 认证头对象
 */
function getAuthHeaders() {
  const token = localStorage.getItem('user_token')
  if (!token) {
    return {}
  }
  // 确保 token 格式正确
  const tokenValue = token.startsWith('Bearer ') ? token : `Bearer ${token}`
  return { 'Authorization': tokenValue }
}

/**
 * 确保 URL 以 /api 开头
 * @param {string} url - 原始 URL
 * @returns {string} - 处理后的 URL
 */
function ensureApiPrefix(url) {
  // 如果 URL 已经是完整的 URL（以 http:// 或 https:// 开头），则直接返回
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url
  }
  // 确保 URL 以 /api 开头
  return url.startsWith('/api') ? url : `/api${url}`
}

/**
 * 发送API请求的基础函数
 * @param {string} url - API端点
 * @param {Object} options - 请求选项
 * @param {boolean} requiresAuth - 是否需要认证头
 * @returns {Promise} - 请求结果
 */
export async function apiRequest(url, options = {}, requiresAuth = false) {
  try {
    // 处理 URL
    const apiUrl = ensureApiPrefix(url)

    // 默认请求配置
    const requestOptions = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    }

    // 如果需要认证，添加认证头
    if (requiresAuth) {
      const token = localStorage.getItem('user_token')
      if (!token) {
        throw new Error('用户未登录')
      }
      Object.assign(requestOptions.headers, getAuthHeaders())
    }

    // 发送请求
    const response = await fetch(apiUrl, requestOptions)

    // 处理API返回的错误
    if (!response.ok) {
      // 尝试解析错误信息
      let errorMessage = `请求失败: ${response.status}, ${response.statusText}`
      let errorData = null

      try {
        errorData = await response.json()
        errorMessage = errorData.detail || errorData.message || errorMessage
      } catch (e) {
        // 如果无法解析JSON，使用默认错误信息
      }

      // 特殊处理401和403错误
      if (response.status === 401) {
        // 如果是认证失败，可能需要重新登录
        const userStore = useUserStore()
        if (userStore.isLoggedIn) {
          // 如果用户认为自己已登录，但收到401，则可能是令牌过期
          const isTokenExpired = errorData &&
            (errorData.detail?.includes('令牌已过期') ||
             errorData.detail?.includes('token expired') ||
             errorMessage?.includes('令牌已过期') ||
             errorMessage?.includes('token expired'))

          message.error(isTokenExpired ? '登录已过期，请重新登录' : '认证失败，请重新登录')
          userStore.logout()

          // 使用setTimeout确保消息显示后再跳转
          setTimeout(() => {
            window.location.href = '/login'
          }, 1500)
        }
        throw new Error('未授权，请先登录')
      } else if (response.status === 403) {
        throw new Error('没有权限执行此操作')
      } else if (response.status === 500) {
        throw new Error('Server 500 Error, please check the log use `docker logs api-dev`')
      }

      throw new Error(errorMessage)
    }

    // 检查Content-Type以确定如何处理响应
    const contentType = response.headers.get('Content-Type')
    if (contentType && contentType.includes('application/json')) {
      return await response.json()
    }

    return await response.text()
  } catch (error) {
    console.error('API请求错误:', error)
    throw error
  }
}

/**
 * 发送GET请求
 * @param {string} url - API端点
 * @param {Object} options - 请求选项
 * @param {boolean} requiresAuth - 是否需要认证
 * @returns {Promise} - 请求结果
 */
export function apiGet(url, options = {}, requiresAuth = false) {
  return apiRequest(url, { method: 'GET', ...options }, requiresAuth)
}

/**
 * 发送POST请求
 * @param {string} url - API端点
 * @param {Object} data - 请求体数据
 * @param {Object} options - 其他请求选项
 * @param {boolean} requiresAuth - 是否需要认证
 * @returns {Promise} - 请求结果
 */
export function apiPost(url, data = {}, options = {}, requiresAuth = false) {
  return apiRequest(
    url,
    {
      method: 'POST',
      body: JSON.stringify(data),
      ...options
    },
    requiresAuth
  )
}

/**
 * 发送PUT请求
 * @param {string} url - API端点
 * @param {Object} data - 请求体数据
 * @param {Object} options - 其他请求选项
 * @param {boolean} requiresAuth - 是否需要认证
 * @returns {Promise} - 请求结果
 */
export function apiPut(url, data = {}, options = {}, requiresAuth = false) {
  return apiRequest(
    url,
    {
      method: 'PUT',
      body: JSON.stringify(data),
      ...options
    },
    requiresAuth
  )
}

/**
 * 发送DELETE请求
 * @param {string} url - API端点
 * @param {Object} options - 请求选项
 * @param {boolean} requiresAuth - 是否需要认证
 * @returns {Promise} - 请求结果
 */
export function apiDelete(url, options = {}, requiresAuth = false) {
  return apiRequest(url, { method: 'DELETE', ...options }, requiresAuth)
}

/**
 * 健康检查API
 */
export const healthApi = {
  /**
   * 检查服务端健康状态
   * @returns {Promise} - 健康检查结果
   */
  async checkHealth() {
    try {
      const response = await apiGet('/api/health')
      return { status: 'ok', data: response }
    } catch (error) {
      return { status: 'error', error: error.message }
    }
  }
}