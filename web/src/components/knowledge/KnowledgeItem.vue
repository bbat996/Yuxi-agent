<template>
  <div class="knowledge-item">
    <div class="knowledge-item-info">
      <span class="knowledge-item-name">{{ name }}</span>
    </div>
    <div class="knowledge-item-actions">
      <a-button type="link" size="small" @click="$emit('configure')">
        <template #icon><SettingOutlined /></template>
      </a-button>
      <a-button type="link" size="small" danger @click="$emit('remove')">
        <template #icon><DeleteOutlined /></template>
      </a-button>
    </div>
  </div>
</template>

<script setup>
import { SettingOutlined, DeleteOutlined } from '@ant-design/icons-vue'

defineProps({
  name: {
    type: String,
    required: true
  }
})

defineEmits(['configure', 'remove'])
</script>

<style lang="less" scoped>
.knowledge-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background-color: #f5f5f5;
  border-radius: 4px;
  
  .knowledge-item-info {
    display: flex;
    align-items: center;
    
    .knowledge-item-name {
      font-weight: 500;
      margin-right: 8px;
    }
  }
  
  .knowledge-item-actions {
    display: flex;
    gap: 4px;
  }
}
</style>
