<template>
  <div class="prompt-template-management">
    <div class="section-header">
      <h3>提示词模板</h3>
      <a-button type="primary" @click="showCreateModal" :icon="h(PlusOutlined)">
        创建模板
      </a-button>
    </div>

    <div class="section">
      <div class="template-filters">
        <a-row :gutter="16">
          <a-col :span="8">
            <a-input-search
              :value="filters.search"
              placeholder="搜索模板名称、描述"
              @search="handleSearch"
              @change="handleSearch"
            />
          </a-col>
          <a-col :span="6">
            <a-select
              :value="filters.category"
              placeholder="分类筛选"
              @change="handleCategoryChange"
              style="width: 100%"
              allowClear
            >
              <a-select-option value="">全部分类</a-select-option>
              <a-select-option
                v-for="category in templateStore.promptCategories"
                :key="category"
                :value="category"
              >
                {{ category }}
              </a-select-option>
            </a-select>
          </a-col>
          <a-col :span="6">
            <a-select
              :value="filters.scope"
              placeholder="范围筛选"
              @change="handleScopeChange"
              style="width: 100%"
            >
              <a-select-option value="">全部模板</a-select-option>
              <a-select-option value="mine">我的模板</a-select-option>
              <a-select-option value="system">系统模板</a-select-option>
            </a-select>
          </a-col>
          <a-col :span="4">
            <a-button
              @click="refreshTemplates"
              :loading="templateStore.loading.promptTemplates"
              :icon="h(ReloadOutlined)"
            >
              刷新
            </a-button>
          </a-col>
        </a-row>
      </div>

      <div class="template-list">
        <a-spin :spinning="templateStore.loading.promptTemplates">
          <a-row :gutter="[16, 16]">
            <a-col v-for="template in filteredTemplates" :key="template.template_id" :span="24">
              <a-card class="template-item-card" :hoverable="true">
                <div class="template-item">
                  <div class="template-info">
                    <div class="template-title">
                      <span class="name">{{ template.name }}</span>
                      <a-space>
                        <a-tag v-if="template.is_system" color="gold">系统</a-tag>
                        <a-tag v-if="template.category" color="blue">{{ template.category }}</a-tag>
                      </a-space>
                    </div>
                    <div class="template-description" v-if="template.description">
                      {{ template.description }}
                    </div>
                    <div class="template-meta">
                      <span class="meta-item">
                        <CalendarOutlined />
                        {{ formatDate(template.created_at) }}
                      </span>
                      <span class="meta-item" v-if="template.use_count">
                        <EyeOutlined />
                        使用 {{ template.use_count }} 次
                      </span>
                      <span
                        class="meta-item"
                        v-if="template.variables && template.variables.length"
                      >
                        <SettingOutlined />
                        {{ template.variables.length }} 个变量
                      </span>
                    </div>
                  </div>
                  <div class="template-actions">
                    <a-space>
                      <a-button
                        size="small"
                        @click="previewTemplate(template)"
                        :icon="h(EyeOutlined)"
                      >
                        预览
                      </a-button>
                      <a-button
                        size="small"
                        @click="editTemplate(template)"
                        :icon="h(EditOutlined)"
                      >
                        编辑
                      </a-button>
                      <a-button
                        size="small"
                        @click="copyTemplate(template)"
                        :icon="h(CopyOutlined)"
                      >
                        复制
                      </a-button>
                      <a-button
                        size="small"
                        danger
                        @click="deleteTemplate(template)"
                        :icon="h(DeleteOutlined)"
                      >
                        删除
                      </a-button>
                    </a-space>
                  </div>
                </div>
              </a-card>
            </a-col>
          </a-row>
        </a-spin>

        <!-- 空状态 -->
        <a-empty
          v-if="!templateStore.loading.promptTemplates && filteredTemplates.length === 0"
          class="empty-state"
        >
          <template #description>
            <span v-if="hasFilters">没有找到符合条件的模板</span>
            <span v-else>还没有提示词模板，快来创建第一个吧！</span>
          </template>
          <a-button v-if="!hasFilters" type="primary" @click="showCreateModal"> 创建模板 </a-button>
        </a-empty>
      </div>
    </div>

    <!-- 模态框 -->
    <a-modal
      :open="modalVisible"
      @update:open="modalVisible = $event"
      :title="modalMode === 'create' ? '创建提示词模板' : '编辑提示词模板'"
      width="800px"
      :footer="null"
      :destroy-on-close="true"
    >
      <PromptTemplateModal
        :mode="modalMode"
        :template="currentTemplate"
        @submit="handleSubmit"
        @cancel="modalVisible = false"
      />
    </a-modal>

    <a-modal
      :open="previewVisible"
      @update:open="previewVisible = $event"
      title="模板预览"
      width="600px"
      :footer="null"
    >
      <PromptTemplatePreview :template="currentTemplate" @close="previewVisible = false" />
    </a-modal>
  </div>
</template>

<script setup>
import { computed, reactive, ref, h, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { useTemplateStore } from '@/stores/template'
import {
  PlusOutlined,
  ReloadOutlined,
  EyeOutlined,
  EditOutlined,
  CopyOutlined,
  DeleteOutlined,
  CalendarOutlined,
  SettingOutlined
} from '@ant-design/icons-vue'
import PromptTemplateModal from '@/components/PromptTemplateModal.vue'
import PromptTemplatePreview from '@/components/PromptTemplatePreview.vue'

const templateStore = useTemplateStore()

// 状态管理
const modalVisible = ref(false)
const modalMode = ref('create')
const previewVisible = ref(false)
const currentTemplate = ref(null)

const filters = reactive({
  search: '',
  category: '',
  scope: ''
})

// 计算属性
const filteredTemplates = computed(() => {
  let templates = [...templateStore.promptTemplates]

  // 搜索过滤
  if (filters.search) {
    const searchTerm = filters.search.toLowerCase()
    templates = templates.filter(
      (template) =>
        template.name?.toLowerCase().includes(searchTerm) ||
        template.description?.toLowerCase().includes(searchTerm)
    )
  }

  // 分类过滤
  if (filters.category) {
    templates = templates.filter((template) => template.category === filters.category)
  }

  // 范围过滤
  if (filters.scope === 'mine') {
    templates = templates.filter((template) => !template.is_system)
  } else if (filters.scope === 'system') {
    templates = templates.filter((template) => template.is_system)
  }

  return templates
})

const hasFilters = computed(() => {
  return filters.search || filters.category || filters.scope
})

// 事件处理
const handleSearch = (value) => {
  if (typeof value === 'string') {
    filters.search = value
  } else if (value && value.target) {
    filters.search = value.target.value
  }
}

const handleCategoryChange = (value) => {
  filters.category = value || ''
}

const handleScopeChange = (value) => {
  filters.scope = value || ''
}

const refreshTemplates = () => {
  templateStore.fetchPromptTemplates()
}

const showCreateModal = () => {
  currentTemplate.value = null
  modalMode.value = 'create'
  modalVisible.value = true
}

const editTemplate = (template) => {
  currentTemplate.value = template
  modalMode.value = 'edit'
  modalVisible.value = true
}

const previewTemplate = (template) => {
  currentTemplate.value = template
  previewVisible.value = true
}

const copyTemplate = async (template) => {
  try {
    const newTemplate = {
      ...template,
      name: template.name + ' (副本)',
      template_id: undefined,
      is_system: false
    }
    currentTemplate.value = newTemplate
    modalMode.value = 'create'
    modalVisible.value = true
  } catch (error) {
    console.error('复制模板失败:', error)
    message.error('复制模板失败')
  }
}

const deleteTemplate = async (template) => {
  try {
    await templateStore.deletePromptTemplate(template.template_id)
    message.success('模板删除成功')
    refreshTemplates()
  } catch (error) {
    console.error('删除模板失败:', error)
    message.error('删除模板失败')
  }
}

const handleSubmit = () => {
  modalVisible.value = false
  refreshTemplates()
}

const formatDate = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}`
}

onMounted(() => {
  templateStore.fetchPromptTemplates()
})
</script>

<style lang="less" scoped>
.prompt-template-management {
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }

  .section {
    background-color: var(--gray-10);
    padding: 20px;
    border-radius: 8px;
    border: 1px solid var(--gray-300);
  }

  .template-filters {
    margin-bottom: 16px;
  }

  .template-list {
    .template-item-card {
      margin-bottom: 16px;
      border: 1px solid var(--gray-300);
      border-radius: 8px;
      transition: all 0.2s;

      &:hover {
        border-color: var(--primary-color);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      }
    }
  }

  .empty-state {
    margin-top: 20px;
  }

  .template-item {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 16px;

    .template-info {
      flex: 1;
      margin-right: 16px;

      .template-title {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 8px;

        .name {
          font-size: 16px;
          font-weight: 500;
          color: var(--gray-900);
        }
      }

      .template-description {
        color: var(--gray-600);
        font-size: 14px;
        margin-bottom: 12px;
        line-height: 1.5;
      }

      .template-meta {
        display: flex;
        gap: 16px;
        flex-wrap: wrap;

        .meta-item {
          display: flex;
          align-items: center;
          gap: 4px;
          color: var(--gray-500);
          font-size: 12px;

          .anticon {
            font-size: 12px;
          }
        }
      }
    }

    .template-actions {
      flex-shrink: 0;
    }
  }
}
</style> 