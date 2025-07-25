import { apiGet, apiPost, apiDelete, apiPut } from './base'
import { useUserStore } from '@/stores/user'

/**
 * 需要用户认证的API模块
 * 用户必须登录才能访问的API
 * 权限要求: 任何已登录用户（普通用户、管理员、超级管理员）
 */

// 聊天相关API
export const chatApi = {
  /**
   * 发送聊天消息
   * @param {Object} params - 聊天参数
   * @returns {Promise} - 聊天响应流
   */
  sendMessage: (params) => {
    return fetch('/api/chat/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...useUserStore().getAuthHeaders()
      },
      body: JSON.stringify(params),
    })
  },

  /**
   * 发送可中断的聊天消息
   * @param {Object} params - 聊天参数
   * @param {AbortSignal} signal - 用于中断请求的信号控制器
   * @returns {Promise} - 聊天响应流
   */
  sendMessageWithAbort: (params, signal) => {
    return fetch('/api/chat/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...useUserStore().getAuthHeaders()
      },
      body: JSON.stringify(params),
      signal // 添加 signal 用于中断请求
    })
  },

  /**
   * 发送聊天消息到指定智能体（流式响应）
   * @param {string} agentId - 智能体ID
   * @param {Object} data - 聊天数据
   * @returns {Promise} - 聊天响应流
   */
  sendAgentMessage: (agentId, data) => {
    return fetch(`/api/chat/agent/${agentId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...useUserStore().getAuthHeaders()
      },
      body: JSON.stringify(data)
    })
  },

  /**
   * 简单聊天调用（非流式）
   * @param {string} query - 查询内容
   * @returns {Promise} - 聊天响应
   */
  simpleCall: (query) => apiPost('/api/chat/call', { query }, {}, true),



  /**
   * 获取智能体列表
   * @returns {Promise} - 智能体列表
   */
  getAgents: () => apiGet('/api/chat/agent', {}, true),

  /**
   * 获取单个智能体详情
   * @param {string} agentId - 智能体ID
   * @returns {Promise} - 智能体详情
   */
  getAgentDetail: (agentId) => apiGet(`/api/chat/agent/${agentId}`, {}, true),

  /**
   * 获取智能体历史消息
   * @param {string} agentName - 智能体名称
   * @param {string} threadId - 会话ID
   * @returns {Promise} - 历史消息
   */
  getAgentHistory: (agentName, threadId) => apiGet(`/api/chat/agent/${agentName}/history?thread_id=${threadId}`, {}, true),

  /**
   * 获取可用工具列表
   * @returns {Promise} - 工具列表
   */
  getTools: () => apiGet('/api/chat/tools', {}, true),

  /**
   * 获取模型提供商的模型列表
   * @param {string} provider - 模型提供商
   * @returns {Promise} - 模型列表
   */
  getProviderModels: (provider) => {
    return fetch(`/api/model/models?model_provider=${provider}`, {
      headers: {
        ...useUserStore().getAuthHeaders()
      }
    }).then(response => response.json())
  },

  /**
   * 更新模型提供商的模型列表
   * @param {string} provider - 模型提供商
   * @param {Array} models - 选中的模型列表
   * @returns {Promise} - 更新结果
   */
  updateProviderModels: (provider, models) => {
    return fetch(`/api/model/models/update?model_provider=${provider}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...useUserStore().getAuthHeaders()
      },
      body: JSON.stringify(models)
    }).then(response => response.json())
  },

  /**
   * 获取模型提供商配置
   * @param {string} provider - 模型提供商
   * @returns {Promise} - 提供商配置
   */
  getProviderConfig: (provider) => {
    return fetch(`/api/model/provider/${provider}/config`, {
      headers: {
        ...useUserStore().getAuthHeaders()
      }
    }).then(response => response.json())
  },

  /**
   * 更新模型提供商配置
   * @param {string} provider - 模型提供商
   * @param {Object} config - 配置信息 {base_url, api_key}
   * @returns {Promise} - 更新结果
   */
  updateProviderConfig: (provider, config) => {
    return fetch(`/api/model/provider/${provider}/config`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...useUserStore().getAuthHeaders()
      },
      body: JSON.stringify(config)
    }).then(response => response.json())
  },

  /**
   * 为模型提供商添加模型
   * @param {string} provider - 模型提供商
   * @param {string} modelName - 模型名称
   * @returns {Promise} - 添加结果
   */
  addProviderModel: (provider, modelName) => {
    return fetch(`/api/model/provider/${provider}/models/add`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...useUserStore().getAuthHeaders()
      },
      body: JSON.stringify(modelName)
    }).then(response => response.json())
  },

  /**
   * 从模型提供商删除模型
   * @param {string} provider - 模型提供商
   * @param {string} modelName - 模型名称
   * @returns {Promise} - 删除结果
   */
  removeProviderModel: (provider, modelName) => {
    return fetch(`/api/model/provider/${provider}/models/${modelName}`, {
      method: 'DELETE',
      headers: {
        ...useUserStore().getAuthHeaders()
      }
    }).then(response => response.json())
  },

  /**
   * 测试模型提供商连接
   * @param {string} provider - 模型提供商
   * @param {Object} config - 配置信息 {base_url, api_key}
   * @returns {Promise} - 测试结果
   */
  testProviderConnection: (provider, config) => {
    return fetch(`/api/model/provider/${provider}/test`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...useUserStore().getAuthHeaders()
      },
      body: JSON.stringify(config)
    }).then(response => response.json())
  },

  /**
   * 切换模型提供商启用状态
   * @param {string} provider - 模型提供商
   * @param {boolean} enabled - 是否启用
   * @returns {Promise} - 切换结果
   */
  toggleProviderStatus: (provider, enabled) => {
    return fetch(`/api/model/provider/${provider}/toggle`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...useUserStore().getAuthHeaders()
      },
      body: JSON.stringify({ enabled })
    }).then(response => response.json())
  }
}

// 用户设置API
export const userSettingsApi = {
  /**
   * 获取用户设置
   * @returns {Promise} - 用户设置
   */
  getSettings: () => apiGet('/api/user/settings', {}, true),

  /**
   * 更新用户设置
   * @param {Object} settings - 新设置
   * @returns {Promise} - 更新结果
   */
  updateSettings: (settings) => apiPost('/api/user/settings', settings, {}, true),
}

// 对话线程相关API
export const threadApi = {
  /**
   * 获取对话线程列表
   * @param {string} agentId - 智能体ID
   * @returns {Promise} - 对话线程列表
   */
  getThreads: (agentId) => {
    const url = agentId ? `/api/chat/threads?agent_id=${agentId}` : '/api/chat/threads';
    return apiGet(url, {}, true);
  },

  /**
   * 创建新对话线程
   * @param {string} agentId - 智能体ID
   * @param {string} title - 对话标题
   * @param {Object} metadata - 元数据
   * @returns {Promise} - 创建结果
   */
  createThread: (agentId, title, metadata) => apiPost('/api/chat/thread', {
    agent_id: agentId,
    title: title || '新对话',
    metadata: metadata || {}
  }, {}, true),

  /**
   * 更新对话线程
   * @param {string} threadId - 对话线程ID
   * @param {string} title - 对话标题
   * @param {string} description - 对话描述
   * @returns {Promise} - 更新结果
   */
  updateThread: (threadId, title, description) => apiPut(`/api/chat/thread/${threadId}`, {
    title,
    description
  }, {}, true),

  /**
   * 删除对话线程
   * @param {string} threadId - 对话线程ID
   * @returns {Promise} - 删除结果
   */
  deleteThread: (threadId) => apiDelete(`/api/chat/thread/${threadId}`, {}, true)
};

// 其他需要用户认证的API可以继续添加到这里

// 个人信息管理API
export const profileApi = {
  /**
   * 获取个人信息
   * @returns {Promise} - 个人信息
   */
  getProfile: () => apiGet('/api/auth/profile', {}, true),

  /**
   * 更新个人信息
   * @param {Object} profileData - 个人信息数据
   * @param {string} profileData.display_name - 显示名称
   * @param {string} profileData.email - 邮箱
   * @param {string} profileData.avatar - 头像
   * @returns {Promise} - 更新结果
   */
  updateProfile: (profileData) => apiPut('/api/auth/profile', profileData, {}, true),

  /**
   * 修改密码
   * @param {Object} passwordData - 密码数据
   * @param {string} passwordData.current_password - 当前密码
   * @param {string} passwordData.new_password - 新密码
   * @returns {Promise} - 修改结果
   */
  changePassword: (passwordData) => apiPost('/api/auth/change-password', passwordData, {}, true),

  /**
   * 获取个人统计信息
   * @returns {Promise} - 统计信息
   */
  getStats: () => apiGet('/api/auth/profile/stats', {}, true),

  /**
   * 获取个人文件存储信息
   * @returns {Promise} - 存储信息
   */
  getFileStorage: () => apiGet('/api/auth/profile/file-storage', {}, true)
}