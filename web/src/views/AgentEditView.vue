<template>
  <div class="agent-edit-view layout-container">
    <!-- 页面头部 -->
    <HeaderComponent 
      title="编辑智能体" 
      :loading="loading"
      :show-back-button="true"
      :show-save-button="true"
      :saving="saving"
      @back="goBack"
      @save="onSave"
    />

    <div class="edit-container">
      <!-- 左侧配置区域 -->
      <div class="left-panel">
        <div class="config-content">
          <a-steps direction="vertical" :current="0" class="edit-steps" progressDot>
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
                    <a-form ref="formRef" layout="vertical" :model="form" :rules="formRules" @submit.prevent="onSave">
                      <a-form-item label="系统提示词" name="system_prompt">
                        <a-textarea v-model:value="form.system_prompt" :maxlength="30720" :auto-size="{ minRows: 4, maxRows: 8 }" placeholder="请输入系统提示词，定义智能体的行为和能力" />
                        <div class="prompt-info">{{ form.system_prompt.length }} / 30720</div>
                      </a-form-item>
                        <div class="model-config-section">
                          <div class="model-selector-wrapper">
                            <span class="config-label">选择模型:</span>
                            <ModelSelectorComponent 
                              :model_name="form.model_config.model" 
                              :model_provider="form.model_config.provider"
                              @select-model="handleModelSelect"
                            />
                            <a-button 
                              type="link" 
                              size="small" 
                              @click="openModelConfigModal"
                              class="config-btn"
                            >
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
                      <span>知识库</span>
                      <a-switch v-model:checked="form.knowledge_config.enabled" size="small" style="margin-left: 8px; margin-right: 8px;" />
                      <span class="section-action">{{ form.knowledge_config.databases.length }}/{{ knowledgeList.length }}</span>
                      <a-button type="link" size="small">+ 知识库</a-button>
                      <a-button type="link" size="small">配置</a-button>
                    </div>
                    <a-form-item v-if="form.knowledge_config.enabled">
                      <a-select v-model:value="form.knowledge_config.databases" mode="multiple" placeholder="选择知识库">
                        <a-select-option v-for="item in knowledgeList" :key="item.id" :value="item.id">{{ item.name }}</a-select-option>
                      </a-select>
                    </a-form-item>
                    <div v-if="form.knowledge_config.enabled && form.knowledge_config.databases.length > 0" class="retrieval-config">
                      <a-row :gutter="16">
                        <a-col :span="12">
                          <a-form-item label="检索数量">
                            <a-input-number v-model:value="form.knowledge_config.retrieval_config.top_k" :min="1" :max="20" style="width: 100%" />
                          </a-form-item>
                        </a-col>
                        <a-col :span="12">
                          <a-form-item label="相似度阈值">
                            <a-slider v-model:value="form.knowledge_config.retrieval_config.similarity_threshold" :min="0" :max="1" :step="0.1" :tooltip-formatter="(val) => `${val}`" />
                          </a-form-item>
                        </a-col>
                      </a-row>
                    </div>
                    <div class="section-row">
                      <span>动态文件解析</span>
                      <a-switch v-model:checked="form.knowledge_config.dynamic_file_parsing" size="small" style="margin-left: 8px;" />
                    </div>
                    <div class="section-row">
                      <span>联网搜索</span>
                      <a-switch v-model:checked="form.knowledge_config.web_search" size="small" style="margin-left: 8px; margin-right: 8px;" />
                      <a-button type="link" size="small">?</a-button>
                    </div>
                    <div class="section-row">
                      <span>样例库</span>
                      <a-switch v-model:checked="form.knowledge_config.example_library" size="small" style="margin-left: 8px;" />
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
                      <span>MCP服务</span>
                      <a-switch v-model:checked="form.mcp_config.enabled" size="small" style="margin-left: 8px; margin-right: 8px;" />
                      <span class="section-action">{{ form.mcp_config.skills.length }}/{{ mcpList.length }}</span>
                      <a-button type="link" size="small">+ MCP</a-button>
                    </div>
                    <a-form-item v-if="form.mcp_config.enabled">
                      <a-select v-model:value="form.mcp_config.skills" mode="multiple" placeholder="选择MCP服务">
                        <a-select-option v-for="item in mcpList" :key="item.id" :value="item.id">{{ item.name }}</a-select-option>
                      </a-select>
                    </a-form-item>
                    <div v-if="form.mcp_config.enabled && form.mcp_config.skills.length > 0" class="mcp-skills-list">
                      <div v-for="skillId in form.mcp_config.skills" :key="skillId" class="section-row">
                        <span style="margin-left: 24px;">{{ mcpList.find(item => item.id === skillId)?.name || skillId }}</span>
                        <span class="section-action">{{ mcpList.find(item => item.id === skillId)?.category || '未知' }}</span>
                        <a-button type="link" size="small" style="margin-left: 8px;" @click="removeMCPSkill(skillId)">🗑</a-button>
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
          <SimpleAgentChat 
            :agent-id="agentId" 
            :config="{}"
            :state="{}"
          />
        </div>
      </div>
    </div>

    <!-- 模型配置弹窗 -->
    <a-modal
      v-model:open="showModelConfigModal"
      title="模型推理参数配置"
      width="600px"
      @ok="handleModelConfigSave"
      @cancel="handleModelConfigCancel"
    >
      <div class="model-config-modal">
        <a-form layout="vertical" :model="tempModelConfig">
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="最大Token数">
                <a-input-number 
                  v-model:value="tempModelConfig.max_tokens" 
                  :min="100" 
                  :max="8000" 
                  style="width: 100%"
                  placeholder="请输入最大token数"
                />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="Temperature">
                <a-slider 
                  v-model:value="tempModelConfig.temperature" 
                  :min="0" 
                  :max="2" 
                  :step="0.1" 
                  :tooltip-formatter="(val) => `${val}`"
                />
                <div style="text-align: center; font-size: 12px; color: #8c8c8c; margin-top: 4px;">
                  {{ tempModelConfig.temperature }}
                </div>
              </a-form-item>
            </a-col>
          </a-row>
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="Top P">
                <a-slider 
                  v-model:value="tempModelConfig.top_p" 
                  :min="0" 
                  :max="1" 
                  :step="0.1" 
                  :tooltip-formatter="(val) => `${val}`"
                />
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
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { DownOutlined, UpOutlined, SettingOutlined } from '@ant-design/icons-vue'
import SimpleAgentChat from '@/components/agent/SimpleAgentChat.vue'
import HeaderComponent from '@/components/HeaderComponent.vue'
import ModelSelectorComponent from '@/components/model/ModelSelectorComponent.vue'
import { getAgent, updateAgent } from '@/apis/agent_api'
import { knowledgeBaseApi } from '@/apis/admin_api'
import { templateAPI } from '@/apis/template_api'
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

// 步骤状态管理
const stepStates = ref({
  instruction: true,  // 指令步骤默认展开
  knowledge: false,
  skills: false
})

const activeStep = ref('instruction')

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
const form = ref({
  system_prompt: '',
  model_config: {
    model: 'gpt-3.5-turbo',
    provider: 'openai',
    max_tokens: 2000,
    temperature: 0.7,
    top_p: 1.0
  },
  knowledge_config: {
    enabled: true,
    databases: [],
    retrieval_config: {
      top_k: 5,
      similarity_threshold: 0.7
    },
    dynamic_file_parsing: false,
    web_search: true,
    example_library: false
  },
  mcp_config: {
    enabled: true,
    skills: []
  },
  tools_config: []
})

const knowledgeList = ref([])
const mcpList = ref([])
const saving = ref(false)
const formRef = ref()

// 模型配置弹窗相关
const showModelConfigModal = ref(false)
const tempModelConfig = ref({
  max_tokens: 2000,
  temperature: 0.7,
  top_p: 1.0
})

// 表单验证规则
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
      console.log('加载到的智能体数据:', agentData)
      
      // 映射后端数据到表单结构
      form.value = {
        system_prompt: agentData.system_prompt || '',
        model_config: {
          model: agentData.model_config?.model || 'gpt-3.5-turbo',
          provider: agentData.model_config?.provider || 'openai',
          max_tokens: agentData.model_config?.max_tokens || 2000,
          temperature: agentData.model_config?.temperature || 0.7,
          top_p: agentData.model_config?.top_p || 1.0
        },
        knowledge_config: {
          enabled: agentData.knowledge_config?.enabled !== false,
          databases: agentData.knowledge_config?.databases || [],
          retrieval_config: {
            top_k: agentData.knowledge_config?.retrieval_config?.top_k || 5,
            similarity_threshold: agentData.knowledge_config?.retrieval_config?.similarity_threshold || 0.7
          },
          dynamic_file_parsing: agentData.knowledge_config?.dynamic_file_parsing || false,
          web_search: agentData.knowledge_config?.web_search !== false,
          example_library: agentData.knowledge_config?.example_library || false
        },
        mcp_config: {
          enabled: agentData.mcp_config?.enabled !== false,
          skills: agentData.mcp_config?.skills || []
        },
        tools_config: agentData.tools_config || []
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
    const response = await knowledgeBaseApi.getDatabases()
    if (response.databases) {
      knowledgeList.value = response.databases.map(db => ({
        id: db.db_id,
        name: db.name,
        description: db.description
      }))
    }
  } catch (error) {
    console.error('加载知识库列表失败:', error)
    // 非管理员用户可能无法访问知识库API，使用默认数据
    knowledgeList.value = [
      { id: 'kb1', name: '产品知识库', description: '产品相关信息' },
      { id: 'kb2', name: '技术文档库', description: '技术文档' },
      { id: 'kb3', name: '常见问题库', description: 'FAQ信息' }
    ]
  }
}

// 加载MCP技能列表
const loadMCPSkills = async () => {
  try {
    const response = await templateAPI.getMCPSkills()
    if (response.success && response.data?.skills) {
      mcpList.value = response.data.skills.map(skill => ({
        id: skill.skill_id,
        name: skill.name,
        description: skill.description,
        category: skill.category
      }))
    }
  } catch (error) {
    console.error('加载MCP技能列表失败:', error)
    // 使用默认数据
    mcpList.value = [
      { id: 'mcp1', name: 'Amap Maps', description: '高德地图服务', category: '地图' },
      { id: 'mcp2', name: 'Weather Service', description: '天气服务', category: '天气' },
      { id: 'mcp3', name: 'Calculator', description: '计算器服务', category: '工具' }
    ]
  }
}

// 移除MCP技能
const removeMCPSkill = (skillId) => {
  const index = form.value.mcp_config.skills.indexOf(skillId)
  if (index > -1) {
    form.value.mcp_config.skills.splice(index, 1)
  }
}

// 处理模型选择
const handleModelSelect = (modelInfo) => {
  form.value.model_config.model = modelInfo.name
  form.value.model_config.provider = modelInfo.provider
  console.log('Model selected:', modelInfo)
}

// 打开模型配置弹窗
const openModelConfigModal = () => {
  // 复制当前配置到临时变量
  tempModelConfig.value = {
    max_tokens: form.value.model_config.max_tokens,
    temperature: form.value.model_config.temperature,
    top_p: form.value.model_config.top_p
  }
  showModelConfigModal.value = true
}

// 保存模型配置
const handleModelConfigSave = () => {
  // 将临时配置应用到表单
  form.value.model_config.max_tokens = tempModelConfig.value.max_tokens
  form.value.model_config.temperature = tempModelConfig.value.temperature
  form.value.model_config.top_p = tempModelConfig.value.top_p
  showModelConfigModal.value = false
  message.success('模型配置已保存')
}

// 取消模型配置
const handleModelConfigCancel = () => {
  showModelConfigModal.value = false
}

onMounted(async () => {
  // 先加载系统配置
  await configStore.refreshConfig()
  console.log('Config loaded:', configStore.config)
  
  // 清除可能的缓存，确保获取最新数据
  await loadAgentData()
  await Promise.all([
    loadKnowledgeBases(),
    loadMCPSkills()
  ])
  
  // 调试：打印当前的步骤状态
  console.log('当前步骤状态:', stepStates.value)
  
  // 确保指令步骤展开，其他步骤折叠
  stepStates.value = {
    instruction: true,
    knowledge: false,
    skills: false
  }
  console.log('重置后的步骤状态:', stepStates.value)
})

const onSave = async () => {
  try {
    // 表单验证
    await formRef.value.validate()
    
    saving.value = true
    
    // 构建保存数据，映射表单数据到后端API格式
    const saveData = {
      system_prompt: form.value.system_prompt,
      model_config: form.value.model_config,
      knowledge_config: {
        enabled: form.value.knowledge_config.enabled,
        databases: form.value.knowledge_config.databases,
        retrieval_config: form.value.knowledge_config.retrieval_config,
        dynamic_file_parsing: form.value.knowledge_config.dynamic_file_parsing,
        web_search: form.value.knowledge_config.web_search,
        example_library: form.value.knowledge_config.example_library
      },
      mcp_config: {
        enabled: form.value.mcp_config.enabled,
        skills: form.value.mcp_config.skills
      },
      tools_config: form.value.tools_config
    }

    console.log('保存数据:', saveData)
    console.log('Agent ID:', agentId.value)
    
    const response = await updateAgent(agentId.value, saveData)
    console.log('保存响应:', response)
    
    if (response.success) {
      message.success('保存成功')
      // 清除agent store的缓存，确保数据同步
      agentStore.clearCache('agents')
      // 保存成功后重新加载数据以确保数据同步
      await loadAgentData()
    } else {
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
    background: white;
    border-top: 1px solid #f0f0f0;
  }
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
  margin-bottom: 8px;
  font-size: 14px;
}

.section-action {
  color: #8c8c8c;
  margin-left: 8px;
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