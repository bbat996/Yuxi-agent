<template>
  <div class="agent-card" :class="{ 'agent-card--favorite': agent.is_favorite }">
    <!-- 卡片头部 -->
    <div class="agent-card__header">
      <div class="agent-card__avatar">
        <a-avatar :size="40" :src="agent.avatar || undefined">
          <template #icon v-if="!agent.avatar">
            <RobotOutlined />
          </template>
        </a-avatar>
      </div>
      <div class="agent-card__info">
        <h3 class="agent-card__name" :title="agent.name">{{ agent.name }}</h3>
        <div class="agent-card__meta">
          <a-tag :color="getTypeColor(agent.agent_type)" size="small">
            {{ getTypeLabel(agent.agent_type) }}
          </a-tag>
          <span class="agent-card__date">
            {{ formatDate(agent.updated_at) }}
          </span>
        </div>
      </div>
      <div class="agent-card__actions">
        <a-dropdown placement="bottomRight" trigger="click">
          <a-button type="text" size="small">
            <template #icon><MoreOutlined /></template>
          </a-button>
          <template #overlay>
            <a-menu>
              <a-menu-item key="view" @click="$emit('view', agent)">
                <EyeOutlined />
                查看详情
              </a-menu-item>
              <a-menu-item key="edit" @click="$emit('edit', agent)">
                <EditOutlined />
                编辑
              </a-menu-item>
              <a-menu-item key="duplicate" @click="$emit('duplicate', agent)">
                <CopyOutlined />
                复制
              </a-menu-item>
              <a-menu-divider />
              <a-menu-item key="favorite" @click="$emit('toggle-favorite', agent)">
                <StarOutlined v-if="!agent.is_favorite" />
                <StarFilled v-else />
                {{ agent.is_favorite ? '取消收藏' : '收藏' }}
              </a-menu-item>
              <a-menu-divider />
              <a-menu-item key="delete" @click="$emit('delete', agent)" class="danger">
                <DeleteOutlined />
                删除
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </div>
    </div>

    <!-- 卡片内容 -->
    <div class="agent-card__content">
      <p class="agent-card__description" :title="agent.description">
        {{ agent.description || '暂无描述' }}
      </p>
      
      <!-- 配置信息 -->
      <div class="agent-card__config">
        <div class="config-item" v-if="agent.model_config?.model">
          <span class="config-label">模型:</span>
          <span class="config-value">{{ agent.model_config.model }}</span>
        </div>
        <div class="config-item" v-if="agent.tools_config?.length">
          <span class="config-label">工具:</span>
          <span class="config-value">{{ agent.tools_config.length }} 个</span>
        </div>
        <div class="config-item" v-if="agent.knowledge_config?.databases?.length">
          <span class="config-label">知识库:</span>
          <span class="config-value">{{ agent.knowledge_config.databases.length }} 个</span>
        </div>
      </div>
    </div>

    <!-- 卡片底部 -->
    <div class="agent-card__footer">
      <div class="agent-card__stats">
        <span class="stat-item">
          <MessageOutlined />
          {{ agent.chat_count || 0 }} 次对话
        </span>
        <span class="stat-item">
          <UserOutlined />
          {{ agent.created_by_name || '未知' }}
        </span>
      </div>
      
      <div class="agent-card__buttons">
        <a-button type="primary" size="small" @click="$emit('chat', agent)">
          <template #icon><MessageOutlined /></template>
          聊天
        </a-button>
      </div>
    </div>

    <!-- 收藏标识 -->
    <div class="agent-card__favorite-badge" v-if="agent.is_favorite">
      <StarFilled />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { 
  RobotOutlined, 
  MoreOutlined,
  EyeOutlined,
  EditOutlined,
  CopyOutlined,
  DeleteOutlined,
  StarOutlined,
  StarFilled,
  MessageOutlined,
  UserOutlined
} from '@ant-design/icons-vue'

// Props
const props = defineProps({
  agent: {
    type: Object,
    required: true
  }
})

// Emits
defineEmits([
  'view',
  'edit', 
  'delete',
  'duplicate',
  'toggle-favorite',
  'chat'
])

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

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '未知'
  
  const date = new Date(dateString)
  const now = new Date()
  const diff = now - date
  
  // 计算时间差
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes} 分钟前`
  if (hours < 24) return `${hours} 小时前`
  if (days < 7) return `${days} 天前`
  
  return date.toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.agent-card {
  background: white;
  border-radius: 12px;
  border: 1px solid #e8e8e8;
  padding: 16px;
  transition: all 0.3s ease;
  cursor: pointer;
  position: relative;
  height: 280px;
  display: flex;
  flex-direction: column;
}

.agent-card:hover {
  border-color: #1890ff;
  box-shadow: 0 4px 16px rgba(24, 144, 255, 0.12);
  transform: translateY(-2px);
}

.agent-card--favorite {
  border-color: #faad14;
}

.agent-card__header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.agent-card__avatar {
  flex-shrink: 0;
}

.agent-card__info {
  flex: 1;
  min-width: 0;
}

.agent-card__name {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.4;
}

.agent-card__meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}

.agent-card__date {
  font-size: 12px;
  color: #999;
}

.agent-card__actions {
  flex-shrink: 0;
}

.agent-card__content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.agent-card__description {
  margin: 0;
  font-size: 14px;
  color: #666;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

.agent-card__config {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.config-item {
  display: flex;
  align-items: center;
  font-size: 12px;
}

.config-label {
  color: #999;
  margin-right: 8px;
  min-width: 40px;
}

.config-value {
  color: #666;
  font-weight: 500;
}

.agent-card__footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: auto;
  padding-top: 12px;
  border-top: 1px solid #f5f5f5;
}

.agent-card__stats {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #999;
}

.stat-item .anticon {
  font-size: 12px;
}

.agent-card__buttons {
  display: flex;
  gap: 8px;
}

.agent-card__favorite-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  color: #faad14;
  font-size: 16px;
}

/* 下拉菜单样式 */
:deep(.ant-dropdown-menu-item.danger) {
  color: #ff4d4f;
}

:deep(.ant-dropdown-menu-item.danger:hover) {
  background-color: #fff2f0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .agent-card {
    height: auto;
    min-height: 250px;
  }
  
  .agent-card__footer {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .agent-card__stats {
    flex-direction: row;
    justify-content: space-between;
  }
}
</style> 