<template>
  <a-modal
    :visible="modalVisible"
    title="智能体详情"
    width="900px"
    :footer="null"
    :destroy-on-close="true"
    @update:visible="emit('update:visible', $event)"
  >
    <div class="agent-detail" v-if="agent">
      <!-- 基础信息 -->
      <div class="detail-section">
        <div class="section-header">
          <div class="agent-avatar">
            <a-avatar :size="60" :src="agent.avatar || undefined">
              <template #icon v-if="!agent.avatar">
                <RobotOutlined />
              </template>
            </a-avatar>
          </div>
          <div class="agent-basic-info">
            <h2 class="agent-name">{{ agent.name }}</h2>
            <div class="agent-meta">
              <a-tag :color="getTypeColor(agent.agent_type)">
                {{ getTypeLabel(agent.agent_type) }}
              </a-tag>
              <span class="create-date">
                创建于 {{ formatDate(agent.created_at) }}
              </span>
            </div>
            <p class="agent-description">{{ agent.description || '暂无描述' }}</p>
          </div>
          <div class="agent-actions">
            <a-button type="primary" @click="$emit('chat', agent)">
              <template #icon><MessageOutlined /></template>
              开始聊天
            </a-button>
            <a-button @click="showEditModal = true">
              <template #icon><EditOutlined /></template>
              编辑信息
            </a-button>
          </div>
        </div>
      </div>

      <!-- 详细配置 -->
      <a-tabs default-active-key="prompt" class="detail-tabs">
        <!-- 系统提示词 -->
        <a-tab-pane key="prompt" tab="系统提示词">
          <div class="tab-content">
            <div class="prompt-display">
              <pre class="prompt-text">{{ agent.system_prompt || '未设置系统提示词' }}</pre>
            </div>
          </div>
        </a-tab-pane>

        <!-- 模型配置 -->
        <a-tab-pane key="model" tab="模型配置">
          <div class="tab-content">
            <a-descriptions :column="2" bordered>
              <a-descriptions-item label="提供商">
                {{ agent.llm_config?.provider || '未配置' }}
              </a-descriptions-item>
              <a-descriptions-item label="模型">
                {{ agent.llm_config?.model || '未配置' }}
              </a-descriptions-item>
              <a-descriptions-item label="温度">
                <div class="config-value">
                  {{ agent.llm_config?.config?.temperature || 0.7 }}
                  <a-tag size="small" color="blue">
                    {{ getTemperatureLabel(agent.llm_config?.config?.temperature || 0.7) }}
                  </a-tag>
                </div>
              </a-descriptions-item>
              <a-descriptions-item label="最大回复长度">
                {{ agent.llm_config?.config?.max_tokens || '未设置' }}
              </a-descriptions-item>
              <a-descriptions-item label="Top P">
                {{ agent.llm_config?.config?.top_p || 0.9 }}
              </a-descriptions-item>
              <a-descriptions-item label="频率惩罚">
                {{ agent.llm_config?.config?.frequency_penalty || 0 }}
              </a-descriptions-item>
              <a-descriptions-item label="存在惩罚">
                {{ agent.llm_config?.config?.presence_penalty || 0 }}
              </a-descriptions-item>
            </a-descriptions>
          </div>
        </a-tab-pane>

        <!-- 工具配置 -->
        <a-tab-pane key="tools" tab="工具配置">
          <div class="tab-content">
            <div class="tools-grid" v-if="agent.tools?.length">
              <div 
                v-for="tool in agent.tools" 
                :key="tool"
                class="tool-card"
              >
                <div class="tool-header">
                  <div class="tool-icon">
                    <component :is="getToolIcon(tool)" />
                  </div>
                  <div class="tool-info">
                    <h4 class="tool-name">{{ tool }}</h4>
                  </div>
                </div>
              </div>
            </div>
            <a-empty v-else description="未配置工具" />
          </div>
        </a-tab-pane>

        <!-- 知识库配置 -->
        <a-tab-pane key="knowledge" tab="知识库">
          <div class="tab-content">
            <div class="knowledge-config" v-if="agent.knowledge_config?.enabled">
              <a-switch
                :model-value="agent.knowledge_config.enabled"
                disabled
                class="mb-4"
              />
              <div class="knowledge-list" v-if="agent.knowledge_config.databases?.length">
                <h4>关联知识库:</h4>
                <div class="knowledge-grid">
                  <div 
                    v-for="dbId in agent.knowledge_config.databases" 
                    :key="dbId"
                    class="knowledge-item"
                  >
                    <DatabaseOutlined class="knowledge-icon" />
                    <span class="knowledge-name">知识库 {{ dbId }}</span>
                  </div>
                </div>
              </div>
              
              <a-divider />
              
              <div class="retrieval-config">
                <h4>检索配置:</h4>
                <a-descriptions :column="2" size="small">
                  <a-descriptions-item label="检索数量">
                    {{ agent.knowledge_config.retrieval_config?.top_k || 3 }}
                  </a-descriptions-item>
                  <a-descriptions-item label="相似度阈值">
                    {{ agent.knowledge_config.retrieval_config?.similarity_threshold || 0.5 }}
                  </a-descriptions-item>
                </a-descriptions>
              </div>
            </div>
            <a-empty v-else description="未启用知识库" />
          </div>
        </a-tab-pane>

        <!-- MCP技能 -->
        <a-tab-pane key="mcp" tab="MCP技能">
          <div class="tab-content">
            <div class="mcp-config" v-if="agent.mcp_config?.enabled">
              <a-switch
                :model-value="agent.mcp_config.enabled"
                disabled
                class="mb-4"
              />
              <div class="mcp-servers" v-if="agent.mcp_config.servers?.length">
                <h4>MCP服务器:</h4>
                <div class="server-grid">
                  <div 
                    v-for="server in agent.mcp_config.servers" 
                    :key="server"
                    class="server-item"
                  >
                    <ApiOutlined class="server-icon" />
                    <span class="server-name">{{ server }}</span>
                  </div>
                </div>
              </div>
            </div>
            <a-empty v-else description="未启用MCP服务" />
          </div>
        </a-tab-pane>

        <!-- 使用统计 -->
        <a-tab-pane key="stats" tab="使用统计">
          <div class="tab-content">
            <a-row :gutter="16" class="stats-row">
              <a-col :span="6">
                <a-statistic title="总对话次数" :value="stats.total_chats || 0" />
              </a-col>
              <a-col :span="6">
                <a-statistic title="总消息数" :value="stats.total_messages || 0" />
              </a-col>
              <a-col :span="6">
                <a-statistic title="平均回复时间" :value="stats.avg_response_time || 0" suffix="ms" />
              </a-col>
              <a-col :span="6">
                <a-statistic title="最后使用" :value="formatDate(stats.last_used)" />
              </a-col>
            </a-row>

            <a-divider />

            <!-- 使用趋势图表区域 -->
            <div class="charts-container">
              <h4>使用趋势</h4>
              <div class="chart-placeholder">
                <a-empty description="统计图表开发中..." />
              </div>
            </div>
          </div>
        </a-tab-pane>
      </a-tabs>
    </div>

    <!-- 加载状态 -->
    <div class="loading-container" v-else>
      <a-spin size="large">
        <template #tip>加载智能体详情中...</template>
      </a-spin>
    </div>
  </a-modal>

  <!-- 编辑智能体模态框 -->
  <AgentModal
    v-model:visible="showEditModal"
    :agent="agent"
    mode="edit"
    @success="handleEditSuccess"
  />
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  RobotOutlined,
  MessageOutlined,
  EditOutlined,
  DatabaseOutlined,
  ApiOutlined,
  ToolOutlined,
  SearchOutlined,
  CalculatorOutlined,
  CodeOutlined
} from '@ant-design/icons-vue'
import { agentAPI } from '@/apis'
import AgentModal from './AgentModal.vue'

// Props
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  agentId: {
    type: String,
    required: true
  }
})

// Emits
const emit = defineEmits(['update:visible', 'edit', 'chat'])

// 响应式数据
const modalVisible = ref(false)
const agent = ref(null)
const stats = ref({})
const loading = ref(false)
const showEditModal = ref(false)

// 监听 visible 变化
watch(() => props.visible, (newVal) => {
  modalVisible.value = newVal
  if (newVal && props.agentId) {
    loadAgentDetail()
  }
})

watch(modalVisible, (newVal) => {
  emit('update:visible', newVal)
  if (!newVal) {
    agent.value = null
    stats.value = {}
  }
})

// 加载智能体详情
const loadAgentDetail = async () => {
  try {
    loading.value = true
    
    // 并行加载智能体详情和统计信息
    const [agentResponse, statsResponse] = await Promise.all([
      agentAPI.getAgent(props.agentId),
      agentAPI.getAgentStats(props.agentId).catch(() => ({ data: {} })) // 统计可选
    ])

    if (agentResponse.success) {
      agent.value = agentResponse.data
    } else {
      message.error('加载智能体详情失败')
      modalVisible.value = false
      return
    }

    if (statsResponse.success) {
      stats.value = statsResponse.data
    }
  } catch (error) {
    console.error('加载智能体详情失败:', error)
    message.error('加载智能体详情失败')
    modalVisible.value = false
  } finally {
    loading.value = false
  }
}

// 处理编辑成功
const handleEditSuccess = () => {
  // 重新加载智能体详情
  loadAgentDetail()
  message.success('智能体更新成功')
}

// 获取类型颜色
const getTypeColor = (type) => {
  const colors = {
    'custom': 'blue',
    'chatbot': 'green',
    'react': 'orange',
    'default': 'default'
  }
  return colors[type] || colors.default
}

// 获取类型标签
const getTypeLabel = (type) => {
  const labels = {
    'custom': '自定义',
    'chatbot': '聊天助手',
    'react': 'ReAct',
    'default': '未知'
  }
  return labels[type] || labels.default
}

// 获取温度标签
const getTemperatureLabel = (temp) => {
  if (temp <= 0.3) return '保守'
  if (temp <= 0.7) return '平衡'
  if (temp <= 1.2) return '创造'
  return '发散'
}

// 获取工具图标
const getToolIcon = (toolType) => {
  const icons = {
    'web_search': SearchOutlined,
    'calculator': CalculatorOutlined,
    'code_executor': CodeOutlined,
    'default': ToolOutlined
  }
  return icons[toolType] || icons.default
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '未知'
  
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}
</script>

<style scoped>
.agent-detail {
  max-height: 80vh;
  overflow-y: auto;
}

.detail-section {
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  border-radius: 12px;
  margin-bottom: 24px;
}

.agent-avatar {
  flex-shrink: 0;
}

.agent-basic-info {
  flex: 1;
  min-width: 0;
}

.agent-name {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
}

.agent-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.create-date {
  color: #666;
  font-size: 14px;
}

.agent-description {
  margin: 0;
  color: #666;
  line-height: 1.6;
}

.agent-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-tabs {
  background: white;
  border-radius: 8px;
}

.tab-content {
  padding: 16px 0;
}

.prompt-display {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #e9ecef;
}

.prompt-text {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
  line-height: 1.6;
  color: #333;
}

.config-value {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.tool-card {
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 16px;
  background: white;
}

.tool-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.tool-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f0f0;
  border-radius: 6px;
  color: #666;
}

.tool-info {
  flex: 1;
}

.tool-name {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 500;
}

.tool-type {
  font-size: 12px;
  color: #999;
}

.tool-description {
  margin: 0 0 12px 0;
  color: #666;
  line-height: 1.5;
}

.tool-params h5 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #333;
}

.params-json {
  background: #f8f9fa;
  border-radius: 4px;
  padding: 8px;
  font-size: 12px;
  color: #666;
  margin: 0;
  max-height: 150px;
  overflow-y: auto;
}

.knowledge-config {
  padding: 16px;
}

.knowledge-list h4,
.retrieval-config h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #333;
}

.knowledge-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.knowledge-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  background: white;
}

.knowledge-icon {
  color: #1890ff;
}

.knowledge-name {
  font-weight: 500;
}

.mcp-skills {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.skill-card {
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 16px;
  background: white;
}

.skill-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.skill-icon {
  color: #52c41a;
  font-size: 18px;
}

.skill-info {
  flex: 1;
}

.skill-name {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 500;
}

.skill-type {
  font-size: 12px;
  color: #999;
}

.skill-description {
  margin: 0 0 12px 0;
  color: #666;
  line-height: 1.5;
}

.skill-config h5 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #333;
}

.config-json {
  background: #f8f9fa;
  border-radius: 4px;
  padding: 8px;
  font-size: 12px;
  color: #666;
  margin: 0;
  max-height: 150px;
  overflow-y: auto;
}

.stats-row {
  margin-bottom: 24px;
}

.charts-container h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #333;
}

.chart-placeholder {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed #d9d9d9;
  border-radius: 8px;
  background: #fafafa;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .section-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  
  .agent-actions {
    flex-direction: row;
    justify-content: center;
  }
  
  .tools-grid {
    grid-template-columns: 1fr;
  }
  
  .knowledge-grid {
    grid-template-columns: 1fr;
  }
}
</style> 