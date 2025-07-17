<template>
  <div>
    <!-- 知识库选择弹窗 -->
    <a-modal :visible="modelValue" title="选择知识库" width="800px" @ok="handleSelect"
      @cancel="handleCancel">
      <div class="knowledge-modal">
        <div class="knowledge-search-bar">
          <a-input-search
            v-model="searchKeyword"
            placeholder="搜索知识库名称或描述..."
            style="width: 100%; margin-bottom: 16px"
            @search="searchKnowledgeBases"
            allow-clear
          >
            <template #prefix>
              <SearchOutlined />
            </template>
          </a-input-search>
        </div>
        <a-table 
          :columns="columns" 
          :data-source="filteredKnowledgeList"
          :row-selection="{ 
            selectedRowKeys: selectedKeys, 
            onChange: onSelectionChange,
            getCheckboxProps: (record) => ({
              disabled: false
            })
          }"
          :pagination="false" 
          size="small"
          :loading="loading"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'action'">
              <a-button type="link" size="small" @click="previewKnowledge(record)">预览</a-button>
            </template>
          </template>
        </a-table>
        <div class="knowledge-modal-footer" v-if="selectedKeys.length > 0">
          <div class="selected-count">
            已选择 {{ selectedKeys.length }} 个知识库
          </div>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import { SearchOutlined } from '@ant-design/icons-vue'
import { knowledgeBaseApi } from '@/apis/admin_api'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  selectedDatabases: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'select', 'cancel'])

// 知识库列表
const knowledgeList = ref([])
const selectedKeys = ref([])
const searchKeyword = ref('')
const loading = ref(false)

// 表格列定义
const columns = [
  {
    title: '名称',
    dataIndex: 'name',
    key: 'name',
  },
  {
    title: '描述',
    dataIndex: 'description',
    key: 'description',
    ellipsis: true,
  },
  {
    title: '嵌入模型',
    dataIndex: 'embed_model',
    key: 'embed_model',
  },
  {
    title: '操作',
    key: 'action',
    width: 80,
  }
]

// 过滤后的知识库列表
const filteredKnowledgeList = computed(() => {
  if (!searchKeyword.value) {
    return knowledgeList.value
  }
  const keyword = searchKeyword.value.toLowerCase()
  return knowledgeList.value.filter(item => 
    item.name.toLowerCase().includes(keyword) || 
    (item.description && item.description.toLowerCase().includes(keyword))
  )
})

// 监听props变化
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    selectedKeys.value = [...props.selectedDatabases]
    loadKnowledgeBases()
  }
})

watch(() => props.selectedDatabases, (newVal) => {
  selectedKeys.value = [...newVal]
})

// 加载知识库列表
const loadKnowledgeBases = async () => {
  try {
    loading.value = true
    const response = await knowledgeBaseApi.getDatabases()
    if (response.databases) {
      knowledgeList.value = response.databases.map(db => ({
        db_id: db.db_id,
        name: db.name,
        description: db.description,
        embed_model: db.embed_model,
        dimension: db.dimension
      }))
    }
  } catch (error) {
    console.error('加载知识库列表失败:', error)
    // 非管理员用户可能无法访问知识库API，使用默认数据或提示
    if (error.message && error.message.includes('权限')) {
      message.warning('您没有权限访问知识库管理功能，请联系管理员')
      knowledgeList.value = []
    } else {
      message.error('加载知识库列表失败')
      knowledgeList.value = []
    }
  } finally {
    loading.value = false
  }
}

// 搜索知识库
const searchKnowledgeBases = () => {
  // 搜索已由计算属性filteredKnowledgeList处理
}

// 知识库选择变化
const onSelectionChange = (selectedRowKeys) => {
  selectedKeys.value = selectedRowKeys
}

// 预览知识库
const previewKnowledge = (record) => {
  message.info(`预览知识库: ${record.name}`)
  // 这里可以实现预览功能，例如打开一个新的弹窗显示知识库详情
}

// 确认选择
const handleSelect = () => {
  const selectedItems = knowledgeList.value.filter(item => 
    selectedKeys.value.includes(item.db_id)
  )
  emit('select', selectedItems)
  emit('update:modelValue', false)
}

// 取消选择
const handleCancel = () => {
  emit('cancel')
  emit('update:modelValue', false)
}
</script>

<style lang="less" scoped>
.knowledge-modal {
  .knowledge-search-bar {
    margin-bottom: 16px;
  }
  
  .knowledge-modal-footer {
    margin-top: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .selected-count {
      font-size: 14px;
      color: #666;
    }
  }
}
</style>
