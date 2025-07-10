<template>
  <div class="mcp-skill-management">
    <div class="section-header">
      <h3>MCP技能</h3>
      <a-button type="primary" @click="showCreateModal" :icon="h(PlusOutlined)">
        注册技能
      </a-button>
    </div>
    
    <div class="section">
      <div class="skill-filters">
        <a-row :gutter="16">
          <a-col :span="8">
            <a-input-search
              :value="filters.search"
              placeholder="搜索技能名称、描述"
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
                v-for="category in templateStore.mcpCategories" 
                :key="category" 
                :value="category"
              >
                {{ category }}
              </a-select-option>
            </a-select>
          </a-col>
          <a-col :span="6">
            <a-select
              :value="filters.status"
              placeholder="状态筛选"
              @change="handleStatusChange"
              style="width: 100%"
            >
              <a-select-option value="">全部技能</a-select-option>
              <a-select-option value="active">已激活</a-select-option>
              <a-select-option value="inactive">未激活</a-select-option>
              <a-select-option value="verified">已验证</a-select-option>
            </a-select>
          </a-col>
          <a-col :span="4">
            <a-button @click="refreshSkills" :loading="templateStore.loading.mcpSkills" :icon="h(ReloadOutlined)">
              刷新
            </a-button>
          </a-col>
        </a-row>
      </div>
      
      <div class="skill-list">
        <a-spin :spinning="templateStore.loading.mcpSkills">
          <a-row :gutter="[16, 16]">
            <a-col v-for="skill in filteredSkills" :key="skill.skill_id" :span="24">
              <a-card 
                class="skill-item-card"
                :hoverable="true"
              >
                <div class="skill-item">
                  <div class="skill-info">
                    <div class="skill-title">
                      <span class="name">{{ skill.name }}</span>
                      <a-space>
                        <a-tag :color="skill.is_active ? 'green' : 'orange'">
                          {{ skill.is_active ? '已激活' : '未激活' }}
                        </a-tag>
                        <a-tag v-if="skill.is_verified" color="gold">已验证</a-tag>
                        <a-tag v-if="skill.category" color="blue">{{ skill.category }}</a-tag>
                      </a-space>
                    </div>
                    <div class="skill-description" v-if="skill.description">
                      {{ skill.description }}
                    </div>
                    <div class="skill-meta">
                      <span class="meta-item">
                        <CalendarOutlined />
                        {{ formatDate(skill.created_at) }}
                      </span>
                      <span class="meta-item" v-if="skill.mcp_server">
                        <CloudServerOutlined />
                        {{ skill.mcp_server }}
                      </span>
                      <span class="meta-item" v-if="skill.tool_schema">
                        <ToolOutlined />
                        工具配置
                      </span>
                    </div>
                  </div>
                  <div class="skill-actions">
                    <a-space>
                      <a-button size="small" @click="previewSkill(skill)" :icon="h(EyeOutlined)">
                        预览
                      </a-button>
                      <a-button size="small" @click="editSkill(skill)" :icon="h(EditOutlined)">
                        编辑
                      </a-button>
                      <a-button size="small" @click="testSkill(skill)" :icon="h(ExperimentOutlined)">
                        测试
                      </a-button>
                      <a-button size="small" danger @click="deleteSkill(skill)" :icon="h(DeleteOutlined)">
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
        <a-empty v-if="!templateStore.loading.mcpSkills && filteredSkills.length === 0" class="empty-state">
          <template #description>
            <span v-if="hasFilters">没有找到符合条件的技能</span>
            <span v-else>还没有MCP技能，快来注册第一个吧！</span>
          </template>
          <a-button v-if="!hasFilters" type="primary" @click="showCreateModal">
            注册技能
          </a-button>
        </a-empty>
      </div>
    </div>
    
    <!-- 模态框 -->
    <a-modal
      :open="modalVisible"
      @update:open="modalVisible = $event"
      :title="modalMode === 'create' ? '注册MCP技能' : '编辑MCP技能'"
      width="800px"
      :footer="null"
      :destroy-on-close="true"
    >
      <MCPSkillModal
        :mode="modalMode"
        :skill="currentSkill"
        @submit="handleSubmit"
        @cancel="modalVisible = false"
      />
    </a-modal>
    
    <a-modal
      :open="previewVisible"
      @update:open="previewVisible = $event"
      title="技能预览"
      width="600px"
      :footer="null"
    >
      <MCPSkillPreview
        :skill="currentSkill"
        @close="previewVisible = false"
      />
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
  DeleteOutlined,
  CalendarOutlined,
  CloudServerOutlined,
  ToolOutlined,
  ExperimentOutlined
} from '@ant-design/icons-vue'
import MCPSkillModal from '@/components/MCPSkillModal.vue'
import MCPSkillPreview from '@/components/MCPSkillPreview.vue'

const templateStore = useTemplateStore()

// 状态管理
const modalVisible = ref(false)
const modalMode = ref('create')
const previewVisible = ref(false)
const currentSkill = ref(null)

const filters = reactive({
  search: '',
  category: '',
  status: ''
})

// 计算属性
const filteredSkills = computed(() => {
  let skills = [...templateStore.mcpSkills]
  
  // 搜索过滤
  if (filters.search) {
    const searchTerm = filters.search.toLowerCase()
    skills = skills.filter(skill => 
      skill.name?.toLowerCase().includes(searchTerm) ||
      skill.description?.toLowerCase().includes(searchTerm)
    )
  }
  
  // 分类过滤
  if (filters.category) {
    skills = skills.filter(skill => skill.category === filters.category)
  }
  
  // 状态过滤
  if (filters.status) {
    if (filters.status === 'active') {
      skills = skills.filter(skill => skill.is_active === true)
    } else if (filters.status === 'inactive') {
      skills = skills.filter(skill => skill.is_active === false)
    } else if (filters.status === 'verified') {
      skills = skills.filter(skill => skill.is_verified === true)
    }
  }
  
  return skills
})

const hasFilters = computed(() => {
  return filters.search || filters.category || filters.status
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

const handleStatusChange = (value) => {
  filters.status = value || ''
}

const refreshSkills = () => {
  templateStore.fetchMcpSkills()
}

const showCreateModal = () => {
  currentSkill.value = null
  modalMode.value = 'create'
  modalVisible.value = true
}

const editSkill = (skill) => {
  currentSkill.value = skill
  modalMode.value = 'edit'
  modalVisible.value = true
}

const previewSkill = (skill) => {
  currentSkill.value = skill
  previewVisible.value = true
}

const testSkill = async (skill) => {
  try {
    message.loading({ content: `正在测试技能 ${skill.name}...`, key: 'test-skill', duration: 0 })
    await templateStore.testMcpSkill(skill.skill_id)
    message.success({ content: `技能 ${skill.name} 测试成功`, key: 'test-skill', duration: 2 })
  } catch (error) {
    console.error('测试技能失败:', error)
    message.error({ content: `技能 ${skill.name} 测试失败`, key: 'test-skill', duration: 2 })
  }
}

const deleteSkill = async (skill) => {
  try {
    await templateStore.deleteMcpSkill(skill.skill_id)
    message.success('技能删除成功')
    refreshSkills()
  } catch (error) {
    console.error('删除技能失败:', error)
    message.error('删除技能失败')
  }
}

const handleSubmit = () => {
  modalVisible.value = false
  refreshSkills()
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
  templateStore.fetchMcpSkills()
})
</script>

<style lang="less" scoped>
.mcp-skill-management {
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

  .skill-filters {
    margin-bottom: 16px;
  }

  .skill-list {
    .skill-item-card {
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

  .skill-item {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 16px;

    .skill-info {
      flex: 1;
      margin-right: 16px;

      .skill-title {
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

      .skill-description {
        color: var(--gray-600);
        font-size: 14px;
        margin-bottom: 12px;
        line-height: 1.5;
      }

      .skill-meta {
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

    .skill-actions {
      flex-shrink: 0;
    }
  }
}
</style> 