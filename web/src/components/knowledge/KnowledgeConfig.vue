<template>
  <div>
    <!-- 知识库配置弹窗 -->
    <a-modal :visible="modelValue" :title="title" width="600px" @ok="handleSave"
      @cancel="handleCancel">
      <div class="knowledge-config-modal">
        <a-form layout="vertical" :model="configData">
          <a-form-item label="检索数量 (Top K)">
            <a-input-number v-model="configData.top_k" :min="1" :max="20" style="width: 100%"
              placeholder="检索返回的文档数量" />
          </a-form-item>
          <a-form-item label="相似度阈值">
            <a-slider v-model="configData.similarity_threshold" :min="0" :max="1" :step="0.1"
              :tooltip-formatter="(val) => `${val}`" />
            <div style="text-align: center; font-size: 12px; color: #8c8c8c; margin-top: 4px;">
              {{ configData.similarity_threshold }}
            </div>
          </a-form-item>
          <a-form-item label="动态文件解析">
            <a-switch v-model="configData.dynamic_file_parsing" />
            <div style="font-size: 12px; color: #8c8c8c; margin-top: 4px;">
              启用后，智能体可以动态解析用户上传的文件
            </div>
          </a-form-item>
          <a-form-item label="网络搜索">
            <a-switch v-model="configData.web_search" />
            <div style="font-size: 12px; color: #8c8c8c; margin-top: 4px;">
              启用后，智能体可以使用网络搜索获取信息
            </div>
          </a-form-item>
        </a-form>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  knowledgeId: {
    type: String,
    default: null
  },
  knowledgeName: {
    type: String,
    default: ''
  },
  config: {
    type: Object,
    default: () => ({
      top_k: 3,
      similarity_threshold: 0.5,
      dynamic_file_parsing: false,
      web_search: false
    })
  }
})

const emit = defineEmits(['update:modelValue', 'save', 'cancel'])

// 配置数据
const configData = ref({
  top_k: 3,
  similarity_threshold: 0.5,
  dynamic_file_parsing: false,
  web_search: false
})

// 弹窗标题
const title = computed(() => {
  return props.knowledgeId ? `知识库配置: ${props.knowledgeName}` : '知识库检索配置'
})

// 监听props变化
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    configData.value = { ...props.config }
  }
})

// 保存配置
const handleSave = () => {
  emit('save', {
    knowledgeId: props.knowledgeId,
    config: { ...configData.value }
  })
  emit('update:modelValue', false)
}

// 取消配置
const handleCancel = () => {
  emit('cancel')
  emit('update:modelValue', false)
}
</script>

<style lang="less" scoped>
.knowledge-config-modal {
  .ant-form-item {
    margin-bottom: 12px;
  }
}
</style>
