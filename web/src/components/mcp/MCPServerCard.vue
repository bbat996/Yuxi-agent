<template>
  <a-card
    class="server-card"
    :class="{ 'enabled': server.enabled, 'disabled': !server.enabled }"
    :hoverable="true"
    @click="handleCardClick"
  >
    <template #cover>
      <div class="server-icon">
        <component :is="serverIcon" />
      </div>
    </template>
    <a-card-meta :title="server.name">
      <template #description>
        <div>
          <div>分类: {{ server.category || '未分类' }}</div>
          <div>版本: {{ server.version || '未知' }}</div>
          <div>
            状态:
            <a-tag :color="server.enabled ? 'green' : 'red'">
              {{ server.enabled ? '已启用' : '已禁用' }}
            </a-tag>
          </div>
          <div v-if="server.description" class="server-description">{{ server.description }}</div>
        </div>
      </template>
    </a-card-meta>
    <div class="card-actions">
      <a-button
        type="text"
        size="small"
        @click.stop="$emit('toggleStatus', server.name, !server.enabled)"
      >
        {{ server.enabled ? '禁用' : '启用' }}
      </a-button>
      <a-button type="link" size="small" @click.stop="$emit('viewDetail', server.name)">
        详情
      </a-button>
    </div>
  </a-card>
</template>

<script setup>
import { computed } from 'vue';
import {
  ServerOutlined,
  ApiOutlined,
  CloudServerOutlined,
  DatabaseOutlined,
  RobotOutlined,
  ToolOutlined,
  AppstoreOutlined
} from '@ant-design/icons-vue';

const props = defineProps({
  server: {
    type: Object,
    required: true
  }
});

// 定义事件
const emit = defineEmits(['toggleStatus', 'viewDetail', 'click']);

// 根据服务器类型或分类选择图标
const serverIcon = computed(() => {
  const category = props.server.category ? props.server.category.toLowerCase() : '';
  const name = props.server.name ? props.server.name.toLowerCase() : '';
  
  if (category.includes('api') || name.includes('api')) {
    return ApiOutlined;
  } else if (category.includes('database') || name.includes('db') || name.includes('sql') || name.includes('mongo')) {
    return DatabaseOutlined;
  } else if (category.includes('ai') || name.includes('ai') || name.includes('gpt') || name.includes('llm')) {
    return RobotOutlined;
  } else if (category.includes('tool') || name.includes('tool')) {
    return ToolOutlined;
  } else if (category.includes('cloud') || name.includes('cloud')) {
    return CloudServerOutlined;
  } else if (props.server.icon) {
    return props.server.icon;
  }
  
  return ServerOutlined;
});

// 处理卡片点击事件
const handleCardClick = () => {
  emit('click', props.server);
  emit('viewDetail', props.server.name);
};
</script>

<style scoped lang="less">
.server-card {
  height: 280px;
  display: flex;
  flex-direction: column;

  &.enabled {
    border-color: #52c41a;
  }

  &.disabled {
    opacity: 0.7;
  }

  .server-icon {
    height: 100px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 48px;
    background-color: #f5f5f5;
  }

  .server-description {
    margin-top: 8px;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }

  .card-actions {
    margin-top: auto;
    display: flex;
    justify-content: flex-end;
    padding-top: 12px;
  }
}
</style>
