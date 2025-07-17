<template>
  <div class="action-item">
    <div class="action-item-info">
      <component :is="icon" class="action-item-icon" v-if="icon" />
      <span class="action-item-name">{{ name }}</span>
    </div>
    <div class="action-item-extra">
      <slot name="extra"></slot>
    </div>
    <div class="action-item-actions">
      <a-button v-if="showConfigure" type="link" size="small" @click="$emit('configure')">
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
  },
  showConfigure: {
    type: Boolean,
    default: true
  },
  icon: {
    type: Object,
    required: false,
    default: null
  }
})

defineEmits(['configure', 'remove'])
</script>

<style lang="less" scoped>
.action-item {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 8px;
  align-items: center;
  padding: 8px 12px;
  background-color: #f5f5f5;
  border-radius: 4px;
  
  .action-item-info {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .action-item-name {
      font-weight: 500;
      margin-right: 8px;
    }
  }
  
  .action-item-actions {
    display: flex;
    gap: 4px;
  }
}
</style>
