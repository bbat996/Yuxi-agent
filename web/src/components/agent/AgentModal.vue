<template>
  <a-modal
    :visible="modalVisible"
    :title="modalTitle"
    :width="modalWidth"
    :confirm-loading="loading"
    :destroy-on-close="true"
    @ok="handleSubmit"
    @cancel="handleCancel"
    @update:visible="emit('update:visible', $event)"
  >
    <a-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      layout="vertical"
      class="agent-form"
    >
      <!-- 基础信息 -->
      <div class="form-section">
        <h4 class="section-title">基础信息</h4>
        
        <!-- 头像上传区域 -->
        <a-form-item label="头像">
          <div class="avatar-upload-section">
            <div class="avatar-preview">
              <a-avatar :size="80" :src="avatarPreview || formData.avatar || undefined">
                <template #icon v-if="!avatarPreview && !formData.avatar">
                  <RobotOutlined />
                </template>
              </a-avatar>
            </div>
            <div class="avatar-upload">
              <a-upload
                v-model:fileList="avatarFileList"
                name="avatar"
                :max-count="1"
                :before-upload="beforeAvatarUpload"
                :show-upload-list="false"
                accept="image/*"
              >
                <a-button type="dashed">
                  <template #icon><UploadOutlined /></template>
                  上传头像
                </a-button>
              </a-upload>
              <div class="upload-hint">
                支持 JPG、PNG 格式，建议尺寸 200x200 像素
              </div>
            </div>
          </div>
        </a-form-item>
        
        <a-form-item label="名称" name="name" required>
          <a-input 
            v-model:value="formData.name" 
            placeholder="输入智能体名称"
            :maxlength="50"
            show-count
          />
        </a-form-item>

        <a-form-item label="描述" name="description">
          <a-textarea 
            v-model:value="formData.description" 
            placeholder="输入描述（可选，最多200字）"
            :maxlength="200"
            :auto-size="{ minRows: 3, maxRows: 6 }"
            show-count
          />
        </a-form-item>

        <a-form-item label="类型" name="agent_type">
          <a-select v-model:value="formData.agent_type" disabled>
            <a-select-option value="chatbot">对话智能体</a-select-option>
          </a-select>
        </a-form-item>
      </div>

      <!-- 仅在创建模式下显示其他配置 -->
      <template v-if="mode === 'create'">
        <!-- 系统提示词 -->
        <div class="form-section">
          <h4 class="section-title">
            系统提示词
            <a-tooltip title="智能体的基础行为指令">
              <QuestionCircleOutlined class="help-icon" />
            </a-tooltip>
          </h4>
          
          <a-form-item name="system_prompt">
            <div class="prompt-editor">
              <div class="prompt-toolbar">
                <a-button-group size="small">
                  <a-button @click="showTemplateSelector = true">
                    <template #icon><AppstoreOutlined /></template>
                    选择模板
                  </a-button>
                  <a-button @click="insertVariable">
                    <template #icon><TagOutlined /></template>
                    插入变量
                  </a-button>
                </a-button-group>
              </div>
              <a-textarea 
                v-model:value="formData.system_prompt"
                placeholder="请输入系统提示词，定义智能体的角色和行为..."
                :rows="6"
                class="prompt-textarea"
              />
            </div>
          </a-form-item>
        </div>

        <!-- 模型配置 -->
        <div class="form-section">
          <h4 class="section-title">模型配置</h4>
          
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="提供商" name="provider">
                <a-select 
                  :model-value="formData.llm_config.provider"
                  @update:model-value="val => formData.llm_config.provider = val"
                  placeholder="选择提供商"
                  show-search
                  @change="handleProviderChange"
                >
                  <a-select-option value="openai">OpenAI</a-select-option>
                  <a-select-option value="zhipu">智谱</a-select-option>
                  <a-select-option value="custom">自定义</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="模型" name="model">
                <a-select 
                  :model-value="formData.llm_config.model"
                  @update:model-value="val => formData.llm_config.model = val"
                  placeholder="选择模型"
                  show-search
                  @change="handleModelChange"
                >
                  <a-select-option value="gpt-4">GPT-4</a-select-option>
                  <a-select-option value="gpt-3.5-turbo">GPT-3.5 Turbo</a-select-option>
                  <a-select-option value="claude-3">Claude-3</a-select-option>
                  <a-select-option value="local-llm">本地模型</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
          </a-row>

          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="温度" name="temperature">
                <a-slider
                  :model-value="formData.llm_config.config.temperature"
                  @update:model-value="val => formData.llm_config.config.temperature = val"
                  :min="0"
                  :max="2"
                  :step="0.1"
                  :tooltip-formatter="(val) => `${val} (${getTemperatureLabel(val)})`"
                />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="最大回复长度">
                <a-input-number
                  :model-value="formData.llm_config.config.max_tokens"
                  @update:model-value="val => formData.llm_config.config.max_tokens = val"
                  :min="1"
                  :max="4000"
                  placeholder="最大回复长度"
                  style="width: 100%"
                />
              </a-form-item>
            </a-col>
          </a-row>

          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="Top P">
                <a-slider
                  :model-value="formData.llm_config.config.top_p"
                  @update:model-value="val => formData.llm_config.config.top_p = val"
                  :min="0"
                  :max="1"
                  :step="0.1"
                  :tooltip-formatter="(val) => `${val}`"
                />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="频率惩罚">
                <a-slider
                  :model-value="formData.llm_config.config.frequency_penalty"
                  @update:model-value="val => formData.llm_config.config.frequency_penalty = val"
                  :min="-2"
                  :max="2"
                  :step="0.1"
                  :tooltip-formatter="(val) => `${val}`"
                />
              </a-form-item>
            </a-col>
          </a-row>
        </div>

        <!-- 工具配置 -->
        <div class="form-section">
          <h4 class="section-title">
            工具配置
            <a-button type="link" size="small" @click="showToolSelector = true">
              <template #icon><PlusOutlined /></template>
              添加工具
            </a-button>
          </h4>
          
          <div class="tools-list">
            <div 
              v-for="(tool, index) in formData.tools" 
              :key="index"
              class="tool-item"
            >
              <div class="tool-info">
                <span class="tool-name">{{ tool }}</span>
              </div>
              <a-button 
                type="text" 
                size="small" 
                danger 
                @click="removeTool(index)"
              >
                <template #icon><DeleteOutlined /></template>
              </a-button>
            </div>
            
            <a-empty v-if="formData.tools.length === 0" :image="false" description="暂未配置工具">
              <a-button type="dashed" @click="showToolSelector = true">
                <template #icon><PlusOutlined /></template>
                添加工具
              </a-button>
            </a-empty>
          </div>
        </div>

        <!-- 知识库配置 -->
        <div class="form-section">
          <h4 class="section-title">知识库配置</h4>
          
          <a-form-item label="启用知识库">
            <a-switch 
              :model-value="formData.knowledge_config.enabled"
              @update:model-value="val => formData.knowledge_config.enabled = val"
            />
          </a-form-item>

          <template v-if="formData.knowledge_config.enabled">
            <a-form-item label="知识库">
              <a-select
                :model-value="formData.knowledge_config.databases"
                @update:model-value="val => formData.knowledge_config.databases = val"
                mode="multiple"
                placeholder="选择要关联的知识库"
                :loading="knowledgeLoading"
                @focus="loadKnowledgeBases"
              >
                <a-select-option 
                  v-for="kb in knowledgeBases" 
                  :key="kb.id" 
                  :value="kb.id"
                >
                  {{ kb.name }}
                </a-select-option>
              </a-select>
            </a-form-item>

            <a-row :gutter="16" v-if="formData.knowledge_config.databases.length > 0">
              <a-col :span="12">
                <a-form-item label="检索数量">
                  <a-input-number
                    :model-value="formData.knowledge_config.retrieval_config.top_k"
                    @update:model-value="val => formData.knowledge_config.retrieval_config.top_k = val"
                    :min="1"
                    :max="20"
                    placeholder="检索数量"
                    style="width: 100%"
                  />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="相似度阈值">
                  <a-slider
                    :model-value="formData.knowledge_config.retrieval_config.similarity_threshold"
                    @update:model-value="val => formData.knowledge_config.retrieval_config.similarity_threshold = val"
                    :min="0"
                    :max="1"
                    :step="0.1"
                    :tooltip-formatter="(val) => `${val}`"
                  />
                </a-form-item>
              </a-col>
            </a-row>
          </template>
        </div>

        <!-- MCP配置 -->
        <div class="form-section">
          <h4 class="section-title">MCP配置</h4>
          
          <a-form-item label="启用MCP服务">
            <a-switch 
              :model-value="formData.mcp_config.enabled"
              @update:model-value="val => formData.mcp_config.enabled = val"
            />
          </a-form-item>

          <template v-if="formData.mcp_config.enabled">
            <a-form-item label="MCP服务器">
              <a-select
                :model-value="formData.mcp_config.servers"
                @update:model-value="val => formData.mcp_config.servers = val"
                mode="multiple"
                placeholder="选择要使用的MCP服务器"
                :loading="mcpLoading"
                @focus="loadMcpServers"
              >
                <a-select-option 
                  v-for="server in mcpServers" 
                  :key="server.id" 
                  :value="server.id"
                >
                  {{ server.name }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </template>
        </div>
      </template>
    </a-form>

    <!-- 测试区域 - 仅在创建模式下显示 -->
    <div class="test-section" v-if="mode === 'create'">
      <a-divider>配置测试</a-divider>
      <div class="test-controls">
        <a-input
          v-model:value="testMessage"
          placeholder="输入测试消息..."
          @keyup.enter="handleTest"
        >
          <template #suffix>
            <a-button 
              type="link" 
              size="small" 
              @click="handleTest"
              :loading="testing"
            >
              测试
            </a-button>
          </template>
        </a-input>
      </div>
      <div class="test-result" v-if="testResult">
        <a-alert 
          :type="testResult.success ? 'success' : 'error'"
          :message="testResult.message"
          show-icon
        />
      </div>
    </div>

    <!-- 提示词模板选择器 -->
    <a-modal
      v-model:open="showTemplateSelector"
      title="选择提示词模板"
      width="600px"
      @ok="selectTemplate"
      @cancel="showTemplateSelector = false"
    >
      <div class="template-list">
        <a-radio-group v-model:value="selectedTemplate" style="width: 100%">
          <div v-for="template in promptTemplates" :key="template.id" class="template-item">
            <a-radio :value="template.id">
              <div class="template-info">
                <div class="template-name">{{ template.name }}</div>
                <div class="template-description">{{ template.description }}</div>
              </div>
            </a-radio>
          </div>
        </a-radio-group>
      </div>
    </a-modal>

    <!-- 工具选择器 -->
    <a-modal
      v-model:open="showToolSelector"
      title="选择工具"
      width="600px"
      @ok="selectTools"
      @cancel="showToolSelector = false"
    >
      <div class="tool-selector">
        <a-checkbox-group v-model:value="selectedTools" style="width: 100%">
          <div v-for="tool in availableTools" :key="tool.id" class="tool-option">
            <a-checkbox :value="tool.id">
              <div class="tool-option-info">
                <div class="tool-option-name">{{ tool.name }}</div>
                <div class="tool-option-description">{{ tool.description }}</div>
              </div>
            </a-checkbox>
          </div>
        </a-checkbox-group>
      </div>
    </a-modal>
  </a-modal>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  QuestionCircleOutlined,
  AppstoreOutlined,
  TagOutlined,
  PlusOutlined,
  DeleteOutlined,
  UploadOutlined,
  RobotOutlined
} from '@ant-design/icons-vue'
import { agentAPI } from '@/apis'

// Props
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  agent: {
    type: Object,
    default: null
  },
  mode: {
    type: String,
    default: 'create' // 'create' | 'edit'
  }
})

// Emits
const emit = defineEmits(['update:visible', 'success'])

// 响应式数据
const loading = ref(false)
const modalVisible = ref(false)
const formRef = ref()

const defaultFormData = {
  name: '',
  description: '',
  agent_type: 'custom',
  system_prompt: '',
  llm_config: {
    provider: 'openai',
    model: 'gpt-3.5-turbo',
    config: {
      temperature: 0.7,
      max_tokens: 2000,
      top_p: 0.9,
      frequency_penalty: 0,
      presence_penalty: 0
    }
  },
  tools: [],
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
  },
  avatar: null // 用于存储头像的URL
}

// 表单数据
const formData = ref({ ...defaultFormData })

// 如果是编辑模式，使用传入的agent数据初始化表单
if (props.mode === 'edit' && props.agent) {
  formData.value = {
    ...defaultFormData,
    ...props.agent,
    llm_config: {
      provider: props.agent.llm_config?.provider || defaultFormData.llm_config.provider,
      model: props.agent.llm_config?.model || defaultFormData.llm_config.model,
      config: {
        temperature: props.agent.llm_config?.config?.temperature || defaultFormData.llm_config.config.temperature,
        max_tokens: props.agent.llm_config?.config?.max_tokens || defaultFormData.llm_config.config.max_tokens,
        top_p: props.agent.llm_config?.config?.top_p || defaultFormData.llm_config.config.top_p,
        frequency_penalty: props.agent.llm_config?.config?.frequency_penalty || defaultFormData.llm_config.config.frequency_penalty,
        presence_penalty: props.agent.llm_config?.config?.presence_penalty || defaultFormData.llm_config.config.presence_penalty
      }
    },
    knowledge_config: {
      enabled: props.agent.knowledge_config?.enabled || defaultFormData.knowledge_config.enabled,
      databases: props.agent.knowledge_config?.databases || defaultFormData.knowledge_config.databases,
      retrieval_config: {
        top_k: props.agent.knowledge_config?.retrieval_config?.top_k || defaultFormData.knowledge_config.retrieval_config.top_k,
        similarity_threshold: props.agent.knowledge_config?.retrieval_config?.similarity_threshold || defaultFormData.knowledge_config.retrieval_config.similarity_threshold
      }
    },
    mcp_config: {
      enabled: props.agent.mcp_config?.enabled || defaultFormData.mcp_config.enabled,
      servers: props.agent.mcp_config?.servers || defaultFormData.mcp_config.servers
    }
  }
}

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入智能体名称', trigger: 'blur' },
    { min: 2, max: 50, message: '名称长度应在2-50个字符之间', trigger: 'blur' }
  ],
  description: [
    { max: 200, message: '描述不能超过200个字符', trigger: 'blur' }
  ],
  'llm_config.provider': [
    { required: true, message: '请选择模型提供商', trigger: 'change' }
  ],
  'llm_config.model': [
    { required: true, message: '请选择模型', trigger: 'change' }
  ]
}

// 其他数据
const testMessage = ref('')
const testing = ref(false)
const testResult = ref(null)

const showTemplateSelector = ref(false)
const selectedTemplate = ref('')
const promptTemplates = ref([])

const showToolSelector = ref(false)
const selectedTools = ref([])
const availableTools = ref([])

const knowledgeLoading = ref(false)
const knowledgeBases = ref([])

const mcpLoading = ref(false)
const mcpServers = ref([])

// 头像上传相关
const avatarFileList = ref([])
const avatarPreview = ref(null)

// 计算属性
const modalTitle = computed(() => {
  return props.mode === 'edit' ? '编辑智能体' : '创建智能体'
})

const modalWidth = computed(() => {
  return props.mode === 'edit' ? '600px' : '800px'
})

// 监听 visible 变化
watch(() => props.visible, (newVal) => {
  modalVisible.value = newVal
  if (newVal) {
    initForm()
  }
})

watch(modalVisible, (newVal) => {
  emit('update:visible', newVal)
})

// 初始化表单
const initForm = () => {
  if (props.mode === 'edit' && props.agent) {
    // 编辑模式，只填充基础字段
    Object.assign(formData, {
      name: props.agent.name || '',
      description: props.agent.description || '',
      agent_type: props.agent.agent_type || 'chatbot',
      avatar: props.agent.avatar || null
    })
    // 处理头像文件列表
    if (props.agent.avatar) {
      avatarFileList.value = [{
        uid: 'avatar',
        name: 'avatar',
        status: 'done',
        url: props.agent.avatar,
        thumbUrl: props.agent.avatar
      }]
      avatarPreview.value = props.agent.avatar
    }
  } else {
    // 创建模式，重置表单
    resetForm()
  }
  
  // 清空测试结果
  testResult.value = null
}

// 重置表单
const resetForm = () => {
  if (props.mode === 'edit') {
    // 编辑模式，只重置基础字段
    Object.assign(formData, {
      name: '',
      description: '',
      agent_type: 'chatbot',
      avatar: null
    })
  } else {
    // 创建模式，重置所有字段
    Object.assign(formData, {
      name: '',
      description: '',
      agent_type: 'custom',
      system_prompt: '',
      llm_config: {
        provider: 'openai',
        model: 'gpt-3.5-turbo',
        config: {
          temperature: 0.7,
          max_tokens: 2000,
          top_p: 0.9,
          frequency_penalty: 0
        }
      },
      tools: [],
      knowledge_config: {
        enabled: false,
        databases: [],
        retrieval_config: {
          top_k: 5,
          similarity_threshold: 0.7
        }
      },
      mcp_config: {
        enabled: false,
        servers: []
      },
      avatar: null
    })
  }
  avatarFileList.value = [] // 清空文件列表
  avatarPreview.value = null // 清空预览
}

// 温度标签
const getTemperatureLabel = (val) => {
  if (val <= 0.3) return '保守'
  if (val <= 0.7) return '平衡'
  if (val <= 1.2) return '创造'
  return '发散'
}

// 提供商变化处理
const handleProviderChange = (provider) => {
  // 根据提供商调整模型列表
  if (provider === 'openai') {
    formData.value.llm_config.model = 'gpt-3.5-turbo'
  } else if (provider === 'zhipu') {
    formData.value.llm_config.model = 'claude-3'
  } else if (provider === 'custom') {
    formData.value.llm_config.model = 'local-llm'
  }
}

// 模型变化处理
const handleModelChange = (model) => {
  // 根据模型调整默认参数
  if (model === 'gpt-4') {
    formData.value.llm_config.config.max_tokens = 3000
  } else if (model === 'gpt-3.5-turbo') {
    formData.value.llm_config.config.max_tokens = 2000
  }
}

// 移除工具
const removeTool = (index) => {
  formData.value.tools.splice(index, 1)
}

// 插入变量
const insertVariable = () => {
  const variables = ['{{user_name}}', '{{current_time}}', '{{context}}']
  // 简单实现，实际可以做成下拉选择
  const variable = variables[0]
  const textarea = document.querySelector('.prompt-textarea textarea')
  if (textarea) {
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const text = formData.value.system_prompt
    formData.value.system_prompt = text.substring(0, start) + variable + text.substring(end)
  }
}

// 加载知识库列表
const loadKnowledgeBases = async () => {
  if (knowledgeBases.value.length > 0) return
  
  try {
    knowledgeLoading.value = true
    // 调用API获取知识库列表
    // const response = await knowledgeAPI.getKnowledgeBases()
    // knowledgeBases.value = response.data || []
    
    // 模拟数据
    knowledgeBases.value = [
      { id: 'kb_1', name: '知识库1' },
      { id: 'kb_2', name: '知识库2' },
      { id: 'kb_3', name: '知识库3' }
    ]
  } catch (error) {
    console.error('加载知识库失败:', error)
  } finally {
    knowledgeLoading.value = false
  }
}

// 加载MCP服务器列表
const loadMcpServers = async () => {
  if (mcpServers.value.length > 0) return
  
  try {
    mcpLoading.value = true
    // 调用MCP API获取列表
    // const response = await mcpAPI.getMcpServers()
    // mcpServers.value = response.data || []
    
    // 模拟数据
    mcpServers.value = [
      { id: '1', name: 'MCP-1' },
      { id: '2', name: 'MCP-2' },
      { id: '3', name: 'MCP-3' }
    ]
  } catch (error) {
    console.error('加载MCP服务器失败:', error)
  } finally {
    mcpLoading.value = false
  }
}

// 选择模板
const selectTemplate = () => {
  const template = promptTemplates.value.find(t => t.id === selectedTemplate.value)
  if (template) {
    formData.value.system_prompt = template.content
  }
  showTemplateSelector.value = false
}

// 选择工具
const selectTools = () => {
  const tools = availableTools.value.filter(tool => selectedTools.value.includes(tool.id))
  formData.value.tools = [...formData.value.tools, ...tools]
  selectedTools.value = []
  showToolSelector.value = false
}

// 测试配置
const handleTest = async () => {
  if (!testMessage.value.trim()) {
    message.warning('请输入测试消息')
    return
  }

  try {
    testing.value = true
    const response = await agentAPI.testAgent(formData.value, testMessage.value)
    
    testResult.value = {
      success: response.success,
      message: response.success ? '配置测试通过' : response.message || '测试失败'
    }
  } catch (error) {
    console.error('测试失败:', error)
    testResult.value = {
      success: false,
      message: '测试请求失败'
    }
  } finally {
    testing.value = false
  }
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    loading.value = true

    // 构建提交数据
    const submitData = {
      ...formData.value,
      // 如果没有启用知识库或MCP，清空相关配置
      knowledge_config: formData.value.knowledge_config.enabled ? formData.value.knowledge_config : {
        enabled: false,
        databases: [],
        retrieval_config: defaultFormData.knowledge_config.retrieval_config
      },
      mcp_config: formData.value.mcp_config.enabled ? formData.value.mcp_config : {
        enabled: false,
        servers: []
      }
    }

    if (props.mode === 'edit') {
      await agentAPI.updateAgent(props.agent.id, submitData)
      message.success('智能体更新成功')
    } else {
      await agentAPI.createAgent(submitData)
      message.success('智能体创建成功')
    }

    emit('success')
    emit('update:visible', false)
  } catch (error) {
    console.error('提交表单失败:', error)
    message.error('操作失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

// 取消
const handleCancel = () => {
  modalVisible.value = false
}

// 头像上传前处理
const beforeAvatarUpload = (file) => {
  const isJPGOrPNG = file.type === 'image/jpeg' || file.type === 'image/png'
  if (!isJPGOrPNG) {
    message.error('只能上传 JPG/PNG 格式的图片!')
    return false
  }
  const isLt2M = file.size / 1024 / 1024 < 2
  if (!isLt2M) {
    message.error('图片大小不能超过 2MB!')
    return false
  }
  
  // 创建预览并转换为base64
  const reader = new FileReader()
  reader.onload = (e) => {
    avatarPreview.value = e.target.result
    formData.value.avatar = e.target.result // 将base64数据保存到formData
  }
  reader.readAsDataURL(file)
  
  return false // 阻止自动上传，我们手动处理
}

// 组件挂载
onMounted(() => {
  // 加载提示词模板
  promptTemplates.value = [
    {
      id: '1',
      name: '通用助手',
      description: '适用于一般对话的助手模板',
      content: '你是一个有用、无害、诚实的AI助手。请根据用户的问题提供准确、有帮助的回答。'
    },
    {
      id: '2', 
      name: '技术专家',
      description: '专注于技术问题解答的专家模板',
      content: '你是一个技术专家，擅长解答编程、系统架构等技术问题。请提供详细、准确的技术解决方案。'
    }
  ]

  // 加载可用工具
  availableTools.value = [
    {
      id: 'web_search',
      name: '网络搜索',
      description: '搜索互联网上的信息'
    },
    {
      id: 'calculator',
      name: '计算器',
      description: '进行数学计算'
    },
    {
      id: 'code_executor',
      name: '代码执行',
      description: '执行Python代码'
    }
  ]
})
</script>

<style scoped>
.agent-form {
  max-height: 600px;
  overflow-y: auto;
}

.form-section {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.form-section:last-child {
  border-bottom: none;
}

.section-title {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  display: flex;
  align-items: center;
  gap: 8px;
}

.help-icon {
  color: #999;
  cursor: help;
}

.prompt-editor {
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  overflow: hidden;
}

.prompt-toolbar {
  padding: 8px 12px;
  background: #fafafa;
  border-bottom: 1px solid #d9d9d9;
}

.prompt-textarea :deep(.ant-input) {
  border: none;
  box-shadow: none;
}

.tools-list {
  max-height: 200px;
  overflow-y: auto;
}

.tool-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  margin-bottom: 8px;
}

.tool-info {
  flex: 1;
}

.tool-name {
  font-weight: 500;
  display: block;
}

.tool-description {
  font-size: 12px;
  color: #999;
}

.test-section {
  margin-top: 16px;
}

.test-controls {
  margin-bottom: 12px;
}

.test-result {
  margin-top: 12px;
}

.template-list {
  max-height: 400px;
  overflow-y: auto;
}

.template-item {
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.template-item:last-child {
  border-bottom: none;
}

.template-info {
  margin-left: 8px;
}

.template-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.template-description {
  font-size: 12px;
  color: #999;
}

.tool-selector {
  max-height: 400px;
  overflow-y: auto;
}

.tool-option {
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.tool-option:last-child {
  border-bottom: none;
}

.tool-option-info {
  margin-left: 8px;
}

.tool-option-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.tool-option-description {
  font-size: 12px;
  color: #999;
}

.avatar-upload-section {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.avatar-preview {
  flex-shrink: 0;
}

.avatar-upload {
  flex-grow: 1;
}

.upload-hint {
  font-size: 12px;
  color: #999;
  margin-top: 8px;
}
</style> 