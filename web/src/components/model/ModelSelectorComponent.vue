<template>
  <!-- 当没有可用模型时，显示禁用状态 -->
  <div v-if="!hasAvailableModels" class="model-select disabled">
    <span class="model-text text">暂无可用模型</span>
  </div>
  
  <!-- 当有可用模型时，显示下拉菜单 -->
  <a-dropdown v-else trigger="click">
    <a class="model-select" @click.prevent>
      <!-- <BulbOutlined /> -->
      <a-tooltip :title="model_name" placement="right">
        <span class="model-text text"> {{ model_name }} </span>
      </a-tooltip>
      <span class="text" style="color: #aaa;">{{ model_provider }} </span>
      <DownOutlined class="dropdown-arrow" />
    </a>
    <template #overlay>
      <a-menu class="scrollable-menu">
        <a-menu-item-group v-for="(item, key) in modelKeys" :key="key" :title="modelNames[item]?.name">
          <a-menu-item v-for="(model, idx) in modelNames[item]?.models" :key="`${item}-${idx}`" @click="handleSelectModel(item, model)">
            {{ model }}
          </a-menu-item>
        </a-menu-item-group>
        <a-menu-item-group v-if="customModels.length > 0" title="自定义模型">
          <a-menu-item v-for="(model, idx) in customModels" :key="`custom-${idx}`" @click="handleSelectModel('custom', model.custom_id)">
            custom/{{ model.custom_id }}
          </a-menu-item>
        </a-menu-item-group>
      </a-menu>
    </template>
  </a-dropdown>
</template>

<script setup>
import { computed } from 'vue'
import { BulbOutlined, DownOutlined } from '@ant-design/icons-vue'
import { useConfigStore } from '@/stores/config'

const props = defineProps({
  model_name: {
    type: String,
    default: ''
  },
  model_provider: {
    type: String,
    default: ''
  }
});

const configStore = useConfigStore()
const emit = defineEmits(['select-model'])

// 从configStore中获取所需数据
const modelNames = computed(() => {
  console.log('ModelSelector: modelNames computed, config:', configStore.config)
  return configStore.config?.model_names
})
const modelStatus = computed(() => configStore.config?.model_provider_status)
const providerEnabledStatus = computed(() => configStore.config?.provider_enabled_status || {})
const customModels = computed(() => configStore.config?.custom_models || [])

// 判断提供商是否启用
const isProviderEnabled = (provider) => {
  // 如果配置中没有启用状态，默认启用
  return providerEnabledStatus.value[provider] !== false
}

// 筛选已配置且启用的模型提供商
const modelKeys = computed(() => {
  const keys = Object.keys(modelStatus.value || {}).filter(key => 
    modelStatus.value?.[key] && isProviderEnabled(key)
  )
  console.log('ModelSelector: modelKeys computed:', keys)
  return keys
})

// 检查是否有可用模型
const hasAvailableModels = computed(() => {
  return modelKeys.value.length > 0 || customModels.value.length > 0
})

// 选择模型的方法
const handleSelectModel = (provider, name) => {
  console.log('ModelSelector: handleSelectModel called with:', { provider, name })
  emit('select-model', { provider, name })
}
</script>

<style lang="less" scoped>
.model-select {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding: 0.25rem 0.5rem;
  cursor: pointer;
  border: 1px solid var(--gray-300);
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background-color: white;
  position: relative;
  z-index: 1;

  &.borderless {
    border: none;
  }

  &.max-width {
    max-width: 380px;
  }

  .model-text {
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .dropdown-arrow {
    font-size: 12px;
    color: #8c8c8c;
    margin-left: 4px;
  }

  &.disabled {
    cursor: not-allowed;
    opacity: 0.6;
    background-color: var(--gray-100);
    color: var(--gray-500);
  }

}

.nav-btn {
  height: 2.5rem;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 8px;
  color: var(--gray-900);
  cursor: pointer;
  width: auto;
  transition: background-color 0.3s;
  padding: 0.5rem 0.75rem;

  .text {
    margin-left: 10px;
  }

  &:hover {
    background-color: var(--main-light-3);
  }
}

.scrollable-menu {
  max-height: 300px;
  overflow-y: auto;

  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
    border-radius: 3px;
  }

  &::-webkit-scrollbar-thumb {
    background: var(--gray-400);
    border-radius: 3px;
  }

  &::-webkit-scrollbar-thumb:hover {
    background: var(--gray-500);
  }
}
</style>

<style lang="less">
// 添加全局样式以确保滚动功能在dropdown内正常工作
.ant-dropdown-menu {
  &.scrollable-menu {
    max-height: 300px;
    overflow-y: auto;
  }
}
</style>