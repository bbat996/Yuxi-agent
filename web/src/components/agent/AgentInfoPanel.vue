<template>
  <div class="agent-info-panel" :class="{ 'collapsed': collapsed }">
    <!-- 展开/收起按钮 -->
    <div class="panel-toggle" @click="togglePanel">
      <info-circle-outlined v-if="collapsed" />
      <close-outlined v-else />
    </div>

    <!-- 智能体基本信息 -->
    <div class="agent-basic-info" v-if="!collapsed && agent">
      <div class="agent-header">
        <div class="agent-avatar">
          <img v-if="agent.avatar" :src="agent.avatar" :alt="agent.name" />
          <robot-outlined v-else />
        </div>
        <div class="agent-title">
          <h3 class="agent-name">{{ agent.name }}</h3>
          <div class="agent-badges">
            <a-tag v-if="agent.is_default" color="gold" size="small">
              <star-filled />
              默认
            </a-tag>
            <a-tag v-if="agent.is_active" color="green" size="small">运行中</a-tag>
            <a-tag :color="getTypeColor(agent.agent_type)" size="small">
              {{ getAgentTypeLabel(agent.agent_type) }}
            </a-tag>
          </div>
        </div>
      </div>

      <p class="agent-description" v-if="agent.description">
        {{ agent.description }}
      </p>

      <!-- 智能体配置信息 -->
      <div class="config-section" v-if="config && Object.keys(config).length > 0">
        <div class="section-header" @click="toggleConfigSection">
          <h4>当前配置</h4>
          <down-outlined :class="{ 'rotated': !configCollapsed }" />
        </div>
        <div class="config-content" v-if="!configCollapsed">
          <div class="config-item" v-if="config.model">
            <span class="config-label">模型:</span>
            <span class="config-value">{{ config.model }}</span>
          </div>
          <div class="config-item" v-if="config.system_prompt">
            <span class="config-label">系统提示:</span>
            <div class="config-value prompt-value">
              <a-tooltip :title="config.system_prompt">
                <span class="prompt-preview">{{ getPromptPreview(config.system_prompt) }}</span>
              </a-tooltip>
            </div>
          </div>
          <div class="config-item" v-if="config.tools && config.tools.length > 0">
            <span class="config-label">工具:</span>
            <div class="config-value">
              <a-tag 
                v-for="tool in config.tools" 
                :key="tool" 
                size="small" 
                class="tool-tag"
              >
                {{ tool }}
              </a-tag>
            </div>
          </div>
        </div>
      </div>

      <!-- MCP技能调用日志 -->
      <div class="mcp-logs-section" v-if="mcpLogs.length > 0">
        <div class="section-header" @click="toggleMcpSection">
          <h4>MCP调用日志</h4>
          <a-badge :count="mcpLogs.length" :offset="[10, 0]">
            <down-outlined :class="{ 'rotated': !mcpCollapsed }" />
          </a-badge>
        </div>
        <div class="mcp-content" v-if="!mcpCollapsed">
          <div class="mcp-logs">
            <div 
              v-for="(log, index) in mcpLogs.slice(-5)" 
              :key="index"
              class="mcp-log-item"
              :class="{ 
                'success': log.status === 'success',
                'error': log.status === 'error',
                'pending': log.status === 'pending'
              }"
            >
              <div class="log-header">
                <span class="skill-name">{{ log.skillName }}</span>
                <span class="log-time">{{ formatTime(log.timestamp) }}</span>
              </div>
              <div class="log-details">
                <div class="log-input" v-if="log.input">
                  <small>输入: {{ JSON.stringify(log.input) }}</small>
                </div>
                <div class="log-output" v-if="log.output">
                  <small>输出: {{ JSON.stringify(log.output) }}</small>
                </div>
                <div class="log-error" v-if="log.error">
                  <small class="error-text">错误: {{ log.error }}</small>
                </div>
              </div>
            </div>
          </div>
          <div class="mcp-actions" v-if="mcpLogs.length > 5">
            <a-button type="link" size="small" @click="showAllMcpLogs">
              查看全部 ({{ mcpLogs.length }})
            </a-button>
          </div>
        </div>
      </div>

      <!-- 会话统计 -->
      <div class="stats-section" v-if="stats">
        <div class="section-header" @click="toggleStatsSection">
          <h4>会话统计</h4>
          <down-outlined :class="{ 'rotated': !statsCollapsed }" />
        </div>
        <div class="stats-content" v-if="!statsCollapsed">
          <div class="stats-grid">
            <div class="stat-item">
              <span class="stat-value">{{ stats.messageCount || 0 }}</span>
              <span class="stat-label">消息数</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ stats.tokenCount || 0 }}</span>
              <span class="stat-label">Token数</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ stats.toolCalls || 0 }}</span>
              <span class="stat-label">工具调用</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ formatDuration(stats.duration || 0) }}</span>
              <span class="stat-label">对话时长</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div class="empty-state" v-if="!collapsed && !agent">
      <robot-outlined class="empty-icon" />
      <p>未选择智能体</p>
    </div>

    <!-- MCP日志详情模态框 -->
    <a-modal
      v-model:open="mcpModalVisible"
      title="MCP调用日志详情"
      :width="800"
      :footer="null"
    >
      <div class="mcp-logs-detail">
        <div 
          v-for="(log, index) in mcpLogs" 
          :key="index"
          class="mcp-log-detail"
          :class="{ 
            'success': log.status === 'success',
            'error': log.status === 'error',
            'pending': log.status === 'pending'
          }"
        >
          <div class="log-detail-header">
            <h4>{{ log.skillName }}</h4>
            <span class="log-status">{{ getStatusLabel(log.status) }}</span>
            <span class="log-timestamp">{{ formatFullTime(log.timestamp) }}</span>
          </div>
          <div class="log-detail-content">
            <div class="log-section" v-if="log.input">
              <h5>输入参数:</h5>
              <pre class="log-json">{{ JSON.stringify(log.input, null, 2) }}</pre>
            </div>
            <div class="log-section" v-if="log.output">
              <h5>输出结果:</h5>
              <pre class="log-json">{{ JSON.stringify(log.output, null, 2) }}</pre>
            </div>
            <div class="log-section" v-if="log.error">
              <h5>错误信息:</h5>
              <pre class="log-error">{{ log.error }}</pre>
            </div>
            <div class="log-section" v-if="log.duration">
              <h5>执行时间:</h5>
              <span>{{ log.duration }}ms</span>
            </div>
          </div>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, watch, reactive } from 'vue'
import {
  InfoCircleOutlined,
  CloseOutlined,
  RobotOutlined,
  StarFilled,
  DownOutlined
} from '@ant-design/icons-vue'

// ================================================================================
// Props 和 Emits
// ================================================================================

const props = defineProps({
  // 当前智能体
  agent: {
    type: Object,
    default: null
  },
  // 智能体配置
  config: {
    type: Object,
    default: () => ({})
  },
  // MCP调用日志
  mcpLogs: {
    type: Array,
    default: () => []
  },
  // 会话统计
  stats: {
    type: Object,
    default: null
  },
  // 是否默认收起
  defaultCollapsed: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['panel-toggle'])

// ================================================================================
// 响应式数据
// ================================================================================

const collapsed = ref(props.defaultCollapsed)
const configCollapsed = ref(false)
const mcpCollapsed = ref(false)
const statsCollapsed = ref(false)
const mcpModalVisible = ref(false)

// ================================================================================
// 计算属性和方法
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
 * 获取类型颜色
 */
const getTypeColor = (type) => {
  const colorMap = {
    'custom': 'blue',
    'chatbot': 'green',
    'react': 'orange'
  }
  return colorMap[type] || 'default'
}

/**
 * 获取提示词预览
 */
const getPromptPreview = (prompt) => {
  if (!prompt) return ''
  return prompt.length > 50 ? prompt.substring(0, 50) + '...' : prompt
}

/**
 * 格式化时间
 */
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString()
}

/**
 * 格式化完整时间
 */
const formatFullTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleString()
}

/**
 * 格式化持续时间
 */
const formatDuration = (duration) => {
  if (!duration) return '0s'
  if (duration < 60) return `${duration}s`
  const minutes = Math.floor(duration / 60)
  const seconds = duration % 60
  return `${minutes}m ${seconds}s`
}

/**
 * 获取状态标签
 */
const getStatusLabel = (status) => {
  const statusMap = {
    'success': '成功',
    'error': '错误',
    'pending': '进行中'
  }
  return statusMap[status] || status
}

/**
 * 切换面板显示状态
 */
const togglePanel = () => {
  collapsed.value = !collapsed.value
  emit('panel-toggle', collapsed.value)
}

/**
 * 切换配置区域
 */
const toggleConfigSection = () => {
  configCollapsed.value = !configCollapsed.value
}

/**
 * 切换MCP区域
 */
const toggleMcpSection = () => {
  mcpCollapsed.value = !mcpCollapsed.value
}

/**
 * 切换统计区域
 */
const toggleStatsSection = () => {
  statsCollapsed.value = !statsCollapsed.value
}

/**
 * 显示所有MCP日志
 */
const showAllMcpLogs = () => {
  mcpModalVisible.value = true
}

// ================================================================================
// 监听器
// ================================================================================

// 监听智能体变化
watch(() => props.agent, (newAgent) => {
  if (newAgent && collapsed.value) {
    // 如果有新的智能体且面板是收起状态，自动展开
    collapsed.value = false
    emit('panel-toggle', false)
  }
})

// 监听MCP日志变化
watch(() => props.mcpLogs.length, (newLength, oldLength) => {
  if (newLength > oldLength && !mcpCollapsed.value) {
    // 有新的MCP调用时，确保区域是展开的
    mcpCollapsed.value = false
  }
})
</script>

<style scoped>
.agent-info-panel {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  position: relative;
  transition: all 0.3s ease;
}

.agent-info-panel.collapsed {
  padding: 8px;
  width: 40px;
  height: 40px;
}

.panel-toggle {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-radius: 4px;
  color: #666;
  transition: all 0.2s;
}

.panel-toggle:hover {
  background: #f5f5f5;
  color: #1890ff;
}

/* 智能体基本信息 */
.agent-basic-info {
  margin-top: 8px;
}

.agent-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.agent-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #999;
  flex-shrink: 0;
}

.agent-avatar img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.agent-title {
  flex: 1;
}

.agent-name {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.agent-badges {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.agent-description {
  color: #666;
  line-height: 1.5;
  margin: 0 0 16px 0;
  font-size: 14px;
}

/* 区域样式 */
.config-section,
.mcp-logs-section,
.stats-section {
  border-top: 1px solid #f0f0f0;
  padding-top: 12px;
  margin-top: 12px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  padding: 4px 0;
  user-select: none;
}

.section-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.section-header .anticon {
  transition: transform 0.3s;
  color: #999;
}

.section-header .anticon.rotated {
  transform: rotate(180deg);
}

/* 配置内容 */
.config-content {
  margin-top: 8px;
}

.config-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 13px;
}

.config-label {
  font-weight: 500;
  color: #666;
  min-width: 60px;
}

.config-value {
  color: #333;
  flex: 1;
}

.prompt-value {
  display: flex;
  align-items: center;
}

.prompt-preview {
  background: #f5f5f5;
  padding: 4px 8px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
  cursor: help;
}

.tool-tag {
  margin: 2px;
}

/* MCP日志 */
.mcp-content {
  margin-top: 8px;
}

.mcp-logs {
  max-height: 200px;
  overflow-y: auto;
}

.mcp-log-item {
  padding: 8px;
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  margin-bottom: 8px;
  font-size: 12px;
}

.mcp-log-item.success {
  border-left: 3px solid #52c41a;
}

.mcp-log-item.error {
  border-left: 3px solid #ff4d4f;
}

.mcp-log-item.pending {
  border-left: 3px solid #1890ff;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.skill-name {
  font-weight: 500;
  color: #333;
}

.log-time {
  color: #999;
  font-size: 11px;
}

.log-details {
  color: #666;
}

.log-input,
.log-output {
  margin: 2px 0;
}

.log-error {
  margin: 2px 0;
}

.error-text {
  color: #ff4d4f;
}

.mcp-actions {
  text-align: center;
  margin-top: 8px;
}

/* 统计信息 */
.stats-content {
  margin-top: 8px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.stat-item {
  text-align: center;
  padding: 8px;
  background: #fafafa;
  border-radius: 4px;
}

.stat-value {
  display: block;
  font-size: 16px;
  font-weight: 600;
  color: #1890ff;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: #666;
  margin-top: 2px;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 24px;
  color: #999;
}

.empty-icon {
  font-size: 32px;
  margin-bottom: 8px;
  display: block;
}

/* MCP日志详情模态框 */
.mcp-logs-detail {
  max-height: 600px;
  overflow-y: auto;
}

.mcp-log-detail {
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  margin-bottom: 16px;
  overflow: hidden;
}

.mcp-log-detail.success {
  border-left: 4px solid #52c41a;
}

.mcp-log-detail.error {
  border-left: 4px solid #ff4d4f;
}

.mcp-log-detail.pending {
  border-left: 4px solid #1890ff;
}

.log-detail-header {
  background: #fafafa;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.log-detail-header h4 {
  margin: 0;
  font-size: 16px;
  flex: 1;
}

.log-status {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  background: #e6f7ff;
  color: #1890ff;
}

.log-timestamp {
  font-size: 12px;
  color: #999;
}

.log-detail-content {
  padding: 16px;
}

.log-section {
  margin-bottom: 16px;
}

.log-section h5 {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.log-json {
  background: #f6f8fa;
  border: 1px solid #e1e4e8;
  border-radius: 4px;
  padding: 12px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
  overflow-x: auto;
  color: #333;
}

.log-error {
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 4px;
  padding: 12px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 12px;
  color: #ff4d4f;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .agent-info-panel {
    padding: 12px;
  }
  
  .agent-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }
}
</style> 