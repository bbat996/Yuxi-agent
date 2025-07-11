<template>
  <a-modal
    :visible="modalVisible"
    :title="modalTitle"
    width="800px"
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
        
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="智能体名称" name="name">
              <a-input 
                v-model:value="formData.name" 
                placeholder="请输入智能体名称"
                :maxlength="50"
                show-count
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="智能体类型" name="agent_type">
              <a-select v-model:value="formData.agent_type" placeholder="选择智能体类型">
                <a-select-option value="custom">自定义</a-select-option>
                <a-select-option value="chatbot">聊天助手</a-select-option>
                <a-select-option value="react">ReAct智能体</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item label="智能体描述" name="description">
          <a-textarea 
            v-model:value="formData.description" 
            placeholder="描述智能体的功能和用途"
            :rows="3"
            :maxlength="200"
            show-count
          />
        </a-form-item>
      </div>

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
            <a-form-item label="模型" name="model">
              <a-select 
                v-model:value="formData.model_config.model" 
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
          <a-col :span="12">
            <a-form-item label="温度" name="temperature">
              <a-slider
                v-model:value="formData.model_config.temperature"
                :min="0"
                :max="2"
                :step="0.1"
                :tooltip-formatter="(val) => `${val} (${getTemperatureLabel(val)})`"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="最大回复长度">
              <a-input-number
                v-model:value="formData.model_config.max_tokens"
                :min="1"
                :max="4000"
                placeholder="最大回复长度"
                style="width: 100%"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="Top P">
              <a-slider
                v-model:value="formData.model_config.top_p"
                :min="0"
                :max="1"
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
            v-for="(tool, index) in formData.tools_config" 
            :key="index"
            class="tool-item"
          >
            <div class="tool-info">
              <span class="tool-name">{{ tool.name }}</span>
              <span class="tool-description">{{ tool.description }}</span>
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
          
          <a-empty v-if="formData.tools_config.length === 0" :image="false" description="暂未配置工具">
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
        
        <a-form-item label="知识库">
          <a-select
            v-model:value="formData.knowledge_config.databases"
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
                v-model:value="formData.knowledge_config.retrieval_config.top_k"
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
                v-model:value="formData.knowledge_config.retrieval_config.similarity_threshold"
                :min="0"
                :max="1"
                :step="0.1"
                :tooltip-formatter="(val) => `${val}`"
              />
            </a-form-item>
          </a-col>
        </a-row>
      </div>
    </a-form>

    <!-- 测试区域 -->
    <div class="test-section" v-if="mode === 'create' || mode === 'edit'">
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
  DeleteOutlined
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

// 表单数据
const formData = reactive({
  name: '',
  description: '',
  agent_type: 'custom',
  system_prompt: '',
  model_config: {
    model: 'gpt-3.5-turbo',
    temperature: 0.7,
    max_tokens: 2000,
    top_p: 0.9
  },
  tools_config: [],
  knowledge_config: {
    databases: [],
    retrieval_config: {
      top_k: 5,
      similarity_threshold: 0.7
    }
  },
  mcp_config: {
    skills: []
  }
})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入智能体名称', trigger: 'blur' },
    { min: 2, max: 50, message: '名称长度在2-50字符之间', trigger: 'blur' }
  ],
  agent_type: [
    { required: true, message: '请选择智能体类型', trigger: 'change' }
  ],
  system_prompt: [
    { required: true, message: '请输入系统提示词', trigger: 'blur' },
    { min: 10, message: '提示词至少需要10个字符', trigger: 'blur' }
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

// 计算属性
const modalTitle = computed(() => {
  return props.mode === 'edit' ? '编辑智能体' : '创建智能体'
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
    // 编辑模式，填充现有数据
    Object.assign(formData, {
      ...props.agent,
      model_config: { ...formData.model_config, ...props.agent.model_config },
      knowledge_config: { ...formData.knowledge_config, ...props.agent.knowledge_config }
    })
  } else {
    // 创建模式，重置表单
    resetForm()
  }
  
  // 清空测试结果
  testResult.value = null
}

// 重置表单
const resetForm = () => {
  Object.assign(formData, {
    name: '',
    description: '',
    agent_type: 'custom',
    system_prompt: '',
    model_config: {
      model: 'gpt-3.5-turbo',
      temperature: 0.7,
      max_tokens: 2000,
      top_p: 0.9
    },
    tools_config: [],
    knowledge_config: {
      databases: [],
      retrieval_config: {
        top_k: 5,
        similarity_threshold: 0.7
      }
    },
    mcp_config: {
      skills: []
    }
  })
}

// 温度标签
const getTemperatureLabel = (val) => {
  if (val <= 0.3) return '保守'
  if (val <= 0.7) return '平衡'
  if (val <= 1.2) return '创造'
  return '发散'
}

// 模型变化处理
const handleModelChange = (model) => {
  // 根据模型调整默认参数
  if (model === 'gpt-4') {
    formData.model_config.max_tokens = 3000
  } else if (model === 'gpt-3.5-turbo') {
    formData.model_config.max_tokens = 2000
  }
}

// 移除工具
const removeTool = (index) => {
  formData.tools_config.splice(index, 1)
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
    const text = formData.system_prompt
    formData.system_prompt = text.substring(0, start) + variable + text.substring(end)
  }
}

// 加载知识库列表
const loadKnowledgeBases = async () => {
  if (knowledgeBases.value.length > 0) return
  
  try {
    knowledgeLoading.value = true
    // 调用知识库API获取列表
    // const response = await knowledgeAPI.getKnowledgeBases()
    // knowledgeBases.value = response.data || []
    
    // 模拟数据
    knowledgeBases.value = [
      { id: '1', name: '技术文档' },
      { id: '2', name: '产品手册' },
      { id: '3', name: '常见问题' }
    ]
  } catch (error) {
    console.error('加载知识库失败:', error)
  } finally {
    knowledgeLoading.value = false
  }
}

// 选择模板
const selectTemplate = () => {
  const template = promptTemplates.value.find(t => t.id === selectedTemplate.value)
  if (template) {
    formData.system_prompt = template.content
  }
  showTemplateSelector.value = false
}

// 选择工具
const selectTools = () => {
  const tools = availableTools.value.filter(tool => selectedTools.value.includes(tool.id))
  formData.tools_config = [...formData.tools_config, ...tools]
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
    const response = await agentAPI.testAgent(formData, testMessage.value)
    
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
    await formRef.value.validateFields()
    loading.value = true

    let response
    if (props.mode === 'edit') {
      response = await agentAPI.updateAgent(props.agent.agent_id, formData)
    } else {
      response = await agentAPI.createAgent(formData)
    }

    if (response.success) {
      message.success(props.mode === 'edit' ? '智能体更新成功' : '智能体创建成功')
      emit('success')
      modalVisible.value = false
    } else {
      message.error(response.message || '操作失败')
    }
  } catch (error) {
    console.error('表单验证失败:', error)
  } finally {
    loading.value = false
  }
}

// 取消
const handleCancel = () => {
  modalVisible.value = false
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
</style> 