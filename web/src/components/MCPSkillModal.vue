<template>
  <div class="mcp-skill-modal">
    <a-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      layout="vertical"
      @finish="handleSubmit"
    >
      <!-- 基础信息 -->
      <a-row :gutter="16">
        <a-col :span="12">
          <a-form-item label="技能名称" name="name">
            <a-input 
              v-model:value="formData.name" 
              placeholder="请输入技能名称"
              :maxlength="100"
              show-count
            />
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="分类" name="category">
            <a-select 
              v-model:value="formData.category" 
              placeholder="请选择或输入分类"
              :options="categoryOptions"
              show-search
              allow-clear
            />
          </a-form-item>
        </a-col>
      </a-row>

      <!-- 描述 -->
      <a-form-item label="技能描述" name="description">
        <a-textarea
          v-model:value="formData.description"
          placeholder="请输入技能描述"
          :rows="3"
          :maxlength="500"
          show-count
        />
      </a-form-item>

      <!-- MCP服务器配置 -->
      <a-form-item label="MCP服务器地址" name="mcp_server">
        <a-input
          v-model:value="formData.mcp_server"
          placeholder="请输入MCP服务器地址，如：http://localhost:3000"
        />
      </a-form-item>

      <!-- 版本 -->
      <a-form-item label="版本号" name="version">
        <a-input
          v-model:value="formData.version"
          placeholder="请输入版本号，如：1.0.0"
        />
      </a-form-item>

      <!-- MCP配置 -->
      <a-form-item label="MCP连接配置" name="mcp_config">
        <div class="json-editor">
          <a-textarea
            v-model:value="mcpConfigString"
            placeholder='请输入MCP配置JSON，如：{"timeout": 30}'
            :rows="6"
            @blur="validateMCPConfig"
          />
          <div v-if="mcpConfigError" class="config-error">
            <a-alert type="error" :message="mcpConfigError" show-icon />
          </div>
        </div>
      </a-form-item>

      <!-- 工具Schema -->
      <a-form-item label="工具Schema定义（可选）" name="tool_schema">
        <div class="json-editor">
          <a-textarea
            v-model:value="toolSchemaString"
            placeholder="请输入工具Schema JSON定义"
            :rows="8"
            @blur="validateToolSchema"
          />
          <div v-if="toolSchemaError" class="config-error">
            <a-alert type="error" :message="toolSchemaError" show-icon />
          </div>
        </div>
      </a-form-item>

      <!-- 默认参数 -->
      <a-form-item label="默认参数配置（可选）" name="parameters">
        <div class="json-editor">
          <a-textarea
            v-model:value="parametersString"
            placeholder='请输入默认参数JSON，如：{"max_retries": 3}'
            :rows="4"
            @blur="validateParameters"
          />
          <div v-if="parametersError" class="config-error">
            <a-alert type="error" :message="parametersError" show-icon />
          </div>
        </div>
      </a-form-item>

      <!-- 表单操作 -->
      <a-form-item>
        <div class="form-actions">
          <a-space>
            <a-button @click="handleCancel">取消</a-button>
            <a-button type="primary" html-type="submit" :loading="loading">
              {{ mode === 'create' ? '注册技能' : '更新技能' }}
            </a-button>
            <a-button v-if="mode === 'edit'" @click="handleTest">
              测试技能
            </a-button>
          </a-space>
        </div>
      </a-form-item>
    </a-form>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { templateAPI } from '@/apis/template_api'

// Props
const props = defineProps({
  data: {
    type: Object,
    default: null
  },
  mode: {
    type: String,
    default: 'create' // 'create' | 'edit'
  }
})

// Emits
const emit = defineEmits(['success', 'cancel'])

// 响应式数据
const formRef = ref()
const loading = ref(false)
const categoryOptions = ref([])

// JSON字符串
const mcpConfigString = ref('{}')
const toolSchemaString = ref('')
const parametersString = ref('{}')

// 错误信息
const mcpConfigError = ref('')
const toolSchemaError = ref('')
const parametersError = ref('')

// 表单数据
const formData = reactive({
  name: '',
  description: '',
  mcp_server: '',
  mcp_config: {},
  tool_schema: null,
  parameters: {},
  category: '',
  version: ''
})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入技能名称' },
    { min: 1, max: 100, message: '技能名称长度为1-100个字符' }
  ],
  mcp_server: [
    { required: true, message: '请输入MCP服务器地址' }
  ]
}

// 初始化表单数据
const initFormData = () => {
  if (props.data && props.mode === 'edit') {
    Object.assign(formData, {
      name: props.data.name || '',
      description: props.data.description || '',
      mcp_server: props.data.mcp_server || '',
      mcp_config: props.data.mcp_config || {},
      tool_schema: props.data.tool_schema || null,
      parameters: props.data.parameters || {},
      category: props.data.category || '',
      version: props.data.version || ''
    })
    
    // 设置JSON字符串
    mcpConfigString.value = JSON.stringify(props.data.mcp_config || {}, null, 2)
    toolSchemaString.value = props.data.tool_schema ? JSON.stringify(props.data.tool_schema, null, 2) : ''
    parametersString.value = JSON.stringify(props.data.parameters || {}, null, 2)
  } else {
    // 重置表单
    Object.assign(formData, {
      name: '',
      description: '',
      mcp_server: '',
      mcp_config: {},
      tool_schema: null,
      parameters: {},
      category: '',
      version: ''
    })
    
    // 重置JSON字符串
    mcpConfigString.value = '{}'
    toolSchemaString.value = ''
    parametersString.value = '{}'
  }
}

// 获取分类选项
const fetchCategories = async () => {
  try {
    const response = await templateAPI.getCategories('mcp')
    if (response.success) {
      categoryOptions.value = (response.data.categories || []).map(cat => ({
        label: cat,
        value: cat
      }))
    }
  } catch (error) {
    console.error('获取分类失败:', error)
  }
}

// 验证MCP配置
const validateMCPConfig = () => {
  try {
    const config = JSON.parse(mcpConfigString.value)
    formData.mcp_config = config
    mcpConfigError.value = ''
  } catch (error) {
    mcpConfigError.value = 'MCP配置JSON格式错误'
  }
}

// 验证工具Schema
const validateToolSchema = () => {
  if (!toolSchemaString.value.trim()) {
    formData.tool_schema = null
    toolSchemaError.value = ''
    return
  }
  
  try {
    const schema = JSON.parse(toolSchemaString.value)
    formData.tool_schema = schema
    toolSchemaError.value = ''
  } catch (error) {
    toolSchemaError.value = '工具Schema JSON格式错误'
  }
}

// 验证参数配置
const validateParameters = () => {
  try {
    const params = JSON.parse(parametersString.value)
    formData.parameters = params
    parametersError.value = ''
  } catch (error) {
    parametersError.value = '参数配置JSON格式错误'
  }
}

// 测试技能
const handleTest = async () => {
  try {
    loading.value = true
    
    // 验证所有JSON配置
    validateMCPConfig()
    validateToolSchema() 
    validateParameters()
    
    if (mcpConfigError.value || toolSchemaError.value || parametersError.value) {
      message.error('请修复JSON配置错误')
      return
    }
    
    const response = await templateAPI.testMCPSkill(props.data.skill_id, {
      test_config: formData.mcp_config,
      test_params: formData.parameters
    })
    
    if (response.success) {
      message.success('技能测试成功')
    } else {
      message.error('技能测试失败: ' + (response.message || '未知错误'))
    }
  } catch (error) {
    console.error('测试技能失败:', error)
    message.error('技能测试失败')
  } finally {
    loading.value = false
  }
}

// 提交表单
const handleSubmit = async (values) => {
  try {
    loading.value = true
    
    // 验证所有JSON配置
    validateMCPConfig()
    validateToolSchema()
    validateParameters()
    
    if (mcpConfigError.value || toolSchemaError.value || parametersError.value) {
      message.error('请修复JSON配置错误')
      return
    }
    
    const submitData = {
      ...values,
      mcp_config: formData.mcp_config,
      tool_schema: formData.tool_schema,
      parameters: formData.parameters
    }
    
    let response
    if (props.mode === 'create') {
      response = await templateAPI.createMCPSkill(submitData)
    } else {
      response = await templateAPI.updateMCPSkill(props.data.skill_id, submitData)
    }
    
    if (response.success) {
      message.success(`技能${props.mode === 'create' ? '注册' : '更新'}成功`)
      emit('success')
    } else {
      message.error(`技能${props.mode === 'create' ? '注册' : '更新'}失败`)
    }
  } catch (error) {
    console.error('提交技能失败:', error)
    message.error(`技能${props.mode === 'create' ? '注册' : '更新'}失败`)
  } finally {
    loading.value = false
  }
}

// 取消
const handleCancel = () => {
  emit('cancel')
}

// 确保在组件挂载时初始化表单
onMounted(() => {
  initFormData()
  fetchCategories()
})

// 监听 props.data 变化，重新初始化表单
watch(() => props.data, () => {
  initFormData()
}, { immediate: true })
</script>

<style scoped>
.mcp-skill-modal {
  .json-editor {
    .config-error {
      margin-top: 8px;
    }
  }
  
  .form-actions {
    display: flex;
    justify-content: flex-end;
    padding-top: 16px;
    border-top: 1px solid #f0f0f0;
  }
}
</style> 