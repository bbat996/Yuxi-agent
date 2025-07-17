<template>
  <div class="agent-edit-view layout-container">
    <!-- 页面头部 -->
    <HeaderComponent :title="form.name || '编辑智能体'" :loading="loading" :show-back-button="true" :show-save-button="true"
      :saving="saving" @back="goBack" @save="onSave">
      <template #title-action>
        <a-button type="text" shape="circle" @click="openEditInfoModal" title="编辑名称和描述">
          <template #icon>
            <EditOutlined />
          </template>
        </a-button>
      </template>
      <template #tabSwitch>
        <div class="custom-tab-switch">
          <div class="tab-container">
            <div class="tab-item" :class="{ active: activeTab === 'config' }" @click="activeTab = 'config'">
              <span>应用配置</span>
            </div>
            <div class="tab-item" :class="{ active: activeTab === 'publish' }" @click="activeTab = 'publish'">
              <span>发布渠道</span>
            </div>
          </div>
        </div>
      </template>
    </HeaderComponent>

    <div class="main-content">
      <div class="tab-content">
        <div v-show="activeTab === 'config'">
          <div class="edit-container">
            <!-- 左侧配置区域 -->
            <div class="left-panel">
              <div class="config-content">
                <a-steps direction="vertical" :current="getCurrentStepIndex()" class="edit-steps" progressDot>
                  <a-step :class="{ expanded: stepStates.instruction }">
                    <template #title>
                      <div class="step-title-wrapper" @click.stop="toggleStep('instruction')">
                        <span>指令</span>
                        <DownOutlined v-if="!stepStates.instruction" class="step-toggle-icon" />
                        <UpOutlined v-else class="step-toggle-icon" />
                      </div>
                    </template>
                    <template #description>
                      <div class="step-content" v-show="stepStates.instruction">
                        <div class="section">
                          <a-form ref="formRef" layout="vertical" :model="form" :rules="formRules"
                            @submit.prevent="onSave">
                            <a-form-item name="system_prompt">
                              <template #label>
                                <div class="form-item-label">
                                  <span>系统提示词</span>
                                  <div class="label-actions">
                                    <a-button type="link" size="small"><template #icon>
                                        <FileTextOutlined />
                                      </template>模板</a-button>
                                    <a-button type="link" size="small"><template #icon>
                                        <BulbOutlined />
                                      </template>优化</a-button>
                                  </div>
                                </div>
                              </template>
                              <a-textarea :value="form.system_prompt" @update:value="form.system_prompt = $event"
                                :maxlength="30720" :auto-size="{ minRows: 4, maxRows: 8 }"
                                placeholder="请输入系统提示词，定义智能体的行为和能力" />
                              <div class="prompt-info">{{ form.system_prompt.length }} / 30720</div>
                            </a-form-item>
                            <div class="model-config-section">
                              <div class="model-selector-wrapper">
                                <span class="config-label">选择模型:</span>
                                <ModelSelectorComponent :model_name="form.model_config.model"
                                  :model_provider="form.model_config.provider" @select-model="handleModelSelect" />
                                <a-button type="link" size="small" @click="openModelConfigModal" class="config-btn">
                                  <SettingOutlined />
                                  配置
                                </a-button>
                              </div>
                            </div>
                          </a-form>
                        </div>
                      </div>
                    </template>
                  </a-step>
                  <a-step :class="{ expanded: stepStates.knowledge }">
                    <template #title>
                      <div class="step-title-wrapper" @click.stop="toggleStep('knowledge')">
                        <span>知识</span>
                        <DownOutlined v-if="!stepStates.knowledge" class="step-toggle-icon" />
                        <UpOutlined v-else class="step-toggle-icon" />
                      </div>
                    </template>
                    <template #description>
                      <div class="step-content" v-show="stepStates.knowledge">
                        <div class="section">
                          <div class="section-row">
                            <a-form-item label="知识库">
                              <a-switch :checked="form.knowledge_config.enabled"
                                @update:checked="form.knowledge_config.enabled = $event" />
                            </a-form-item>
                            <div v-if="form.knowledge_config.enabled" class="knowledge-section">
                              <a-button type="text" @click="openKnowledgeModal">+ 选择知识库</a-button>
                              <div class="selected-knowledge-list">
                                <div v-for="db in selectedKnowledgeBases" :key="db.db_id" class="knowledge-item">
                                  <span class="knowledge-name">{{ db.name }}</span>
                                  <div class="knowledge-actions">
                                    <a-button type="link" @click="openKnowledgeConfig(db)">配置</a-button>
                                    <a-button type="link" danger @click="removeKnowledge(db.db_id)">移除</a-button>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                          <div v-if="form.knowledge_config.enabled" class="knowledge-list-container">
                            <div v-if="form.knowledge_config.databases.length === 0" class="empty-knowledge">
                              <p>暂无选择的知识库，请点击上方按钮选择</p>
                            </div>
                            <div v-else class="knowledge-item-list">
                              <ActionItem v-for="dbId in form.knowledge_config.databases" :key="dbId"
                                :name="getKnowledgeName(dbId)" @configure="configureKnowledge(dbId)"
                                @remove="removeKnowledge(dbId)" />
                            </div>
                          </div>

                        </div>
                      </div>
                    </template>
                  </a-step>
                  <a-step :class="{ expanded: stepStates.skills }">
                    <template #title>
                      <div class="step-title-wrapper" @click.stop="toggleStep('skills')">
                        <span>技能</span>
                        <DownOutlined v-if="!stepStates.skills" class="step-toggle-icon" />
                        <UpOutlined v-else class="step-toggle-icon" />
                      </div>
                    </template>
                    <template #description>
                      <div class="step-content" v-show="stepStates.skills">
                        <div class="section">
                          <div class="section-row">
                            <div class="section-left">
                              <span>MCP服务</span>
                              <a-switch :checked="form.mcp_config.enabled"
                                @update:checked="form.mcp_config.enabled = $event" size="small" />
                              <span class="section-action">{{ form.mcp_config.servers.length }}/{{ mcpServerList.length
                              }}</span>
                            </div>
                            <div class="section-right">
                              <a-button type="text" size="small" @click="openMCPSkillModal">
                               + MCP
                              </a-button>
                            </div>
                          </div>

                          <div v-if="form.mcp_config.enabled && form.mcp_config.servers.length > 0"
                            class="mcp-skills-list">
                            <div v-for="serverName in form.mcp_config.servers" :key="serverName" class="section-row">
                              <div class="section-left">
                                <span style="margin-left: 24px;">
                                  {{ getServerDisplayName(serverName) }}
                                  <a-tag :color="getServerIsExternal(serverName) ? 'orange' : 'blue'" size="small"
                                    style="margin-left: 8px;">
                                    {{ getServerIsExternal(serverName) ? '外部' : '内置' }}
                                  </a-tag>
                                </span>
                                <span class="section-action">{{ getServerDisplayDescription(serverName) }}</span>
                                <a-tag color="blue" size="small" style="margin-left: 8px;">{{
                                  getServerDisplayToolsCount(serverName) }} 工具</a-tag>
                              </div>
                              <div class="section-right">
                                <a-button type="link" size="small" @click="removeMCPServer(serverName)">x</a-button>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </template>
                  </a-step>
                </a-steps>
              </div>
            </div>

            <!-- 右侧对话区域 -->
            <div class="right-panel">
              <div class="chat-header">
                <h3>对话测试</h3>
                <p>在这里测试智能体的对话能力</p>
              </div>
              <div class="chat-content">
                <SimpleAgentChat :agent-id="agentId" :config="{}" :state="{}" />
              </div>
            </div>
          </div>
        </div>
        <div v-show="activeTab === 'publish'" class="publish-container">
          <p>发布渠道功能正在开发中...</p>
        </div>
      </div>
    </div>

    <!-- 模型配置弹窗 -->
    <a-modal :visible="showModelConfigModal" @update:visible="showModelConfigModal = $event" title="模型推理参数配置"
      width="600px" @ok="handleModelConfigSave" @cancel="handleModelConfigCancel">
      <div class="model-config-modal">
        <a-form layout="vertical" :model="tempModelConfig">
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="最大Token数">
                <a-input-number :value="tempModelConfig.max_tokens" @update:value="tempModelConfig.max_tokens = $event"
                  :min="100" :max="8000" style="width: 100%" placeholder="请输入最大token数" />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="Temperature">
                <a-slider :value="tempModelConfig.temperature" @update:value="tempModelConfig.temperature = $event"
                  :min="0" :max="2" :step="0.1" :tooltip-formatter="(val) => `${val}`" />
                <div style="text-align: center; font-size: 12px; color: #8c8c8c; margin-top: 4px;">
                  {{ tempModelConfig.temperature }}
                </div>
              </a-form-item>
            </a-col>
          </a-row>
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="Top P">
                <a-slider :value="tempModelConfig.top_p" @update:value="tempModelConfig.top_p = $event" :min="0"
                  :max="1" :step="0.1" :tooltip-formatter="(val) => `${val}`" />
                <div style="text-align: center; font-size: 12px; color: #8c8c8c; margin-top: 4px;">
                  {{ tempModelConfig.top_p }}
                </div>
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="当前模型">
                <div class="current-model-info">
                  <span class="model-name">{{ form.model_config.model }}</span>
                  <span class="model-provider">({{ form.model_config.provider }})</span>
                </div>
              </a-form-item>
            </a-col>
          </a-row>
        </a-form>
      </div>
    </a-modal>

    <!-- 知识库选择弹窗 -->
    <KnowledgeSelector :visible="showKnowledgeModal" @update:visible="showKnowledgeModal = $event"
      :selected-databases="form.knowledge_config.databases" @select="handleKnowledgeSelect" />

    <!-- 知识库配置弹窗 -->
    <KnowledgeConfig :visible="showKnowledgeConfigModal" @update:visible="showKnowledgeConfigModal = $event"
      :knowledge-id="currentKnowledgeId" :knowledge-name="currentKnowledgeName" :config="currentKnowledgeConfig"
      @save="handleKnowledgeConfigSave" />

    <!-- MCP服务器选择弹窗 -->
    <a-modal :visible="showMCPSkillModal" @update:visible="showMCPSkillModal = $event" title="选择MCP服务器" width="800px"
      @ok="handleMCPSkillSelect" @cancel="handleMCPSkillCancel">
      <div class="mcp-skill-modal">
        <div class="search-section">
          <a-input :value="mcpSearchKeyword" @update:value="mcpSearchKeyword = $event" placeholder="搜索服务器名称、描述或工具数量..."
            allow-clear @change="searchMCPServers">
            <template #prefix>
              <SearchOutlined />
            </template>
          </a-input>
        </div>
        <a-table :columns="mcpColumns" :data-source="filteredMCPServerList"
          :row-selection="{ selectedRowKeys: selectedMCPKeys, onChange: onMCPSelectionChange, type: 'checkbox' }"
          :pagination="false" size="small" row-key="name">
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'name'">
              <div class="skill-name-cell">
                <span>{{ record.name }}</span>

                <a-tag v-if="isServerSelected(record.name)" color="green" size="small">已选择</a-tag>
              </div>
            </template>
            <template v-else-if="column.key === 'tools_count'">
              <a-tag color="blue" size="small">{{ record.tools_count }} 工具</a-tag>
            </template>
            <template v-else-if="column.key === 'enabled'">
              <a-tag :color="record.enabled ? 'green' : 'red'" size="small">{{ record.enabled ? '启用' : '禁用' }}</a-tag>
            </template>
            <template v-else-if="column.key === 'action'">
              <a-button type="link" size="small" @click="previewMCPSkill(record)">预览</a-button>
            </template>
          </template>
        </a-table>
      </div>
    </a-modal>

    <!-- 编辑智能体信息弹窗 -->
    <AgentModal :visible="showEditInfoModal" @update:visible="showEditInfoModal = $event" :agent="tempInfo" mode="edit"
      @success="handleEditInfoSave" />
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { DownOutlined, UpOutlined, SettingOutlined, SearchOutlined, EditOutlined, FileTextOutlined, BulbOutlined, PlusOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import SimpleAgentChat from '@/components/agent/SimpleAgentChat.vue'
import ActionItem from '@/components/common/ActionItem.vue'
import HeaderComponent from '@/components/HeaderComponent.vue'
import ModelSelectorComponent from '@/components/model/ModelSelectorComponent.vue'
import AgentModal from '@/components/agent/AgentModal.vue'
import { KnowledgeSelector, KnowledgeConfig } from '@/components/knowledge'
import { getAgent, updateAgent } from '@/apis/agent_api'
import { knowledgeBaseApi } from '@/apis/admin_api'
import { templateAPI } from '@/apis/template_api'
import { mcpConfigApi } from '@/apis/mcp_api'
import { useConfigStore } from '@/stores/config'
import { useAgentStore } from '@/stores/agent'

const route = useRoute()
const router = useRouter()

// 初始化stores
const configStore = useConfigStore()
const agentStore = useAgentStore()

// 从路由参数获取agentId
const agentId = ref(route.params.agent_id)
const loading = ref(false)
const saving = ref(false)

// MCP服务器列表
const mcpServerList = ref([])
const filteredMCPServerList = ref([])
const mcpSearchKeyword = ref('')
const showMCPSkillModal = ref(false)
const selectedMCPKeys = ref([])
const knowledgeSearchKeyword = ref('')
const knowledgeLoading = ref(false)

// 知识库列表
const knowledgeList = ref([])
const selectedKnowledgeKeys = ref([])
const showKnowledgeModal = ref(false)
const currentEditingKnowledge = ref(null)

// MCP服务器列表列定义
const mcpColumns = [
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
    title: '工具数量',
    dataIndex: 'tools_count',
    key: 'tools_count',
    width: 100,
  },
  {
    title: '状态',
    dataIndex: 'enabled',
    key: 'enabled',
    width: 80,
  },
  {
    title: '操作',
    key: 'action',
    width: 80,
  }
]

// 过滤后的知识库列表
const filteredKnowledgeList = computed(() => {
  if (!knowledgeSearchKeyword.value) {
    return knowledgeList.value
  }
  const keyword = knowledgeSearchKeyword.value.toLowerCase()
  return knowledgeList.value.filter(item =>
    item.name.toLowerCase().includes(keyword) ||
    (item.description && item.description.toLowerCase().includes(keyword))
  )
})
const knowledgeColumns = [
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

// 表单数据
const form = ref({
  name: '',
  description: '',
  system_prompt: '',
  avatar: null,
  model_config: {
    provider: '',
    model: '',
    config: {}
  },
  knowledge_config: {
    enabled: false,
    databases: [],
    retrieval_config: {
      top_k: 3,
      similarity_threshold: 0.5
    }
  },
  mcp_config: {
    enabled: false,
    servers: []
  }
})

// 编辑名称和描述的弹窗
const showEditInfoModal = ref(false)
const tempInfo = ref({ name: '', description: '' })

// 知识库配置弹窗
const showKnowledgeConfigModal = ref(false)
const tempKnowledgeConfig = ref({
  top_k: 3,
  similarity_threshold: 0.5,
  dynamic_file_parsing: false,
  web_search: false
})
// 编辑智能体信息的弹窗
const openEditInfoModal = () => {
  tempInfo.value = {
    name: form.value.name,
    description: form.value.description,
    agent_type: 'chatbot',
    avatar: form.value.avatar || null
  }
  showEditInfoModal.value = true
};

const handleEditInfoSave = (updatedAgent) => {
  form.value.name = updatedAgent.name
  form.value.description = updatedAgent.description
  form.value.avatar = updatedAgent.avatar
  showEditInfoModal.value = false
};

const handleEditInfoCancel = () => {
  showEditInfoModal.value = false
};

// Tab管理
const activeTab = ref('config');

// 步骤状态管理
const stepStates = ref({
  instruction: true,  // 指令步骤默认展开
  knowledge: false,
  skills: false
})

const activeStep = ref('instruction')

// 获取当前步骤的索引
const getCurrentStepIndex = () => {
  const stepOrder = ['instruction', 'knowledge', 'skills']
  return stepOrder.indexOf(activeStep.value)
}

// 切换步骤展开/折叠状态
const toggleStep = (stepKey) => {
  console.log('Toggle step:', stepKey, 'Current state:', stepStates.value[stepKey])
  stepStates.value[stepKey] = !stepStates.value[stepKey]
  console.log('New state:', stepStates.value[stepKey])

  // 如果展开，设置为激活状态
  if (stepStates.value[stepKey]) {
    activeStep.value = stepKey
  }
}

// 重置所有步骤为折叠状态
const collapseAllSteps = () => {
  stepStates.value = {
    instruction: true,  // 保持指令步骤展开
    knowledge: false,
    skills: false
  }
}

// 展开所有步骤
const expandAllSteps = () => {
  stepStates.value = {
    instruction: true,
    knowledge: true,
    skills: true
  }
}

// 修改表单数据结构以匹配后端API
const formRules = {
  system_prompt: [
    { required: true, message: '请输入系统提示词' },
    { min: 10, message: '系统提示词至少需要10个字符' }
  ]
}

// 返回上一页
const goBack = () => {
  router.back()
}

// 加载智能体数据
const loadAgentData = async () => {
  if (!agentId.value) return

  try {
    loading.value = true
    const response = await getAgent(agentId.value)

    if (response.success) {
      const agentData = response.data
      console.log('=== 加载智能体数据 ===')
      console.log('原始数据:', agentData)

      // 映射后端数据到表单结构
      form.value = {
        name: agentData.name,
        description: agentData.description,
        system_prompt: agentData.system_prompt || '',
        avatar: agentData.avatar || null,
        model_config: {
          provider: agentData.model_config?.provider || '',
          model: agentData.model_config?.model_name || '',
          config: agentData.model_config?.parameters || {}
        },
        knowledge_config: {
          enabled: agentData.knowledge_config?.databases?.length > 0,
          databases: agentData.knowledge_config?.databases || [],
          retrieval_config: {
            top_k: agentData.knowledge_config?.retrieval_params?.top_k || 3,
            similarity_threshold: agentData.knowledge_config?.retrieval_params?.similarity_threshold || 0.5
          }
        },
        mcp_config: {
          enabled: agentData.tools_config?.mcp_servers?.length > 0,
          servers: agentData.tools_config?.mcp_servers || []
        }
      }
      console.log('映射后的表单数据:', form.value)
    } else {
      message.error(response.message || '加载智能体数据失败')
    }
  } catch (error) {
    console.error('加载智能体数据失败:', error)
    message.error('加载智能体数据失败')
  } finally {
    loading.value = false
  }
}

// 加载知识库列表
const loadKnowledgeBases = async () => {
  try {
    knowledgeLoading.value = true
    const response = await axios.get('/api/knowledge/list')
    knowledgeList.value = response.data.map(item => ({
      ...item,
      key: item.db_id
    }))
    console.log('Knowledge bases loaded:', knowledgeList.value)
  } catch (error) {
    console.error('Failed to load knowledge bases:', error)
    if (error.message && error.message.includes('权限')) {
      message.warning('您没有权限访问知识库管理功能，请联系管理员')
      knowledgeList.value = []
    } else {
      message.error('加载知识库列表失败')
      knowledgeList.value = []
    }
  } finally {
    knowledgeLoading.value = false
  }
}

// 加载MCP服务器列表
const loadMCPServers = async () => {
  try {
    const response = await mcpConfigApi.getServers()
    console.log('MCP服务器API响应:', response)

    if (response.success && response.data?.servers) {
      // 将服务器对象转换为数组格式
      const servers = Object.entries(response.data.servers).map(([serverName, serverData]) => {
        // 创建带有必要属性的服务器对象
        return {
          key: serverName, // 添加key属性作为唯一标识
          name: serverName,
          description: serverData.description || 'MCP服务器',
          enabled: serverData.enabled || false,
          tools_count: serverData.tools ? Object.keys(serverData.tools).length : 0,
          tools: serverData.tools || {},
          config: serverData.config || {},
          is_external: serverData.is_external || false
        };
      });

      console.log('处理后的MCP服务器列表:', servers)
      // 确保服务器列表有数据
      if (servers && servers.length > 0) {
        mcpServerList.value = servers
        filteredMCPServerList.value = servers
      } else {
        console.warn('服务器列表为空')
        // 添加测试数据以确保表格正常显示
        const testServers = [
          { key: 'test1', name: 'test1', description: '测试服务器1', enabled: true, tools_count: 5, is_external: false },
          { key: 'test2', name: 'test2', description: '测试服务器2', enabled: true, tools_count: 3, is_external: true }
        ];
        mcpServerList.value = testServers
        filteredMCPServerList.value = testServers
      }
    } else {
      console.warn('未获取到MCP服务器数据')
      // 添加测试数据以确保表格正常显示
      const testServers = [
        { key: 'test1', name: 'test1', description: '测试服务器1', enabled: true, tools_count: 5, is_external: false },
        { key: 'test2', name: 'test2', description: '测试服务器2', enabled: true, tools_count: 3, is_external: true }
      ];
      mcpServerList.value = testServers
      filteredMCPServerList.value = testServers
    }
  } catch (error) {
    console.error('加载MCP服务器列表失败:', error)
    message.error('加载MCP服务器列表失败')
    mcpServerList.value = []
    filteredMCPServerList.value = []
  }
}

// 搜索MCP服务器
const searchMCPServers = () => {
  if (!mcpSearchKeyword.value) {
    filteredMCPServerList.value = mcpServerList.value
  } else {
    const keyword = mcpSearchKeyword.value.toLowerCase()
    filteredMCPServerList.value = mcpServerList.value.filter(server =>
      server.name.toLowerCase().includes(keyword) ||
      server.description.toLowerCase().includes(keyword) ||
      server.tools_count.toString().includes(keyword)
    )
  }
}

// 移除MCP服务器
const removeMCPServer = (serverName) => {
  const index = form.value.mcp_config.servers.indexOf(serverName)
  if (index > -1) {
    form.value.mcp_config.servers.splice(index, 1)
  }
}

// 处理模型选择
const handleModelSelect = (modelInfo) => {
  form.value.model_config.provider = modelInfo.provider
  form.value.model_config.model = modelInfo.name
  console.log('Model selected:', modelInfo)
}

// 打开模型配置弹窗
const openModelConfigModal = () => {
  tempModelConfig.value = {
    max_tokens: form.value.model_config.config.max_tokens,
    temperature: form.value.model_config.config.temperature,
    top_p: form.value.model_config.config.top_p
  }
  showModelConfigModal.value = true
}

// 保存模型配置
const handleModelConfigSave = () => {
  form.value.model_config.config.max_tokens = tempModelConfig.value.max_tokens
  form.value.model_config.config.temperature = tempModelConfig.value.temperature
  form.value.model_config.config.top_p = tempModelConfig.value.top_p
  showModelConfigModal.value = false
  message.success('模型配置已保存')
}

// 取消模型配置
const handleModelConfigCancel = () => {
  showModelConfigModal.value = false
}

// 打开知识库选择弹窗
const openKnowledgeModal = () => {
  showKnowledgeModal.value = true
}

// 获取知识库名称
const getKnowledgeName = (dbId) => {
  const db = knowledgeList.value.find(item => item.db_id === dbId)
  return db ? db.name : '未知知识库'
}

// 配置特定知识库
const configureKnowledge = (dbId) => {
  currentEditingKnowledge.value = dbId
  openKnowledgeConfigModal()
}

// 移除知识库
const removeKnowledge = (dbId) => {
  form.value.knowledge_config.databases = form.value.knowledge_config.databases.filter(id => id !== dbId)
  if (form.value.knowledge_config.databases.length === 0) {
    form.value.knowledge_config.enabled = false
  }
  message.success('已移除知识库')
}

// 保存知识库选择
const handleKnowledgeSelect = (selectedItems) => {
  form.value.knowledge_config.databases = selectedItems.map(item => item.db_id)
  selectedKnowledgeBases.value = selectedItems
  if (selectedItems.length > 0) {
    form.value.knowledge_config.enabled = true
  }
  showKnowledgeModal.value = false
}

// 取消知识库选择
const handleKnowledgeCancel = () => {
  showKnowledgeModal.value = false
}

// 打开知识库配置弹窗
const openKnowledgeConfigModal = () => {
  // 如果是编辑特定知识库，可以在这里加载特定配置
  // 目前使用全局配置
  tempKnowledgeConfig.value = {
    top_k: form.value.knowledge_config.retrieval_config.top_k,
    similarity_threshold: form.value.knowledge_config.retrieval_config.similarity_threshold,
    dynamic_file_parsing: form.value.knowledge_config.dynamic_file_parsing || false,
    web_search: form.value.knowledge_config.web_search || false,
    example_library: form.value.knowledge_config.example_library
  }
  showKnowledgeConfigModal.value = true
}

// 保存知识库配置
const handleKnowledgeConfigSave = (payload) => {
  // 更新所有知识库的检索配置
  form.value.knowledge_config.retrieval_config = payload.config
  showKnowledgeConfigModal.value = false
  message.success('知识库配置已保存')
}

// 取消知识库配置
const handleKnowledgeConfigCancel = () => {
  showKnowledgeConfigModal.value = false
  currentEditingKnowledge.value = null
}

// 打开MCP服务器选择弹窗
const openMCPSkillModal = () => {
  console.log('Opening MCP modal, current servers:', mcpServerList.value)
  console.log('Current form MCP servers:', form.value.mcp_config.servers)
  selectedMCPKeys.value = [...form.value.mcp_config.servers]
  mcpSearchKeyword.value = ''
  filteredMCPServerList.value = mcpServerList.value
  console.log('Filtered MCP server list:', filteredMCPServerList.value)
  showMCPSkillModal.value = true
}

// MCP服务器选择变化
const onMCPSelectionChange = (selectedRowKeys) => {
  console.log('MCP selection changed:', selectedRowKeys)
  selectedMCPKeys.value = selectedRowKeys
}

// 保存MCP服务器选择
const handleMCPSkillSelect = () => {
  console.log('Saving MCP selection:', selectedMCPKeys.value)
  form.value.mcp_config.servers = [...selectedMCPKeys.value]
  form.value.mcp_config.enabled = selectedMCPKeys.value.length > 0
  showMCPSkillModal.value = false
  message.success('MCP服务器选择已保存')
}

// 取消MCP服务器选择
const handleMCPSkillCancel = () => {
  showMCPSkillModal.value = false
}

// 预览知识库
const previewKnowledge = (record) => {
  message.info(`预览知识库: ${record.name}`)
  // TODO: 实现知识库预览功能
}

// 预览MCP服务器
const previewMCPSkill = (record) => {
  message.info(`预览MCP服务器: ${record.name}`)
  // TODO: 实现MCP服务器预览功能
}

// 检查服务器是否已选择
const isServerSelected = (serverName) => {
  return form.value.mcp_config.servers.includes(serverName)
}

// 获取服务器显示名称
const getServerDisplayName = (serverName) => {
  // 从MCP服务器列表中查找
  const serverFromList = mcpServerList.value.find(item => item.name === serverName)
  return serverFromList?.name || serverName
}

// 获取服务器显示描述
const getServerDisplayDescription = (serverName) => {
  // 从MCP服务器列表中查找
  const serverFromList = mcpServerList.value.find(item => item.name === serverName)
  return serverFromList?.description || '暂无描述'
}

// 获取服务器显示工具数量
const getServerDisplayToolsCount = (serverName) => {
  // 从MCP服务器列表中查找
  const serverFromList = mcpServerList.value.find(item => item.name === serverName)
  return serverFromList?.tools_count || 0
}

// 获取服务器是否外部
const getServerIsExternal = (serverName) => {
  const server = mcpServerList.value.find(item => item.name === serverName)
  return server?.is_external || false
}


onMounted(async () => {
  // 先加载系统配置
  await configStore.refreshConfig()
  console.log('Config loaded:', configStore.config)

  // 清除可能的缓存，确保获取最新数据
  await loadAgentData()

  try {
    console.log('Loading MCP servers...')
    await loadMCPServers()
    console.log('MCP servers loaded, count:', mcpServerList.value.length)
    console.log('MCP servers:', mcpServerList.value)
  } catch (error) {
    console.error('Error loading MCP servers:', error)
  }

  try {
    await loadKnowledgeBases()
  } catch (error) {
    console.error('Error loading knowledge bases:', error)
  }

  // 确保指令步骤展开，其他步骤折叠
  stepStates.value = {
    instruction: true,
    knowledge: false,
    skills: false
  }
})

const onSave = async () => {
  try {
    // 表单验证
    await formRef.value.validate()

    saving.value = true

    // 构建保存数据，映射表单数据到后端API格式
    const saveData = {
      name: form.value.name,
      description: form.value.description,
      system_prompt: form.value.system_prompt,
      provider: form.value.model_config.provider,
      model_name: form.value.model_config.model,
      model_parameters: {
        max_tokens: form.value.model_config.config.max_tokens,
        temperature: form.value.model_config.config.temperature,
        top_p: form.value.model_config.config.top_p
      },
      knowledge_databases: form.value.knowledge_config.enabled ? form.value.knowledge_config.databases : [],
      retrieval_params: form.value.knowledge_config.retrieval_config,
      mcp_servers: form.value.mcp_config.enabled ? form.value.mcp_config.servers : [], // <--- 修改字段名
      tools: [] // 暂时为空，后续根据需要添加
    };

    console.log('=== 保存智能体配置 ===')
    console.log('Agent ID:', agentId.value)
    console.log('当前表单数据:', form.value)
    console.log('发送的保存数据:', saveData)

    const response = await updateAgent(agentId.value, saveData)
    console.log('API响应:', response)

    if (response.success) {
      message.success('保存成功')
      // 清除agent store的缓存，确保数据同步
      agentStore.clearCache('agents')
      // 保存成功后重新加载数据以确保数据同步
      await loadAgentData()
      console.log('保存后重新加载的数据:', form.value)
    } else {
      console.error('保存失败，响应:', response)
      message.error(response.message || '保存失败')
    }
  } catch (error) {
    console.error('保存过程中的错误:', error)
    if (error.errorFields) {
      // 表单验证失败
      message.error('请检查表单输入')
    } else {
      console.error('保存失败:', error)
      message.error('保存失败')
    }
  } finally {
    saving.value = false
  }
}
</script>

<style lang="less" scoped>
.agent-edit-view {
  padding: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.edit-container {
  display: flex;
  flex: 1;
  min-height: 0;
}

.left-panel {
  width: 50%;
  border-right: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
  background: #fafbfc;
}

.config-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.right-panel {
  width: 50%;
  display: flex;
  flex-direction: column;
  background: white;
}

.chat-header {
  padding: 16px 24px;
  border-bottom: 1px solid #f0f0f0;
  background: white;

  h3 {
    margin: 0 0 4px 0;
    font-size: 16px;
    font-weight: 600;
    color: #262626;
  }

  p {
    margin: 0;
    font-size: 14px;
    color: #8c8c8c;
  }
}

.chat-content {
  flex: 1;
  min-height: 0;
  overflow: hidden;

  :deep(.chat-container) {
    height: 100%;
  }

  :deep(.chat) {
    height: 100%;
    overflow: hidden;
  }

  :deep(.chat-box) {
    flex: 1;
    overflow-y: auto;
  }

  :deep(.bottom) {
    position: sticky;
    bottom: 0;
    background-color: #fff;
    border-left: 1px solid #f0f0f0;
  }
}

.main-content {
  flex: 1;
  overflow: auto;
  padding: 0;
}

.tab-content {
  height: 100%;
}

.custom-tab-switch {
  display: flex;
  justify-content: center;
  align-items: center;
}

.tab-container {
  display: flex;
  background: rgba(0, 0, 0, 0.04);
  border-radius: 12px;
  padding: 3px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.tab-item {
  position: relative;
  padding: 8px 24px;
  min-width: 100px;
  text-align: center;
  cursor: pointer;
  font-size: 15px;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.65);
  border-radius: 10px;
  transition: all 0.3s ease;
  margin: 0 2px;
  user-select: none;
}

.tab-item:hover {
  color: #1890ff;
}

.tab-item.active {
  color: #1890ff;
  background: white;
  box-shadow: 0 2px 6px rgba(24, 144, 255, 0.15);
}

.tab-item span {
  position: relative;
  z-index: 2;
}

.form-item-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.label-actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.selected-mcp-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
  margin-bottom: 12px;
}

.mcp-tag {
  margin-right: 0;
  padding: 4px 8px;
  border-radius: 4px;
  background-color: #f0f5ff;
  border-color: #d6e4ff;
  color: #1890ff;
  font-size: 13px;
}

.edit-steps {
  margin-bottom: 24px;

  :deep(.ant-steps-item) {
    cursor: pointer;

    &:hover {
      .ant-steps-item-title {
        color: #1890ff;
      }
    }

    // 展开状态的高亮样式
    &.expanded {
      .ant-steps-item-title {
        color: #1890ff;
        font-weight: 600;
      }

      .ant-steps-item-icon {
        background-color: #1890ff;
        border-color: #1890ff;

        .ant-steps-icon {
          color: white;
        }
      }

      .ant-steps-item-tail {
        background-color: #1890ff;
      }
    }
  }

  :deep(.ant-steps-item-title) {
    width: 100%;
    padding-right: 0;
    cursor: pointer;
  }

  :deep(.ant-steps-item-container) {
    cursor: pointer;
  }
}

.step-title-wrapper {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  cursor: pointer;
  padding: 4px 0;
  transition: color 0.3s ease;

  &:hover {
    color: #1890ff;
  }

  .step-toggle-icon {
    font-size: 12px;
    color: #8c8c8c;
    transition: transform 0.3s ease;
    margin-left: auto;
    flex-shrink: 0;
  }
}

.step-content {
  padding: 12px;
  background: white;
  border-radius: 4px;
  border: 1px solid #f0f0f0;
  margin-top: 8px;
  position: relative;
  z-index: 5;
}

.section {
  margin-bottom: 16px;
}

.section-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;

  .section-left {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .section-right {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

.section-action {
  color: #8c8c8c;
  font-size: 13px;
}

.prompt-info {
  text-align: right;
  color: #bfbfbf;
  font-size: 12px;
  margin-top: 2px;
}

.retrieval-config {
  margin-top: 12px;
  padding: 12px;
  background: #fafafa;
  border-radius: 4px;
  border: 1px solid #f0f0f0;
}

.mcp-skills-list {
  margin-top: 8px;
}

.mcp-skills-list .section-row {
  padding: 4px 0;
  border-bottom: 1px solid #f0f0f0;
}

.mcp-skills-list .section-row:last-child {
  border-bottom: none;
}

.model-config-section {
  .model-selector-wrapper {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 8px;
    position: relative;
    z-index: 10;

    .config-label {
      font-size: 14px;
      color: #262626;
      font-weight: 500;
      min-width: 80px;
    }

    .config-btn {
      margin-left: auto;
      color: #1890ff;

      &:hover {
        color: #40a9ff;
      }
    }
  }
}

.model-config-modal {
  .current-model-info {
    padding: 8px 12px;
    background: #f5f5f5;
    border-radius: 4px;
    border: 1px solid #d9d9d9;

    .model-name {
      font-weight: 500;
      color: #262626;
    }

    .model-provider {
      color: #8c8c8c;
      margin-left: 4px;
    }
  }
}

.knowledge-modal {
  .ant-table-wrapper {
    border-radius: 4px;
    overflow: hidden;
  }

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

.knowledge-list-container {
  margin-top: 8px;

  .empty-knowledge {
    text-align: center;
    color: #999;
    padding: 16px 0;
  }

  .knowledge-item-list {
    display: flex;
    flex-direction: column;
    gap: 8px;

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
  }
}

.knowledge-config-modal {
  .ant-form-item {
    margin-bottom: 12px;
  }
}

.mcp-skill-modal {
  .search-section {
    margin-bottom: 12px;
  }

  .ant-table-wrapper {
    border-radius: 4px;
    overflow: hidden;
  }
}

.skill-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;

  span {
    flex: 1;
  }
}

.form-item-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;

  .label-actions {
    display: flex;
    align-items: center;
    gap: 0;
  }
}

/* 响应式设计 */
@media (max-width: 1200px) {

  .left-panel,
  .right-panel {
    width: 50%;
  }
}

@media (max-width: 768px) {
  .edit-container {
    flex-direction: column;
  }

  .left-panel,
  .right-panel {
    width: 100%;
  }

  .left-panel {
    height: 50vh;
  }

  .right-panel {
    height: 50vh;
  }
}
</style>