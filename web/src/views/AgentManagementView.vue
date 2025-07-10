<template>
  <div class="agent-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h2>智能体管理</h2>
        <p>创建、编辑和管理您的自定义智能体</p>
      </div>
      <div class="header-actions">
        <a-button type="primary" @click="showCreateModal">
          <template #icon><PlusOutlined /></template>
          创建智能体
        </a-button>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-filters">
      <a-row :gutter="16">
        <a-col :span="8">
          <a-input-search
            v-model:value="searchQuery"
            placeholder="搜索智能体名称或描述"
            @search="handleSearch"
            @change="handleSearch"
          />
        </a-col>
        <a-col :span="4">
          <a-select
            v-model:value="filterType"
            placeholder="类型筛选"
            @change="handleSearch"
            style="width: 100%"
          >
            <a-select-option value="">全部类型</a-select-option>
            <a-select-option value="custom">自定义</a-select-option>
            <a-select-option value="chatbot">聊天助手</a-select-option>
            <a-select-option value="react">ReAct</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select
            v-model:value="filterScope"
            placeholder="范围筛选"
            @change="handleSearch"
            style="width: 100%"
          >
            <a-select-option value="">全部</a-select-option>
            <a-select-option value="mine">我的智能体</a-select-option>
            <a-select-option value="public">公开智能体</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select
            v-model:value="sortBy"
            placeholder="排序方式"
            @change="handleSearch"
            style="width: 100%"
          >
            <a-select-option value="created_at">创建时间</a-select-option>
            <a-select-option value="updated_at">更新时间</a-select-option>
            <a-select-option value="name">名称</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-button @click="refreshList" :loading="loading">
            <template #icon><ReloadOutlined /></template>
            刷新
          </a-button>
        </a-col>
      </a-row>
    </div>

    <!-- 智能体列表 -->
    <div class="agent-list">
      <a-spin :spinning="loading">
        <a-row :gutter="[16, 16]">
          <a-col v-for="agent in agents" :key="agent.agent_id" :span="8">
            <AgentCard
              :agent="agent"
              @edit="handleEdit"
              @delete="handleDelete"
              @duplicate="handleDuplicate"
              @view="handleView"
              @toggle-favorite="handleToggleFavorite"
            />
          </a-col>
        </a-row>
      </a-spin>

      <!-- 空状态 -->
      <a-empty v-if="!loading && agents.length === 0" class="empty-state">
        <template #description>
          <span v-if="hasFilters">没有找到符合条件的智能体</span>
          <span v-else>还没有智能体，快来创建第一个吧！</span>
        </template>
        <a-button v-if="!hasFilters" type="primary" @click="showCreateModal">
          创建智能体
        </a-button>
      </a-empty>
    </div>

    <!-- 分页 -->
    <div class="pagination" v-if="pagination.total > 0">
      <a-pagination
        v-model:current="pagination.current"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :show-size-changer="true"
        :show-quick-jumper="true"
        :show-total="(total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`"
        @change="handlePageChange"
        @show-size-change="handlePageSizeChange"
      />
    </div>

    <!-- 创建/编辑智能体模态框 -->
    <AgentModal
      v-model:visible="modalVisible"
      :agent="currentAgent"
      :mode="modalMode"
      @success="handleModalSuccess"
    />

    <!-- 智能体详情模态框 -->
    <AgentDetailModal
      v-model:visible="detailModalVisible"
      :agent-id="selectedAgentId"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons-vue'
import { agentAPI } from '@/apis/agent_api'
import AgentCard from '@/components/AgentCard.vue'
import AgentModal from '@/components/AgentModal.vue'
import AgentDetailModal from '@/components/AgentDetailModal.vue'

// 响应式数据
const loading = ref(false)
const agents = ref([])
const searchQuery = ref('')
const filterType = ref('')
const filterScope = ref('')
const sortBy = ref('created_at')
const sortOrder = ref('desc')

// 分页
const pagination = reactive({
  current: 1,
  pageSize: 12,
  total: 0
})

// 模态框
const modalVisible = ref(false)
const modalMode = ref('create') // 'create' | 'edit'
const currentAgent = ref(null)

const detailModalVisible = ref(false)
const selectedAgentId = ref('')

// 计算属性
const hasFilters = computed(() => {
  return searchQuery.value || filterType.value || filterScope.value
})

// 获取智能体列表
const fetchAgents = async () => {
  try {
    loading.value = true
    
    const params = {
      page: pagination.current,
      page_size: pagination.pageSize,
      search: searchQuery.value || undefined,
      agent_type: filterType.value || undefined,
      only_mine: filterScope.value === 'mine' || undefined,
      only_public: filterScope.value === 'public' || undefined,
      sort_by: sortBy.value,
      sort_order: sortOrder.value
    }

    const response = await agentAPI.getAgents(params)
    
    if (response.success) {
      agents.value = response.data.agents
      pagination.total = response.data.pagination.total
    } else {
      message.error('获取智能体列表失败')
    }
  } catch (error) {
    console.error('获取智能体列表失败:', error)
    message.error('获取智能体列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索处理
const handleSearch = () => {
  pagination.current = 1
  fetchAgents()
}

// 分页处理
const handlePageChange = (page, pageSize) => {
  pagination.current = page
  pagination.pageSize = pageSize
  fetchAgents()
}

const handlePageSizeChange = (current, size) => {
  pagination.current = 1
  pagination.pageSize = size
  fetchAgents()
}

// 刷新列表
const refreshList = () => {
  fetchAgents()
}

// 显示创建模态框
const showCreateModal = () => {
  currentAgent.value = null
  modalMode.value = 'create'
  modalVisible.value = true
}

// 编辑智能体
const handleEdit = (agent) => {
  currentAgent.value = agent
  modalMode.value = 'edit'
  modalVisible.value = true
}

// 删除智能体
const handleDelete = (agent) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除智能体"${agent.name}"吗？此操作无法撤销。`,
    okText: '删除',
    okType: 'danger',
    cancelText: '取消',
    async onOk() {
      try {
        const response = await agentAPI.deleteAgent(agent.agent_id)
        if (response.success) {
          message.success('智能体删除成功')
          fetchAgents()
        } else {
          message.error('删除失败')
        }
      } catch (error) {
        console.error('删除智能体失败:', error)
        message.error('删除失败')
      }
    }
  })
}

// 复制智能体
const handleDuplicate = async (agent) => {
  try {
    const newName = `${agent.name} - 副本`
    const response = await agentAPI.duplicateAgent(agent.agent_id, { new_name: newName })
    
    if (response.success) {
      message.success('智能体复制成功')
      fetchAgents()
    } else {
      message.error('复制失败')
    }
  } catch (error) {
    console.error('复制智能体失败:', error)
    message.error('复制失败')
  }
}

// 查看智能体详情
const handleView = (agent) => {
  selectedAgentId.value = agent.agent_id
  detailModalVisible.value = true
}

// 切换收藏状态
const handleToggleFavorite = async (agent) => {
  try {
    // 这里需要实现收藏功能的API
    // const response = await agentAPI.toggleFavorite(agent.agent_id)
    message.info('收藏功能开发中...')
  } catch (error) {
    console.error('切换收藏失败:', error)
    message.error('操作失败')
  }
}

// 模态框成功回调
const handleModalSuccess = () => {
  modalVisible.value = false
  fetchAgents()
}

// 监听搜索变化
watch([searchQuery], () => {
  // 防抖处理
  clearTimeout(window.searchTimer)
  window.searchTimer = setTimeout(() => {
    handleSearch()
  }, 500)
})

// 组件挂载
onMounted(() => {
  fetchAgents()
})
</script>

<style scoped>
.agent-management {
  padding: 24px;
  background: #f5f5f5;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 24px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-content h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
}

.header-content p {
  margin: 4px 0 0 0;
  color: #666;
  font-size: 14px;
}

.search-filters {
  margin-bottom: 24px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.agent-list {
  min-height: 400px;
}

.empty-state {
  padding: 80px 0;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 32px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .agent-list :deep(.ant-col) {
    flex: 0 0 50%;
    max-width: 50%;
  }
}

@media (max-width: 768px) {
  .agent-management {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .search-filters .ant-row {
    flex-direction: column;
  }
  
  .search-filters .ant-col {
    margin-bottom: 12px;
  }
  
  .agent-list :deep(.ant-col) {
    flex: 0 0 100%;
    max-width: 100%;
  }
}
</style> 