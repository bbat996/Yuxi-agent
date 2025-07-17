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
                                  :model_provider="form.model_config.provider" @select-model="handleModelSelect"
                                  class="model-selector-comp" />
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
                            <div class="section-left">
                              <span>知识库：</span>
                              <a-switch :checked="form.knowledge_config.enabled"
                                @update:checked="form.knowledge_config.enabled = $event" size="small" />
                            </div>
                            <div class="section-right">
                              <a-button v-if="form.knowledge_config.enabled" type="text" @click="openKnowledgeModal">+ 选择知识库</a-button>
                            </div>
                          </div>

                          <div v-if="form.knowledge_config.enabled" class="knowledge-list-container">
                            <div v-if="form.knowledge_config.databases.length === 0" class="empty-knowledge">
                              <p>暂无选择的知识库，请点击上方按钮选择</p>
                            </div>
                            <div v-else class="knowledge-item-list">
                              <ActionItem v-for="dbId in form.knowledge_config.databases" :key="dbId"
                                :name="getKnowledgeName(dbId)" @configure="configureKnowledge(dbId)"
                                @remove="removeKnowledge(dbId)" :icon="BookOutlined" />
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
                              <span>MCP服务：</span>
                              <a-switch :checked="form.mcp_config.enabled"
                                @update:checked="form.mcp_config.enabled = $event" size="small" />
                            </div>
                            <div class="section-right">
                              <span class="section-action">{{ form.mcp_config.servers.length }}/{{ mcpServerList.length
                              }}</span>
                              <a-button type="text" size="small" @click="openMCPSkillModal">
                                + MCP
                              </a-button>
                            </div>
                          </div>

                          <div v-if="form.mcp_config.enabled && form.mcp_config.servers.length > 0"
                            class="mcp-skills-list">
                            <ActionItem v-for="serverName in form.mcp_config.servers" :key="serverName"
                              :name="getServerDisplayName(serverName)" :show-configure="false"
                              @remove="removeMCPServer(serverName)" :icon="ThunderboltOutlined">
                              <template #extra>
                                <a-tag color="blue">{{ getServerDisplayToolsCount(serverName) }} 工具</a-tag>
                              </template>
                            </ActionItem>
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
    <KnowledgeSelector :modelValue="showKnowledgeModal" @update:modelValue="showKnowledgeModal = $event"
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
import { DownOutlined, UpOutlined, SettingOutlined, SearchOutlined, EditOutlined, FileTextOutlined, BulbOutlined, PlusOutlined, DeleteOutlined, BookOutlined, ThunderboltOutlined } from '@ant-design/icons-vue'
import SimpleAgentChat from '@/components/agent/SimpleAgentChat.vue'
import ActionItem from '@/components/common/ActionItem.vue'
import HeaderComponent from '@/components/HeaderComponent.vue'
import ModelSelectorComponent from '@/components/model/ModelSelectorComponent.vue'
import AgentModal from '@/components/agent/AgentModal.vue'
import KnowledgeSelector from '@/components/knowledge/KnowledgeSelector.vue'
import { KnowledgeConfig } from '@/components/knowledge'
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
const saving = ref(false);
const activeTab = ref('config');

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

// 模型配置弹窗
const showModelConfigModal = ref(false);
const tempModelConfig = ref({});

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
const currentKnowledgeId = ref(null)
const currentKnowledgeName = ref('')
const currentKnowledgeConfig = ref({})
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

const handleKnowledgeConfigSave = (config) => {
  // 在这里处理保存逻辑
  console.log('保存知识库配置:', config);
  showKnowledgeConfigModal.value = false;
};

const stepStates = ref({
  instruction: true,
  knowledge: true,
  skills: true
});

const activeStep = ref('instruction')

// 获取当前步骤的索引
const getCurrentStepIndex = () => {
  const stepOrder = ['instruction', 'knowledge', 'skills'];
  return stepOrder.indexOf(activeStep.value);
};

// 切换步骤展开/折叠状态
const toggleStep = (stepKey) => {
  stepStates.value[stepKey] = !stepStates.value[stepKey];
  if (stepStates.value[stepKey]) {
    activeStep.value = stepKey;
  }
};

const formRules = {
  system_prompt: [
    { required: true, message: '请输入系统提示词' },
    { min: 10, message: '系统提示词至少需要10个字符' }
  ]
};

const goBack = () => {
  router.back();
};

const loadAgentData = async () => {
  if (!agentId.value) return;
  try {
    loading.value = true;
    const response = await getAgent(agentId.value);
    if (response.success) {
      const agentData = response.data;
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
      };
    } else {
      message.error(response.message || '加载智能体数据失败');
    }
  } catch (error) {
    console.error('加载智能体数据失败:', error);
    message.error('加载智能体数据失败');
  } finally {
    loading.value = false;
  }
};

const loadKnowledgeBases = async () => {
  // ... (implementation details)
};

const loadMCPServers = async () => {
  try {
    const response = await mcpConfigApi.getServers();
    if (response.success && response.data?.servers) {
      const servers = Object.entries(response.data.servers).map(([serverName, serverData]) => ({
        key: serverName,
        name: serverName,
        description: serverData.description || 'MCP服务器',
        enabled: serverData.enabled || false,
        tools_count: serverData.tools ? Object.keys(serverData.tools).length : 0,
        tools: serverData.tools || {},
        config: serverData.config || {},
        is_external: serverData.is_external || false
      }));
      mcpServerList.value = servers;
      filteredMCPServerList.value = servers;
    }
  } catch (error) {
    console.error('加载MCP服务器列表失败:', error);
    message.error('加载MCP服务器列表失败');
  }
};

const searchMCPServers = () => {
  // ... (implementation details)
};

const removeMCPServer = (serverName) => {
  const index = form.value.mcp_config.servers.indexOf(serverName);
  if (index > -1) {
    form.value.mcp_config.servers.splice(index, 1);
  }
};

const handleModelSelect = (modelInfo) => {
  form.value.model_config.provider = modelInfo.provider;
  form.value.model_config.model = modelInfo.name;
};

const openModelConfigModal = () => {
  tempModelConfig.value = { ...form.value.model_config.config };
  showModelConfigModal.value = true;
};

const handleModelConfigSave = () => {
  form.value.model_config.config = { ...tempModelConfig.value };
  showModelConfigModal.value = false;
  message.success('模型配置已保存');
};

const handleModelConfigCancel = () => {
  showModelConfigModal.value = false;
};

const openKnowledgeModal = () => {
  showKnowledgeModal.value = true;
};

const getKnowledgeName = (dbId) => {
  const db = knowledgeList.value.find(item => item.db_id === dbId);
  return db ? db.name : '未知知识库';
};

const configureKnowledge = (dbId) => {
  const db = knowledgeList.value.find(item => item.db_id === dbId);
  if (db) {
    currentKnowledgeId.value = dbId;
    currentKnowledgeName.value = db.name;
    // 注意：这里的配置应该是和特定知识库关联的，但当前数据结构中配置是全局的。
    // 暂时使用全局配置来填充弹窗。
    currentKnowledgeConfig.value = { ...form.value.knowledge_config.retrieval_config };
    showKnowledgeConfigModal.value = true;
  } else {
    message.error('找不到指定的知识库');
  }
};

const removeKnowledge = (dbId) => {
  form.value.knowledge_config.databases = form.value.knowledge_config.databases.filter(id => id !== dbId);
  if (form.value.knowledge_config.databases.length === 0) {
    form.value.knowledge_config.enabled = false;
  }
  message.success('已移除知识库');
};

const handleKnowledgeSelect = (selectedItems) => {
  // ... (implementation details)
};

const openMCPSkillModal = () => {
  selectedMCPKeys.value = [...form.value.mcp_config.servers];
  showMCPSkillModal.value = true;
};

const onMCPSelectionChange = (selectedRowKeys) => {
  selectedMCPKeys.value = selectedRowKeys;
};

const handleMCPSkillSelect = () => {
  form.value.mcp_config.servers = [...selectedMCPKeys.value];
  form.value.mcp_config.enabled = selectedMCPKeys.value.length > 0;
  showMCPSkillModal.value = false;
  message.success('MCP服务器选择已保存');
};

const handleMCPSkillCancel = () => {
  showMCPSkillModal.value = false;
};

const isServerSelected = (serverName) => {
  return form.value.mcp_config.servers.includes(serverName);
};

const getServerDisplayName = (serverName) => {
  const server = mcpServerList.value.find(item => item.name === serverName);
  return server?.name || serverName;
};

const getServerDisplayToolsCount = (serverName) => {
  const server = mcpServerList.value.find(item => item.name === serverName);
  return server?.tools_count || 0;
};

onMounted(async () => {
  await configStore.refreshConfig();
  await loadAgentData();
  await loadMCPServers();
  await loadKnowledgeBases();
});

const onSave = async () => {
  try {
    await formRef.value.validate();
    saving.value = true;
    const saveData = {
      name: form.value.name,
      description: form.value.description,
      system_prompt: form.value.system_prompt,
      provider: form.value.model_config.provider,
      model_name: form.value.model_config.model,
      model_parameters: form.value.model_config.config,
      knowledge_databases: form.value.knowledge_config.enabled ? form.value.knowledge_config.databases : [],
      retrieval_params: form.value.knowledge_config.retrieval_config,
      mcp_skills: form.value.mcp_config.enabled ? form.value.mcp_config.servers : [],
      tools: []
    };
    const response = await updateAgent(agentId.value, saveData);
    if (response.success) {
      message.success('保存成功');
      agentStore.clearCache('agents');
      await loadAgentData();
    } else {
      message.error(response.message || '保存失败');
    }
  } catch (error) {
    message.error('保存失败');
  } finally {
    saving.value = false;
  }
};
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
}

.tab-item {
  padding: 8px 24px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.65);
  border-radius: 10px;
  transition: all 0.3s ease;

  &.active {
    color: #1890ff;
    background: white;
  }
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
}

.edit-steps {
  :deep(.ant-steps-item-title) {
    width: 100%;
  }
}

.step-title-wrapper {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.step-content {
  padding: 12px;
  background: white;
  border-radius: 4px;
  border: 1px solid #f0f0f0;
  margin-top: 8px;
}

.section-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.prompt-info {
  text-align: right;
  color: #bfbfbf;
  font-size: 12px;
}

.model-config-section {
  .model-selector-wrapper {
    display: flex;
    align-items: center;
    gap: 8px;

    .model-selector-comp {
      min-width: 220px;
    }
  }
}

.knowledge-list-container {
  margin-top: 8px;
}

.knowledge-item-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mcp-skills-list {
  margin-top: 8px;
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