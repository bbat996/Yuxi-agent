<template>
  <div class="prompt-template-modal">
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
          <a-form-item label="模板名称" name="name">
            <a-input 
              v-model:value="formData.name" 
              placeholder="请输入模板名称"
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
              @search="handleCategorySearch"
            >
              <template #notFoundContent>
                <div style="padding: 8px;">
                  <a-button type="link" @click="addCategory">
                    <template #icon><PlusOutlined /></template>
                    添加新分类
                  </a-button>
                </div>
              </template>
            </a-select>
          </a-form-item>
        </a-col>
      </a-row>

      <!-- 描述 -->
      <a-form-item label="模板描述" name="description">
        <a-textarea
          v-model:value="formData.description"
          placeholder="请输入模板描述"
          :rows="3"
          :maxlength="500"
          show-count
        />
      </a-form-item>

      <!-- 模板内容 -->
      <a-form-item label="模板内容" name="content">
        <div class="content-editor">
          <div class="editor-toolbar">
            <a-space>
              <a-button size="small" @click="insertVariable">
                <template #icon><PlusOutlined /></template>
                插入变量
              </a-button>
              <a-button size="small" @click="showVariableHelp">
                <template #icon><QuestionCircleOutlined /></template>
                变量语法
              </a-button>
              <a-button size="small" @click="previewTemplate">
                <template #icon><EyeOutlined /></template>
                预览
              </a-button>
            </a-space>
          </div>
          <a-textarea
            v-model:value="formData.content"
            placeholder="请输入模板内容，使用 {{变量名}} 来定义变量"
            :rows="10"
            class="content-textarea"
          />
        </div>
      </a-form-item>

      <!-- 变量定义 -->
      <a-form-item label="变量定义">
        <div class="variables-section">
          <div class="variables-header">
            <span>已检测到的变量：</span>
            <a-button size="small" type="primary" @click="detectVariables">
              <template #icon><ReloadOutlined /></template>
              重新检测
            </a-button>
          </div>
          
          <div v-if="detectedVariables.length === 0" class="no-variables">
            <a-empty 
              :image="null" 
              description="暂未检测到变量"
              style="margin: 16px 0;"
            />
          </div>
          
          <div v-else class="variables-list">
            <a-card 
              v-for="(variable, index) in detectedVariables" 
              :key="variable.name"
              size="small"
              class="variable-card"
            >
              <template #title>
                <div class="variable-title">
                  <a-tag color="blue">{{ variable.name }}</a-tag>
                  <a-button 
                    type="text" 
                    size="small" 
                    danger
                    @click="removeVariable(index)"
                  >
                    <template #icon><DeleteOutlined /></template>
                  </a-button>
                </div>
              </template>
              
              <a-row :gutter="16">
                <a-col :span="8">
                  <a-form-item label="类型" :name="['variables', index, 'type']">
                    <a-select v-model:value="variable.type" size="small">
                      <a-select-option value="text">文本</a-select-option>
                      <a-select-option value="number">数字</a-select-option>
                      <a-select-option value="boolean">布尔值</a-select-option>
                      <a-select-option value="select">选择</a-select-option>
                    </a-select>
                  </a-form-item>
                </a-col>
                <a-col :span="8">
                  <a-form-item label="默认值" :name="['variables', index, 'default']">
                    <a-input 
                      v-model:value="variable.default" 
                      size="small"
                      placeholder="默认值（可选）"
                    />
                  </a-form-item>
                </a-col>
                <a-col :span="8">
                  <a-form-item label="是否必填" :name="['variables', index, 'required']">
                    <a-switch v-model:checked="variable.required" size="small" />
                  </a-form-item>
                </a-col>
              </a-row>
              
              <a-form-item label="描述" :name="['variables', index, 'description']">
                <a-input 
                  v-model:value="variable.description" 
                  size="small"
                  placeholder="变量用途描述"
                />
              </a-form-item>
              
              <a-form-item 
                v-if="variable.type === 'select'" 
                label="选项" 
                :name="['variables', index, 'options']"
              >
                <a-select
                  v-model:value="variable.options"
                  mode="tags"
                  size="small"
                  placeholder="输入选项，回车添加"
                  style="width: 100%"
                />
              </a-form-item>
            </a-card>
          </div>
        </div>
      </a-form-item>

      <!-- 表单操作 -->
      <a-form-item>
        <div class="form-actions">
          <a-space>
            <a-button @click="handleCancel">取消</a-button>
            <a-button type="primary" html-type="submit" :loading="loading">
              {{ mode === 'create' ? '创建模板' : '更新模板' }}
            </a-button>
            <a-button v-if="mode === 'edit'" @click="handleTest">
              测试模板
            </a-button>
          </a-space>
        </div>
      </a-form-item>
    </a-form>

    <!-- 变量插入模态框 -->
    <a-modal
      v-model:open="variableModalVisible"
      title="插入变量"
      :width="400"
      @ok="handleInsertVariable"
    >
      <a-form layout="vertical">
        <a-form-item label="变量名">
          <a-input v-model:value="newVariableName" placeholder="请输入变量名" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 预览模态框 -->
    <a-modal
      v-model:open="previewModalVisible"
      title="模板预览"
      :width="800"
      :footer="null"
    >
      <PromptTemplatePreview :template="previewData" />
    </a-modal>

    <!-- 变量语法帮助 -->
    <a-modal
      v-model:open="helpModalVisible"
      title="变量语法说明"
      :width="600"
      :footer="null"
    >
      <div class="help-content">
        <h4>变量语法</h4>
        <ul>
          <li>使用 <code>{{变量名}}</code> 来定义变量</li>
          <li>变量名只能包含字母、数字和下划线</li>
          <li>变量名区分大小写</li>
        </ul>
        
        <h4>示例</h4>
        <pre class="example-code">你好，{{用户名}}！

请帮我分析以下{{内容类型}}：
{{用户输入}}

分析要求：
- 详细程度：{{详细程度}}
- 输出格式：{{输出格式}}</pre>
        
        <h4>常用变量</h4>
        <a-tag color="blue" @click="insertCommonVariable('用户名')">用户名</a-tag>
        <a-tag color="blue" @click="insertCommonVariable('任务')">任务</a-tag>
        <a-tag color="blue" @click="insertCommonVariable('内容')">内容</a-tag>
        <a-tag color="blue" @click="insertCommonVariable('语言')">语言</a-tag>
        <a-tag color="blue" @click="insertCommonVariable('格式')">格式</a-tag>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { 
  PlusOutlined, 
  QuestionCircleOutlined, 
  EyeOutlined,
  ReloadOutlined,
  DeleteOutlined
} from '@ant-design/icons-vue'
import { templateAPI } from '@/apis/template_api'
import PromptTemplatePreview from './PromptTemplatePreview.vue'

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
const detectedVariables = ref([])

// 模态框状态
const variableModalVisible = ref(false)
const previewModalVisible = ref(false)
const helpModalVisible = ref(false)
const newVariableName = ref('')

// 表单数据
const formData = reactive({
  name: '',
  category: '',
  description: '',
  content: '',
  variables: []
})

// 预览数据
const previewData = computed(() => ({
  ...formData,
  variables: detectedVariables.value
}))

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入模板名称' },
    { min: 1, max: 100, message: '模板名称长度为1-100个字符' }
  ],
  content: [
    { required: true, message: '请输入模板内容' }
  ]
}

// 监听模板内容变化，自动检测变量
watch(() => formData.content, (newContent) => {
  if (newContent) {
    detectVariables()
  }
}, { debounce: 500 })

// 初始化表单数据
const initFormData = () => {
  if (props.data && props.mode === 'edit') {
    Object.assign(formData, {
      name: props.data.name || '',
      category: props.data.category || '',
      description: props.data.description || '',
      content: props.data.content || '',
      variables: props.data.variables || []
    })
    
    // 设置检测到的变量
    detectedVariables.value = [...(props.data.variables || [])]
  } else {
    // 重置表单
    Object.assign(formData, {
      name: '',
      category: '',
      description: '',
      content: '',
      variables: []
    })
    detectedVariables.value = []
  }
}

// 获取分类选项
const fetchCategories = async () => {
  try {
    const response = await templateAPI.getCategories('prompt')
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

// 检测模板中的变量
const detectVariables = () => {
  const content = formData.content
  if (!content) {
    detectedVariables.value = []
    return
  }
  
  // 使用正则表达式检测变量
  const variableRegex = /\{\{([^}]+)\}\}/g
  const foundVariables = new Set()
  let match
  
  while ((match = variableRegex.exec(content)) !== null) {
    const variableName = match[1].trim()
    if (variableName) {
      foundVariables.add(variableName)
    }
  }
  
  // 合并现有变量配置
  const newVariables = []
  const existingVarMap = new Map()
  
  detectedVariables.value.forEach(v => {
    existingVarMap.set(v.name, v)
  })
  
  foundVariables.forEach(name => {
    if (existingVarMap.has(name)) {
      newVariables.push(existingVarMap.get(name))
    } else {
      newVariables.push({
        name,
        type: 'text',
        description: '',
        default: '',
        required: false,
        options: []
      })
    }
  })
  
  detectedVariables.value = newVariables
}

// 插入变量
const insertVariable = () => {
  newVariableName.value = ''
  variableModalVisible.value = true
}

// 处理插入变量
const handleInsertVariable = () => {
  const name = newVariableName.value.trim()
  if (!name) {
    message.error('请输入变量名')
    return
  }
  
  if (!/^[a-zA-Z0-9_\u4e00-\u9fa5]+$/.test(name)) {
    message.error('变量名只能包含字母、数字、下划线和中文字符')
    return
  }
  
  const variableText = `{{${name}}}`
  
  // 在光标位置插入变量
  const textarea = document.querySelector('.content-textarea textarea')
  if (textarea) {
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const text = formData.content
    
    formData.content = text.substring(0, start) + variableText + text.substring(end)
    
    // 设置光标位置
    setTimeout(() => {
      textarea.focus()
      textarea.setSelectionRange(start + variableText.length, start + variableText.length)
    }, 0)
  } else {
    formData.content += variableText
  }
  
  variableModalVisible.value = false
}

// 插入常用变量
const insertCommonVariable = (name) => {
  const variableText = `{{${name}}}`
  formData.content += variableText
  helpModalVisible.value = false
}

// 移除变量
const removeVariable = (index) => {
  detectedVariables.value.splice(index, 1)
}

// 显示变量帮助
const showVariableHelp = () => {
  helpModalVisible.value = true
}

// 预览模板
const previewTemplate = () => {
  if (!formData.content) {
    message.warning('请先输入模板内容')
    return
  }
  previewModalVisible.value = true
}

// 测试模板
const handleTest = () => {
  // 实现模板测试逻辑
  message.info('模板测试功能开发中...')
}

// 分类搜索
const handleCategorySearch = (value) => {
  // 实现分类搜索逻辑
}

// 添加分类
const addCategory = () => {
  // 实现添加新分类逻辑
}

// 提交表单
const handleSubmit = async (values) => {
  try {
    loading.value = true
    
    const submitData = {
      ...values,
      variables: detectedVariables.value
    }
    
    let response
    if (props.mode === 'create') {
      response = await templateAPI.createPromptTemplate(submitData)
    } else {
      response = await templateAPI.updatePromptTemplate(props.data.template_id, submitData)
    }
    
    if (response.success) {
      message.success(`模板${props.mode === 'create' ? '创建' : '更新'}成功`)
      emit('success')
    } else {
      message.error(`模板${props.mode === 'create' ? '创建' : '更新'}失败`)
    }
  } catch (error) {
    console.error('提交模板失败:', error)
    message.error(`模板${props.mode === 'create' ? '创建' : '更新'}失败`)
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
.prompt-template-modal .content-editor .editor-toolbar {
  margin-bottom: 8px;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.prompt-template-modal .content-editor .content-textarea {
  font-family: 'Monaco', 'Consolas', 'Courier New', monospace;
}

.prompt-template-modal .variables-section {
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  padding: 16px;
  background-color: #fafafa;
}

.prompt-template-modal .variables-section .variables-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  font-weight: 500;
}

.prompt-template-modal .variables-section .no-variables {
  text-align: center;
  color: #999;
}

.prompt-template-modal .variables-section .variables-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.prompt-template-modal .variables-section .variable-card .variable-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.prompt-template-modal .form-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.prompt-template-modal .help-content h4 {
  margin-top: 16px;
  margin-bottom: 8px;
  color: #333;
}

.prompt-template-modal .help-content ul {
  margin-bottom: 16px;
}

.prompt-template-modal .help-content ul li {
  margin-bottom: 4px;
}

.prompt-template-modal .help-content .example-code {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  padding: 12px;
  font-family: 'Monaco', 'Consolas', 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.5;
  margin-bottom: 16px;
}

.prompt-template-modal .help-content .ant-tag {
  margin: 4px 8px 4px 0;
  cursor: pointer;
}
</style> 