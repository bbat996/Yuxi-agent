<template>
  <div class="agent-selector">
    <!-- 简洁模式 - 用于AgentView.vue顶部 -->
    <div v-if="mode === 'compact'" class="compact-selector">
      <a-select
        v-model="selectedAgentId"
        class="agent-select"
        :style="{ width: width || '260px' }"
        placeholder="选择智能体"
        show-search
        option-filter-prop="label"
        @change="handleAgentChange"
        @dropdown-visible-change="handleDropdownVisible"
      >
        <!-- 系统智能体组 -->
        <a-select-opt-group label="系统智能体" v-if="systemAgents.length > 0">
          <a-select-option
            v-for="agent in systemAgents"
            :key="agent.agent_id"
            :value="agent.agent_id"
            :label="agent.name"
          >
            <div class="agent-option">
              <div class="agent-info">
                <span class="agent-name">{{ agent.name }}</span>
                <span class="agent-type">{{ agent.agent_type }}</span>
              </div>
              <div class="agent-status">
                <a-tag v-if="agent.is_active" color="green" size="small">运行中</a-tag>
              </div>
            </div>
          </a-select-option>
        </a-select-opt-group>

        <!-- 自定义智能体组 -->
        <a-select-opt-group label="自定义智能体" v-if="customAgents.length > 0">
          <a-select-option
            v-for="agent in customAgents"
            :key="agent.agent_id"
            :value="agent.agent_id"
            :label="agent.name"
          >
            <div class="agent-option">
              <div class="agent-info">
                <span class="agent-name">{{ agent.name }}</span>
                <span class="agent-type">{{ agent.agent_type }}</span>
              </div>
              <div class="agent-status">
                <a-tag v-if="agent.is_active" color="green" size="small">运行中</a-tag>
                <a-tag v-if="agent.is_mine" color="blue" size="small">我的</a-tag>
              </div>
            </div>
          </a-select-option>
        </a-select-opt-group>

        <!-- 空状态 -->
        <template v-if="allAgents.length === 0" #notFoundContent>
          <div class="empty-state">
            <robot-outlined class="empty-icon" />
            <p>暂无可用智能体</p>
            <a-button type="link" size="small" @click="$emit('create-agent')">
              创建智能体
            </a-button>
          </div>
        </template>
      </a-select>

      <!-- 快捷操作按钮 -->
      <div class="quick-actions" v-if="selectedAgent">
        <a-tooltip title="智能体配置">
          <a-button type="text" size="small" @click="$emit('open-config')">
            <setting-outlined />
          </a-button>
        </a-tooltip>
        


        <a-tooltip title="智能体详情">
          <a-button type="text" size="small" @click="$emit('view-details', selectedAgent)">
            <info-circle-outlined />
          </a-button>
        </a-tooltip>
      </div>
    </div>

    <!-- 详细模式 - 用于独立选择器页面 -->
    <div v-else-if="mode === 'detailed'" class="detailed-selector">
      <!-- 搜索和筛选栏 -->
      <div class="selector-header">
        <div class="search-section">
          <a-input-search
            v-model="searchQuery"
            placeholder="搜索智能体名称、描述..."
            style="width: 300px"
            @search="handleSearch"
          />
        </div>
        
        <div class="filter-section">
          <a-select
            v-model="typeFilter"
            placeholder="智能体类型"
            style="width: 120px"
            @change="handleFilter"
            allow-clear
          >
            <a-select-option value="custom">自定义</a-select-option>
            <a-select-option value="chatbot">聊天助手</a-select-option>
            <a-select-option value="react">ReAct智能体</a-select-option>
          </a-select>

          <a-select
            v-model="scopeFilter"
            placeholder="范围"
            style="width: 100px"
            @change="handleFilter"
            allow-clear
          >
            <a-select-option value="mine">我的</a-select-option>
            <a-select-option value="public">公开</a-select-option>
            <a-select-option value="system">系统</a-select-option>
          </a-select>

          <a-select
            v-model="sortBy"
            style="width: 120px"
            @change="handleSort"
          >
            <a-select-option value="created_at">创建时间</a-select-option>
            <a-select-option value="updated_at">更新时间</a-select-option>
            <a-select-option value="name">名称</a-select-option>
          </a-select>

          <a-button @click="toggleSortOrder">
            <swap-outlined :class="{ 'rotated': sortOrder === 'asc' }" />
          </a-button>
        </div>

        <div class="action-section">
          <a-button type="primary" @click="$emit('create-agent')">
            <plus-outlined />
            创建智能体
          </a-button>
        </div>
      </div>

      <!-- 智能体列表 -->
      <div class="agents-grid">
        <div
          v-for="agent in filteredAgents"
          :key="agent.agent_id"
          class="agent-card"
          :class="{ 
            'selected': selectedAgentId === agent.agent_id,
            'system': !agent.is_custom,
            'custom': agent.is_custom 
          }"
          @click="handleAgentSelect(agent)"
        >
          <div class="agent-card-header">
            <div class="agent-avatar">
              <img v-if="agent.avatar" :src="agent.avatar" :alt="agent.name" />
              <robot-outlined v-else />
            </div>
            <div class="agent-badges">
              <a-tag v-if="agent.is_active" color="green" size="small">运行中</a-tag>
              <a-tag v-if="agent.is_mine" color="blue" size="small">我的</a-tag>
            </div>
          </div>

          <div class="agent-card-body">
            <h4 class="agent-name">{{ agent.name }}</h4>
            <p class="agent-description">{{ agent.description || '暂无描述' }}</p>
            
            <div class="agent-meta">
              <span class="agent-type">{{ getAgentTypeLabel(agent.agent_type) }}</span>
              <span class="agent-time">{{ formatTime(agent.updated_at) }}</span>
            </div>
          </div>

          <div class="agent-card-actions">
            <a-button type="text" size="small" @click.stop="handleQuickEdit(agent)">
              <edit-outlined />
            </a-button>

            <a-dropdown trigger="click" @click="(e) => e.stopPropagation()">
              <a-button type="text" size="small">
                <more-outlined />
              </a-button>
              <template #overlay>
                <a-menu>
                  <a-menu-item @click="$emit('duplicate-agent', agent)">
                    <copy-outlined />
                    复制
                  </a-menu-item>
                  <a-menu-item @click="$emit('export-agent', agent)">
                    <export-outlined />
                    导出
                  </a-menu-item>
                  <a-menu-divider v-if="agent.is_mine" />
                  <a-menu-item v-if="agent.is_mine" @click="handleDelete(agent)" danger>
                    <delete-outlined />
                    删除
                  </a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-if="filteredAgents.length === 0" class="empty-grid">
          <a-empty description="没有找到匹配的智能体">
            <a-button type="primary" @click="$emit('create-agent')">
              创建智能体
            </a-button>
          </a-empty>
        </div>
      </div>

      <!-- 分页 -->
      <div class="pagination-section" v-if="pagination.total > pagination.pageSize">
        <a-pagination
          :current="pagination.current"
          :page-size="pagination.pageSize"
          :total="pagination.total"
          :show-size-changer="true"
          :show-quick-jumper="true"
          :show-total="(total, range) => `第 ${range[0]}-${range[1]} 项，共 ${total} 项`"
          @change="handlePageChange"
          @show-size-change="handlePageSizeChange"
        />
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <a-spin size="large" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { message, Modal } from 'ant-design-vue'
import {
  RobotOutlined,
  SettingOutlined,
  InfoCircleOutlined,
  PlusOutlined,
  SwapOutlined,
  EditOutlined,
  MoreOutlined,
  CopyOutlined,
  ExportOutlined,
  DeleteOutlined
} from '@ant-design/icons-vue'
import { useAgentStore } from '@/stores/agent'
import { useUserStore } from '@/stores/user'

// ================================================================================
// Props 和 Emits
// ================================================================================

const props = defineProps({
  // 选择器模式: 'compact' | 'detailed'
  mode: {
    type: String,
    default: 'compact'
  },
  // 当前选中的智能体ID
  modelValue: {
    type: String,
    default: ''
  },

  // 组件宽度（仅compact模式）
  width: {
    type: String,
    default: '260px'
  },
  // 是否显示创建按钮
  showCreateButton: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits([
  'update:modelValue',
  'change',
  'create-agent',
  'open-config',
  'view-details',
  'edit-agent',
  'duplicate-agent',
  'export-agent',
  'delete-agent',

])

// ================================================================================
// Store 和响应式数据
// ================================================================================

const agentStore = useAgentStore()
const userStore = useUserStore()

// 本地状态
const selectedAgentId = ref(props.modelValue)
const searchQuery = ref('')
const typeFilter = ref('')
const scopeFilter = ref('')
const sortBy = ref('updated_at')
const sortOrder = ref('desc')

// 计算属性
const loading = computed(() => agentStore.loading.agents)
const allAgents = computed(() => agentStore.agents)
const customAgents = computed(() => agentStore.customAgents)
const systemAgents = computed(() => agentStore.systemAgents)
const filteredAgents = computed(() => agentStore.filteredAgents)
const pagination = computed(() => agentStore.pagination)

const selectedAgent = computed(() => {
  return allAgents.value.find(agent => agent.agent_id === selectedAgentId.value)
})

// ================================================================================
// 方法
// ================================================================================

/**
 * 获取智能体类型标签
 */
const getAgentTypeLabel = (type) => {
  const typeMap = {
    'custom': '自定义',
    'chatbot': '聊天助手',
    'react': 'ReAct智能体'
  }
  return typeMap[type] || type
}

/**
 * 格式化时间
 */
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`
  
  return date.toLocaleDateString()
}

/**
 * 处理智能体改变
 */
const handleAgentChange = (agentId) => {
  selectedAgentId.value = agentId
  const agent = allAgents.value.find(a => a.agent_id === agentId)
  agentStore.setCurrentAgent(agent)
  
  emit('update:modelValue', agentId)
  emit('change', agent)
}

/**
 * 处理智能体选择（详细模式）
 */
const handleAgentSelect = (agent) => {
  handleAgentChange(agent.agent_id)
}

/**
 * 处理下拉框显示状态改变
 */
const handleDropdownVisible = (visible) => {
  if (visible && allAgents.value.length === 0) {
    fetchAgents()
  }
}

/**
 * 处理搜索
 */
const handleSearch = () => {
  agentStore.updateFilters({ search: searchQuery.value })
  fetchAgents()
}

/**
 * 处理筛选
 */
const handleFilter = () => {
  agentStore.updateFilters({
    type: typeFilter.value,
    scope: scopeFilter.value
  })
  fetchAgents()
}

/**
 * 处理排序
 */
const handleSort = () => {
  agentStore.updateFilters({
    sortBy: sortBy.value,
    sortOrder: sortOrder.value
  })
  fetchAgents()
}

/**
 * 切换排序顺序
 */
const toggleSortOrder = () => {
  sortOrder.value = sortOrder.value === 'desc' ? 'asc' : 'desc'
  handleSort()
}

/**
 * 处理分页改变
 */
const handlePageChange = (page, pageSize) => {
  agentStore.updatePagination({ current: page, pageSize })
  fetchAgents()
}

/**
 * 处理页面大小改变
 */
const handlePageSizeChange = (current, size) => {
  agentStore.updatePagination({ current: 1, pageSize: size })
  fetchAgents()
}



/**
 * 快速编辑
 */
const handleQuickEdit = (agent) => {
  emit('edit-agent', agent)
}

/**
 * 删除智能体
 */
const handleDelete = (agent) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除智能体 "${agent.name}" 吗？此操作不可恢复。`,
    okText: '确认删除',
    okType: 'danger',
    cancelText: '取消',
    onOk: () => {
      emit('delete-agent', agent)
    }
  })
}

/**
 * 获取智能体列表
 */
const fetchAgents = async (options = {}) => {
  try {
    await agentStore.fetchAgents(options)
  } catch (error) {
    console.error('获取智能体列表失败:', error)
  }
}

/**
 * 刷新智能体列表
 */
const refresh = () => {
  fetchAgents({ forceRefresh: true })
}

// ================================================================================
// 生命周期和监听
// ================================================================================

// 监听外部传入的值变化
watch(() => props.modelValue, (newValue) => {
  selectedAgentId.value = newValue
}, { immediate: true })

// 监听选中智能体变化
watch(selectedAgentId, (newId, oldId) => {
  if (newId !== oldId) {
    const agent = allAgents.value.find(a => a.agent_id === newId)
    if (agent) {
      agentStore.setCurrentAgent(agent)
    }
  }
})

// 组件挂载时获取数据
onMounted(() => {
  fetchAgents()
})

// 暴露方法给父组件
defineExpose({
  refresh,
  fetchAgents
})
</script>

<style scoped>
.agent-selector {
  width: 100%;
}

/* ================ 紧凑模式样式 ================ */
.compact-selector {
  display: flex;
  align-items: center;
  gap: 8px;
}

.agent-select {
  flex: 1;
}

.agent-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
}

.agent-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.agent-name {
  font-weight: 500;
  font-size: 14px;
}

.agent-type {
  font-size: 12px;
  color: #666;
}

.agent-status {
  display: flex;
  gap: 4px;
}

.quick-actions {
  display: flex;
  gap: 4px;
}

.empty-state {
  text-align: center;
  padding: 20px;
  color: #999;
}

.empty-icon {
  font-size: 24px;
  color: #d9d9d9;
  margin-bottom: 8px;
}

/* ================ 详细模式样式 ================ */
.detailed-selector {
  width: 100%;
}

.selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  gap: 16px;
}

.search-section {
  flex: 1;
}

.filter-section {
  display: flex;
  gap: 8px;
  align-items: center;
}

.action-section {
  flex-shrink: 0;
}

.rotated {
  transform: rotate(180deg);
  transition: transform 0.3s;
}

/* 智能体网格 */
.agents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.agent-card {
  border: 1px solid #d9d9d9;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s;
  background: #fff;
}

.agent-card:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.agent-card.selected {
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.agent-card.system {
  border-left: 4px solid #52c41a;
}

.agent-card.custom {
  border-left: 4px solid #1890ff;
}

.agent-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.agent-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: #999;
}

.agent-avatar img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.agent-badges {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.agent-card-body {
  margin-bottom: 12px;
}

.agent-name {
  font-size: 16px;
  font-weight: 500;
  margin: 0 0 4px 0;
  color: #333;
}

.agent-description {
  font-size: 14px;
  color: #666;
  margin: 0 0 8px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.agent-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #999;
}

.agent-card-actions {
  display: flex;
  justify-content: flex-end;
  gap: 4px;
  border-top: 1px solid #f0f0f0;
  padding-top: 8px;
}

.empty-grid {
  grid-column: 1 / -1;
  text-align: center;
  padding: 40px;
}

/* 分页 */
.pagination-section {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

/* 加载状态 */
.loading-state {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .selector-header {
    flex-direction: column;
    gap: 12px;
  }
  
  .filter-section {
    flex-wrap: wrap;
  }
  
  .agents-grid {
    grid-template-columns: 1fr;
  }
}
</style> 