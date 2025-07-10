/**
 * 智能体状态管理 Store
 * 使用 Pinia 管理智能体相关的全局状态
 */
import { defineStore } from 'pinia'
import { ref, reactive, computed } from 'vue'
import { message } from 'ant-design-vue'
import { agentAPI } from '@/apis/agent_api'
import { useUserStore } from '@/stores/user'

export const useAgentStore = defineStore('agent', () => {
  // ================================================================================
  // 状态定义
  // ================================================================================
  
  // 智能体列表
  const agents = ref([])
  const customAgents = ref([])
  const systemAgents = ref([])
  
  // 当前选中的智能体
  const currentAgent = ref(null)
  const currentAgentConfig = ref({})
  
  // 加载状态
  const loading = reactive({
    agents: false,
    creating: false,
    updating: false,
    deleting: false,
    testing: false
  })
  
  // 错误状态
  const errors = reactive({
    fetch: null,
    create: null,
    update: null,
    delete: null,
    test: null
  })
  
  // 缓存配置
  const cache = reactive({
    agents: new Map(), // 智能体详情缓存
    configs: new Map(), // 配置缓存
    lastFetch: null,    // 最后获取时间
    ttl: 5 * 60 * 1000  // 缓存时间 5分钟
  })
  
  // 筛选和搜索状态
  const filters = reactive({
    search: '',
    type: '',
    scope: 'all', // all, mine, public, system
    sortBy: 'created_at',
    sortOrder: 'desc'
  })
  
  // 分页状态
  const pagination = reactive({
    current: 1,
    pageSize: 12,
    total: 0
  })
  
  // 统计信息
  const stats = reactive({
    total: 0,
    custom: 0,
    system: 0,
    active: 0,
    myAgents: 0
  })

  // ================================================================================
  // 计算属性
  // ================================================================================
  
  // 筛选后的智能体列表
  const filteredAgents = computed(() => {
    let result = [...agents.value]
    
    // 搜索过滤
    if (filters.search) {
      const searchTerm = filters.search.toLowerCase()
      result = result.filter(agent => 
        agent.name?.toLowerCase().includes(searchTerm) ||
        agent.description?.toLowerCase().includes(searchTerm)
      )
    }
    
    // 类型过滤
    if (filters.type) {
      result = result.filter(agent => agent.agent_type === filters.type)
    }
    
    // 范围过滤
    switch (filters.scope) {
      case 'mine':
        result = result.filter(agent => agent.is_mine)
        break
      case 'public':
        result = result.filter(agent => agent.is_public)
        break
      case 'system':
        result = result.filter(agent => agent.is_system)
        break
    }
    
    // 排序
    result.sort((a, b) => {
      const aVal = a[filters.sortBy]
      const bVal = b[filters.sortBy]
      
      if (filters.sortOrder === 'desc') {
        return aVal > bVal ? -1 : 1
      } else {
        return aVal > bVal ? 1 : -1
      }
    })
    
    return result
  })
  
  // 是否有筛选条件
  const hasFilters = computed(() => {
    return filters.search || filters.type || filters.scope !== 'all'
  })
  
  // 当前智能体是否为自定义智能体
  const isCurrentAgentCustom = computed(() => {
    return currentAgent.value && currentAgent.value.agent_type === 'custom'
  })
  
  // 缓存是否有效
  const isCacheValid = computed(() => {
    if (!cache.lastFetch) return false
    return Date.now() - cache.lastFetch < cache.ttl
  })

  // ================================================================================
  // 操作方法
  // ================================================================================
  
  /**
   * 获取智能体列表
   * @param {Object} options 选项
   * @param {boolean} options.forceRefresh 是否强制刷新
   * @param {boolean} options.silent 是否静默加载（不显示loading）
   */
  const fetchAgents = async (options = {}) => {
    const { forceRefresh = false, silent = false } = options
    
    // 检查缓存
    if (!forceRefresh && isCacheValid.value && agents.value.length > 0) {
      return agents.value
    }
    
    const userStore = useUserStore()
    if (!userStore.isLoggedIn) {
      errors.fetch = '用户未登录'
      // message.error('请先登录再获取智能体列表')
      return []
    }

    try {
      if (!silent) {
        loading.agents = true
      }
      errors.fetch = null
      
      const params = {
        page: pagination.current,
        page_size: pagination.pageSize,
        search: filters.search || undefined,
        agent_type: filters.type || undefined,
        only_mine: filters.scope === 'mine' || undefined,
        only_public: filters.scope === 'public' || undefined,
        sort_by: filters.sortBy,
        sort_order: filters.sortOrder
      }
      
      const response = await agentAPI.getAgents(params)
      
      if (response.success) {
        agents.value = response.data.agents || []
        pagination.total = response.data.pagination?.total || 0
        
        // 分类智能体
        customAgents.value = agents.value.filter(a => a.agent_type === 'custom')
        systemAgents.value = agents.value.filter(a => a.agent_type !== 'custom')
        
        // 更新统计
        updateStats()
        
        // 更新缓存
        cache.lastFetch = Date.now()
        agents.value.forEach(agent => {
          cache.agents.set(agent.agent_id, agent)
        })
        
        return agents.value
      } else {
        throw new Error(response.message || '获取智能体列表失败')
      }
    } catch (error) {
      console.error('获取智能体列表失败:', error)
      errors.fetch = error.message
      if (!silent) {
        message.error('获取智能体列表失败')
      }
      return []
    } finally {
      if (!silent) {
        loading.agents = false
      }
    }
  }
  
  /**
   * 获取智能体详情
   * @param {string} agentId 智能体ID
   * @param {boolean} useCache 是否使用缓存
   */
  const fetchAgentDetails = async (agentId, useCache = true) => {
    if (useCache && cache.agents.has(agentId)) {
      return cache.agents.get(agentId)
    }
    
    try {
      const response = await agentAPI.getAgent(agentId)
      if (response.success) {
        const agent = response.data
        cache.agents.set(agentId, agent)
        return agent
      } else {
        throw new Error(response.message || '获取智能体详情失败')
      }
    } catch (error) {
      console.error('获取智能体详情失败:', error)
      message.error('获取智能体详情失败')
      return null
    }
  }
  
  /**
   * 创建智能体
   * @param {Object} agentData 智能体数据
   */
  const createAgent = async (agentData) => {
    try {
      loading.creating = true
      errors.create = null
      
      const response = await agentAPI.createAgent(agentData)
      
      if (response.success) {
        message.success('智能体创建成功')
        
        // 添加到列表
        const newAgent = response.data
        agents.value.unshift(newAgent)
        
        if (newAgent.agent_type === 'custom') {
          customAgents.value.unshift(newAgent)
        } else {
          systemAgents.value.unshift(newAgent)
        }
        
        // 更新统计
        updateStats()
        
        // 更新缓存
        cache.agents.set(newAgent.agent_id, newAgent)
        
        return newAgent
      } else {
        throw new Error(response.message || '创建智能体失败')
      }
    } catch (error) {
      console.error('创建智能体失败:', error)
      errors.create = error.message
      message.error('创建智能体失败')
      return null
    } finally {
      loading.creating = false
    }
  }
  
  /**
   * 更新智能体
   * @param {string} agentId 智能体ID
   * @param {Object} updateData 更新数据
   */
  const updateAgent = async (agentId, updateData) => {
    try {
      loading.updating = true
      errors.update = null
      
      const response = await agentAPI.updateAgent(agentId, updateData)
      
      if (response.success) {
        message.success('智能体更新成功')
        
        // 更新列表中的智能体
        const updatedAgent = response.data
        const index = agents.value.findIndex(a => a.agent_id === agentId)
        if (index !== -1) {
          agents.value[index] = updatedAgent
        }
        
        // 更新分类列表
        if (updatedAgent.agent_type === 'custom') {
          const customIndex = customAgents.value.findIndex(a => a.agent_id === agentId)
          if (customIndex !== -1) {
            customAgents.value[customIndex] = updatedAgent
          }
        }
        
        // 更新缓存
        cache.agents.set(agentId, updatedAgent)
        
        // 如果是当前智能体，更新当前智能体
        if (currentAgent.value?.agent_id === agentId) {
          currentAgent.value = updatedAgent
        }
        
        return updatedAgent
      } else {
        throw new Error(response.message || '更新智能体失败')
      }
    } catch (error) {
      console.error('更新智能体失败:', error)
      errors.update = error.message
      message.error('更新智能体失败')
      return null
    } finally {
      loading.updating = false
    }
  }
  
  /**
   * 删除智能体
   * @param {string} agentId 智能体ID
   */
  const deleteAgent = async (agentId) => {
    try {
      loading.deleting = true
      errors.delete = null
      
      const response = await agentAPI.deleteAgent(agentId)
      
      if (response.success) {
        message.success('智能体删除成功')
        
        // 从列表中移除
        agents.value = agents.value.filter(a => a.agent_id !== agentId)
        customAgents.value = customAgents.value.filter(a => a.agent_id !== agentId)
        systemAgents.value = systemAgents.value.filter(a => a.agent_id !== agentId)
        
        // 更新统计
        updateStats()
        
        // 清除缓存
        cache.agents.delete(agentId)
        cache.configs.delete(agentId)
        
        // 如果删除的是当前智能体，清除当前智能体
        if (currentAgent.value?.agent_id === agentId) {
          currentAgent.value = null
          currentAgentConfig.value = {}
        }
        
        return true
      } else {
        throw new Error(response.message || '删除智能体失败')
      }
    } catch (error) {
      console.error('删除智能体失败:', error)
      errors.delete = error.message
      message.error('删除智能体失败')
      return false
    } finally {
      loading.deleting = false
    }
  }
  
  /**
   * 复制智能体
   * @param {string} agentId 智能体ID
   * @param {Object} options 复制选项
   */
  const duplicateAgent = async (agentId, options = {}) => {
    try {
      const response = await agentAPI.duplicateAgent(agentId, options)
      
      if (response.success) {
        message.success('智能体复制成功')
        
        // 添加到列表
        const newAgent = response.data
        agents.value.unshift(newAgent)
        
        if (newAgent.agent_type === 'custom') {
          customAgents.value.unshift(newAgent)
        }
        
        // 更新统计
        updateStats()
        
        // 更新缓存
        cache.agents.set(newAgent.agent_id, newAgent)
        
        return newAgent
      } else {
        throw new Error(response.message || '复制智能体失败')
      }
    } catch (error) {
      console.error('复制智能体失败:', error)
      message.error('复制智能体失败')
      return null
    }
  }
  
  /**
   * 测试智能体
   * @param {string} agentId 智能体ID
   * @param {Object} testData 测试数据
   */
  const testAgent = async (agentId, testData = {}) => {
    try {
      loading.testing = true
      errors.test = null
      
      const response = await agentAPI.testAgent(agentId, testData)
      
      if (response.success) {
        message.success('智能体测试成功')
        return response.data
      } else {
        throw new Error(response.message || '智能体测试失败')
      }
    } catch (error) {
      console.error('智能体测试失败:', error)
      errors.test = error.message
      message.error('智能体测试失败')
      return null
    } finally {
      loading.testing = false
    }
  }
  
  /**
   * 设置当前智能体
   * @param {Object} agent 智能体对象
   */
  const setCurrentAgent = (agent) => {
    currentAgent.value = agent
    
    // 加载配置到缓存
    if (agent && cache.configs.has(agent.agent_id)) {
      currentAgentConfig.value = cache.configs.get(agent.agent_id)
    } else {
      currentAgentConfig.value = {}
    }
  }
  
  /**
   * 更新当前智能体配置
   * @param {Object} config 配置对象
   */
  const updateCurrentAgentConfig = (config) => {
    currentAgentConfig.value = { ...currentAgentConfig.value, ...config }
    
    // 更新缓存
    if (currentAgent.value) {
      cache.configs.set(currentAgent.value.agent_id, currentAgentConfig.value)
    }
  }
  
  /**
   * 更新筛选条件
   * @param {Object} newFilters 新的筛选条件
   */
  const updateFilters = (newFilters) => {
    Object.assign(filters, newFilters)
    pagination.current = 1 // 重置分页
  }
  
  /**
   * 更新分页
   * @param {Object} newPagination 新的分页信息
   */
  const updatePagination = (newPagination) => {
    Object.assign(pagination, newPagination)
  }
  
  /**
   * 清除错误状态
   */
  const clearErrors = () => {
    Object.keys(errors).forEach(key => {
      errors[key] = null
    })
  }
  
  /**
   * 清除缓存
   * @param {string} type 缓存类型 'all' | 'agents' | 'configs'
   */
  const clearCache = (type = 'all') => {
    switch (type) {
      case 'agents':
        cache.agents.clear()
        break
      case 'configs':
        cache.configs.clear()
        break
      case 'all':
      default:
        cache.agents.clear()
        cache.configs.clear()
        cache.lastFetch = null
        break
    }
  }
  
  /**
   * 更新统计信息
   */
  const updateStats = () => {
    stats.total = agents.value.length
    stats.custom = customAgents.value.length
    stats.system = systemAgents.value.length
    stats.active = agents.value.filter(a => a.is_active).length
    stats.myAgents = agents.value.filter(a => a.is_mine).length
  }
  
  /**
   * 重置状态
   */
  const reset = () => {
    agents.value = []
    customAgents.value = []
    systemAgents.value = []
    currentAgent.value = null
    currentAgentConfig.value = {}
    
    Object.keys(loading).forEach(key => {
      loading[key] = false
    })
    
    clearErrors()
    clearCache()
    
    Object.assign(filters, {
      search: '',
      type: '',
      scope: 'all',
      sortBy: 'created_at',
      sortOrder: 'desc'
    })
    
    Object.assign(pagination, {
      current: 1,
      pageSize: 12,
      total: 0
    })
    
    Object.assign(stats, {
      total: 0,
      custom: 0,
      system: 0,
      active: 0,
      myAgents: 0
    })
  }

  // ================================================================================
  // 返回状态和方法
  // ================================================================================
  
  return {
    // 状态
    agents,
    customAgents,
    systemAgents,
    currentAgent,
    currentAgentConfig,
    loading,
    errors,
    filters,
    pagination,
    stats,
    
    // 计算属性
    filteredAgents,
    hasFilters,
    isCurrentAgentCustom,
    isCacheValid,
    
    // 方法
    fetchAgents,
    fetchAgentDetails,
    createAgent,
    updateAgent,
    deleteAgent,
    duplicateAgent,
    testAgent,
    setCurrentAgent,
    updateCurrentAgentConfig,
    updateFilters,
    updatePagination,
    clearErrors,
    clearCache,
    reset
  }
}) 