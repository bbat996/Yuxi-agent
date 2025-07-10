/**
 * 模板状态管理 Store
 * 使用 Pinia 管理提示词模板和MCP技能相关的全局状态
 */
import { defineStore } from 'pinia'
import { ref, reactive, computed } from 'vue'
import { message } from 'ant-design-vue'
import { templateAPI } from '@/apis/template_api'

export const useTemplateStore = defineStore('template', () => {
  // ================================================================================
  // 状态定义
  // ================================================================================
  
  // 提示词模板
  const promptTemplates = ref([])
  const promptCategories = ref([])
  
  // MCP技能
  const mcpSkills = ref([])
  const mcpCategories = ref([])
  
  // 加载状态
  const loading = reactive({
    promptTemplates: false,
    mcpSkills: false,
    creating: false,
    updating: false,
    deleting: false,
    testing: false
  })
  
  // 错误状态
  const errors = reactive({
    promptTemplates: null,
    mcpSkills: null,
    create: null,
    update: null,
    delete: null,
    test: null
  })
  
  // 缓存配置
  const cache = reactive({
    promptTemplates: new Map(),
    mcpSkills: new Map(),
    lastFetchPrompts: null,
    lastFetchSkills: null,
    ttl: 10 * 60 * 1000  // 缓存时间 10分钟
  })
  
  // 筛选条件
  const promptFilters = reactive({
    search: '',
    category: '',
    is_system: null,
    sortBy: 'created_at',
    sortOrder: 'desc'
  })
  
  const mcpFilters = reactive({
    search: '',
    category: '',
    status: '',
    sortBy: 'created_at',
    sortOrder: 'desc'
  })
  
  // 分页状态
  const promptPagination = reactive({
    current: 1,
    pageSize: 20,
    total: 0
  })
  
  const mcpPagination = reactive({
    current: 1,
    pageSize: 20,
    total: 0
  })
  
  // 统计信息
  const stats = reactive({
    promptTemplates: {
      total: 0,
      system: 0,
      user: 0,
      categories: 0
    },
    mcpSkills: {
      total: 0,
      active: 0,
      inactive: 0,
      categories: 0
    }
  })

  // ================================================================================
  // 计算属性
  // ================================================================================
  
  // 筛选后的提示词模板
  const filteredPromptTemplates = computed(() => {
    let result = [...promptTemplates.value]
    
    // 搜索过滤
    if (promptFilters.search) {
      const searchTerm = promptFilters.search.toLowerCase()
      result = result.filter(template => 
        template.name?.toLowerCase().includes(searchTerm) ||
        template.description?.toLowerCase().includes(searchTerm) ||
        template.content?.toLowerCase().includes(searchTerm)
      )
    }
    
    // 分类过滤
    if (promptFilters.category) {
      result = result.filter(template => template.category === promptFilters.category)
    }
    
    // 系统模板过滤
    if (promptFilters.is_system !== null) {
      result = result.filter(template => template.is_system === promptFilters.is_system)
    }
    
    // 排序
    result.sort((a, b) => {
      const aVal = a[promptFilters.sortBy]
      const bVal = b[promptFilters.sortBy]
      
      if (promptFilters.sortOrder === 'desc') {
        return aVal > bVal ? -1 : 1
      } else {
        return aVal > bVal ? 1 : -1
      }
    })
    
    return result
  })
  
  // 筛选后的MCP技能
  const filteredMcpSkills = computed(() => {
    let result = [...mcpSkills.value]
    
    // 搜索过滤
    if (mcpFilters.search) {
      const searchTerm = mcpFilters.search.toLowerCase()
      result = result.filter(skill => 
        skill.name?.toLowerCase().includes(searchTerm) ||
        skill.description?.toLowerCase().includes(searchTerm)
      )
    }
    
    // 分类过滤
    if (mcpFilters.category) {
      result = result.filter(skill => skill.category === mcpFilters.category)
    }
    
    // 状态过滤
    if (mcpFilters.status) {
      result = result.filter(skill => skill.status === mcpFilters.status)
    }
    
    // 排序
    result.sort((a, b) => {
      const aVal = a[mcpFilters.sortBy]
      const bVal = b[mcpFilters.sortBy]
      
      if (mcpFilters.sortOrder === 'desc') {
        return aVal > bVal ? -1 : 1
      } else {
        return aVal > bVal ? 1 : -1
      }
    })
    
    return result
  })
  
  // 提示词模板是否有筛选条件
  const hasPromptFilters = computed(() => {
    return promptFilters.search || promptFilters.category || promptFilters.is_system !== null
  })
  
  // MCP技能是否有筛选条件
  const hasMcpFilters = computed(() => {
    return mcpFilters.search || mcpFilters.category || mcpFilters.status
  })
  
  // 提示词模板缓存是否有效
  const isPromptCacheValid = computed(() => {
    if (!cache.lastFetchPrompts) return false
    return Date.now() - cache.lastFetchPrompts < cache.ttl
  })
  
  // MCP技能缓存是否有效
  const isMcpCacheValid = computed(() => {
    if (!cache.lastFetchSkills) return false
    return Date.now() - cache.lastFetchSkills < cache.ttl
  })

  // ================================================================================
  // 提示词模板操作方法
  // ================================================================================
  
  /**
   * 获取提示词模板列表
   * @param {Object} options 选项
   */
  const fetchPromptTemplates = async (options = {}) => {
    const { forceRefresh = false, silent = false } = options
    
    if (!forceRefresh && isPromptCacheValid.value && promptTemplates.value.length > 0) {
      return promptTemplates.value
    }
    
    try {
      if (!silent) {
        loading.promptTemplates = true
      }
      errors.promptTemplates = null
      
      const params = {
        page: promptPagination.current,
        page_size: promptPagination.pageSize,
        search: promptFilters.search || undefined,
        category: promptFilters.category || undefined,
        is_system: promptFilters.is_system,
        sort_by: promptFilters.sortBy,
        sort_order: promptFilters.sortOrder
      }
      
      const response = await templateAPI.getPromptTemplates(params)
      
      if (response.success) {
        promptTemplates.value = response.data.templates || []
        promptPagination.total = response.data.pagination?.total || 0
        
        // 提取分类
        extractPromptCategories()
        
        // 更新统计
        updatePromptStats()
        
        // 更新缓存
        cache.lastFetchPrompts = Date.now()
        promptTemplates.value.forEach(template => {
          cache.promptTemplates.set(template.id, template)
        })
        
        return promptTemplates.value
      } else {
        throw new Error(response.message || '获取提示词模板失败')
      }
    } catch (error) {
      console.error('获取提示词模板失败:', error)
      errors.promptTemplates = error.message
      if (!silent) {
        message.error('获取提示词模板失败')
      }
      return []
    } finally {
      if (!silent) {
        loading.promptTemplates = false
      }
    }
  }
  
  /**
   * 创建提示词模板
   * @param {Object} templateData 模板数据
   */
  const createPromptTemplate = async (templateData) => {
    try {
      loading.creating = true
      errors.create = null
      
      const response = await templateAPI.createPromptTemplate(templateData)
      
      if (response.success) {
        message.success('提示词模板创建成功')
        
        const newTemplate = response.data
        promptTemplates.value.unshift(newTemplate)
        
        // 更新分类和统计
        extractPromptCategories()
        updatePromptStats()
        
        // 更新缓存
        cache.promptTemplates.set(newTemplate.id, newTemplate)
        
        return newTemplate
      } else {
        throw new Error(response.message || '创建提示词模板失败')
      }
    } catch (error) {
      console.error('创建提示词模板失败:', error)
      errors.create = error.message
      message.error('创建提示词模板失败')
      return null
    } finally {
      loading.creating = false
    }
  }
  
  /**
   * 更新提示词模板
   * @param {string} templateId 模板ID
   * @param {Object} updateData 更新数据
   */
  const updatePromptTemplate = async (templateId, updateData) => {
    try {
      loading.updating = true
      errors.update = null
      
      const response = await templateAPI.updatePromptTemplate(templateId, updateData)
      
      if (response.success) {
        message.success('提示词模板更新成功')
        
        const updatedTemplate = response.data
        const index = promptTemplates.value.findIndex(t => t.id === templateId)
        if (index !== -1) {
          promptTemplates.value[index] = updatedTemplate
        }
        
        // 更新分类和统计
        extractPromptCategories()
        updatePromptStats()
        
        // 更新缓存
        cache.promptTemplates.set(templateId, updatedTemplate)
        
        return updatedTemplate
      } else {
        throw new Error(response.message || '更新提示词模板失败')
      }
    } catch (error) {
      console.error('更新提示词模板失败:', error)
      errors.update = error.message
      message.error('更新提示词模板失败')
      return null
    } finally {
      loading.updating = false
    }
  }
  
  /**
   * 删除提示词模板
   * @param {string} templateId 模板ID
   */
  const deletePromptTemplate = async (templateId) => {
    try {
      loading.deleting = true
      errors.delete = null
      
      const response = await templateAPI.deletePromptTemplate(templateId)
      
      if (response.success) {
        message.success('提示词模板删除成功')
        
        promptTemplates.value = promptTemplates.value.filter(t => t.id !== templateId)
        
        // 更新分类和统计
        extractPromptCategories()
        updatePromptStats()
        
        // 清除缓存
        cache.promptTemplates.delete(templateId)
        
        return true
      } else {
        throw new Error(response.message || '删除提示词模板失败')
      }
    } catch (error) {
      console.error('删除提示词模板失败:', error)
      errors.delete = error.message
      message.error('删除提示词模板失败')
      return false
    } finally {
      loading.deleting = false
    }
  }

  // ================================================================================
  // MCP技能操作方法
  // ================================================================================
  
  /**
   * 获取MCP技能列表
   * @param {Object} options 选项
   */
  const fetchMcpSkills = async (options = {}) => {
    const { forceRefresh = false, silent = false } = options
    
    if (!forceRefresh && isMcpCacheValid.value && mcpSkills.value.length > 0) {
      return mcpSkills.value
    }
    
    try {
      if (!silent) {
        loading.mcpSkills = true
      }
      errors.mcpSkills = null
      
      const params = {
        page: mcpPagination.current,
        page_size: mcpPagination.pageSize,
        search: mcpFilters.search || undefined,
        category: mcpFilters.category || undefined,
        status: mcpFilters.status || undefined,
        sort_by: mcpFilters.sortBy,
        sort_order: mcpFilters.sortOrder
      }
      
      const response = await templateAPI.getMCPSkills(params)
      
      if (response.success) {
        mcpSkills.value = response.data.skills || []
        mcpPagination.total = response.data.pagination?.total || 0
        
        // 提取分类
        extractMcpCategories()
        
        // 更新统计
        updateMcpStats()
        
        // 更新缓存
        cache.lastFetchSkills = Date.now()
        mcpSkills.value.forEach(skill => {
          cache.mcpSkills.set(skill.id, skill)
        })
        
        return mcpSkills.value
      } else {
        throw new Error(response.message || '获取MCP技能失败')
      }
    } catch (error) {
      console.error('获取MCP技能失败:', error)
      errors.mcpSkills = error.message
      if (!silent) {
        message.error('获取MCP技能失败')
      }
      return []
    } finally {
      if (!silent) {
        loading.mcpSkills = false
      }
    }
  }
  
  /**
   * 创建MCP技能
   * @param {Object} skillData 技能数据
   */
  const createMcpSkill = async (skillData) => {
    try {
      loading.creating = true
      errors.create = null
      
      const response = await templateAPI.createMCPSkill(skillData)
      
      if (response.success) {
        message.success('MCP技能创建成功')
        
        const newSkill = response.data
        mcpSkills.value.unshift(newSkill)
        
        // 更新分类和统计
        extractMcpCategories()
        updateMcpStats()
        
        // 更新缓存
        cache.mcpSkills.set(newSkill.id, newSkill)
        
        return newSkill
      } else {
        throw new Error(response.message || '创建MCP技能失败')
      }
    } catch (error) {
      console.error('创建MCP技能失败:', error)
      errors.create = error.message
      message.error('创建MCP技能失败')
      return null
    } finally {
      loading.creating = false
    }
  }
  
  /**
   * 更新MCP技能
   * @param {string} skillId 技能ID
   * @param {Object} updateData 更新数据
   */
  const updateMcpSkill = async (skillId, updateData) => {
    try {
      loading.updating = true
      errors.update = null
      
      const response = await templateAPI.updateMCPSkill(skillId, updateData)
      
      if (response.success) {
        message.success('MCP技能更新成功')
        
        const updatedSkill = response.data
        const index = mcpSkills.value.findIndex(s => s.id === skillId)
        if (index !== -1) {
          mcpSkills.value[index] = updatedSkill
        }
        
        // 更新分类和统计
        extractMcpCategories()
        updateMcpStats()
        
        // 更新缓存
        cache.mcpSkills.set(skillId, updatedSkill)
        
        return updatedSkill
      } else {
        throw new Error(response.message || '更新MCP技能失败')
      }
    } catch (error) {
      console.error('更新MCP技能失败:', error)
      errors.update = error.message
      message.error('更新MCP技能失败')
      return null
    } finally {
      loading.updating = false
    }
  }
  
  /**
   * 删除MCP技能
   * @param {string} skillId 技能ID
   */
  const deleteMcpSkill = async (skillId) => {
    try {
      loading.deleting = true
      errors.delete = null
      
      const response = await templateAPI.deleteMCPSkill(skillId)
      
      if (response.success) {
        message.success('MCP技能删除成功')
        
        mcpSkills.value = mcpSkills.value.filter(s => s.id !== skillId)
        
        // 更新分类和统计
        extractMcpCategories()
        updateMcpStats()
        
        // 清除缓存
        cache.mcpSkills.delete(skillId)
        
        return true
      } else {
        throw new Error(response.message || '删除MCP技能失败')
      }
    } catch (error) {
      console.error('删除MCP技能失败:', error)
      errors.delete = error.message
      message.error('删除MCP技能失败')
      return false
    } finally {
      loading.deleting = false
    }
  }
  
  /**
   * 测试MCP技能
   * @param {string} skillId 技能ID
   * @param {Object} testData 测试数据
   */
  const testMcpSkill = async (skillId, testData = {}) => {
    try {
      loading.testing = true
      errors.test = null
      
      const response = await templateAPI.testMCPSkill(skillId, testData)
      
      if (response.success) {
        message.success('MCP技能测试成功')
        return response.data
      } else {
        throw new Error(response.message || 'MCP技能测试失败')
      }
    } catch (error) {
      console.error('MCP技能测试失败:', error)
      errors.test = error.message
      message.error('MCP技能测试失败')
      return null
    } finally {
      loading.testing = false
    }
  }

  // ================================================================================
  // 辅助方法
  // ================================================================================
  
  /**
   * 提取提示词模板分类
   */
  const extractPromptCategories = () => {
    const categories = [...new Set(promptTemplates.value.map(t => t.category).filter(Boolean))]
    promptCategories.value = categories.sort()
  }
  
  /**
   * 提取MCP技能分类
   */
  const extractMcpCategories = () => {
    const categories = [...new Set(mcpSkills.value.map(s => s.category).filter(Boolean))]
    mcpCategories.value = categories.sort()
  }
  
  /**
   * 更新提示词模板统计
   */
  const updatePromptStats = () => {
    stats.promptTemplates.total = promptTemplates.value.length
    stats.promptTemplates.system = promptTemplates.value.filter(t => t.is_system).length
    stats.promptTemplates.user = promptTemplates.value.filter(t => !t.is_system).length
    stats.promptTemplates.categories = promptCategories.value.length
  }
  
  /**
   * 更新MCP技能统计
   */
  const updateMcpStats = () => {
    stats.mcpSkills.total = mcpSkills.value.length
    stats.mcpSkills.active = mcpSkills.value.filter(s => s.is_active === true).length
    stats.mcpSkills.inactive = mcpSkills.value.filter(s => s.is_active === false).length
    stats.mcpSkills.categories = mcpCategories.value.length
  }
  
  /**
   * 更新提示词模板筛选条件
   * @param {Object} newFilters 新的筛选条件
   */
  const updatePromptFilters = (newFilters) => {
    Object.assign(promptFilters, newFilters)
    promptPagination.current = 1
  }
  
  /**
   * 更新MCP技能筛选条件
   * @param {Object} newFilters 新的筛选条件
   */
  const updateMcpFilters = (newFilters) => {
    Object.assign(mcpFilters, newFilters)
    mcpPagination.current = 1
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
   * @param {string} type 缓存类型
   */
  const clearCache = (type = 'all') => {
    switch (type) {
      case 'prompts':
        cache.promptTemplates.clear()
        cache.lastFetchPrompts = null
        break
      case 'mcp':
        cache.mcpSkills.clear()
        cache.lastFetchSkills = null
        break
      case 'all':
      default:
        cache.promptTemplates.clear()
        cache.mcpSkills.clear()
        cache.lastFetchPrompts = null
        cache.lastFetchSkills = null
        break
    }
  }
  
  /**
   * 重置状态
   */
  const reset = () => {
    promptTemplates.value = []
    promptCategories.value = []
    mcpSkills.value = []
    mcpCategories.value = []
    
    Object.keys(loading).forEach(key => {
      loading[key] = false
    })
    
    clearErrors()
    clearCache()
    
    Object.assign(promptFilters, {
      search: '',
      category: '',
      is_system: null,
      sortBy: 'created_at',
      sortOrder: 'desc'
    })
    
    Object.assign(mcpFilters, {
      search: '',
      category: '',
      status: '',
      sortBy: 'created_at',
      sortOrder: 'desc'
    })
    
    Object.assign(promptPagination, {
      current: 1,
      pageSize: 20,
      total: 0
    })
    
    Object.assign(mcpPagination, {
      current: 1,
      pageSize: 20,
      total: 0
    })
    
    Object.assign(stats, {
      promptTemplates: {
        total: 0,
        system: 0,
        user: 0,
        categories: 0
      },
      mcpSkills: {
        total: 0,
        active: 0,
        inactive: 0,
        categories: 0
      }
    })
  }

  // ================================================================================
  // 返回状态和方法
  // ================================================================================
  
  return {
    // 状态
    promptTemplates,
    promptCategories,
    mcpSkills,
    mcpCategories,
    loading,
    errors,
    promptFilters,
    mcpFilters,
    promptPagination,
    mcpPagination,
    stats,
    
    // 计算属性
    filteredPromptTemplates,
    filteredMcpSkills,
    hasPromptFilters,
    hasMcpFilters,
    isPromptCacheValid,
    isMcpCacheValid,
    
    // 提示词模板方法
    fetchPromptTemplates,
    createPromptTemplate,
    updatePromptTemplate,
    deletePromptTemplate,
    
    // MCP技能方法
    fetchMcpSkills,
    createMcpSkill,
    updateMcpSkill,
    deleteMcpSkill,
    testMcpSkill,
    
    // 辅助方法
    updatePromptFilters,
    updateMcpFilters,
    clearErrors,
    clearCache,
    reset
  }
}) 