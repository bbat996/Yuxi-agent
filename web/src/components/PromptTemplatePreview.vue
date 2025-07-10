<template>
  <div class="prompt-template-preview">
    <!-- 模板基础信息 -->
    <div class="template-header">
      <h3>{{ template.name }}</h3>
      <div class="template-tags">
        <a-tag v-if="template.category" color="blue">{{ template.category }}</a-tag>
        <a-tag v-if="template.is_system" color="gold">系统模板</a-tag>
      </div>
    </div>

    <div v-if="template.description" class="template-description">
      <p>{{ template.description }}</p>
    </div>

    <!-- 模板内容 -->
    <div class="template-content">
      <h4>模板内容</h4>
      <div class="content-display">
        <pre>{{ template.content }}</pre>
      </div>
    </div>

    <!-- 变量信息 -->
    <div v-if="template.variables && template.variables.length > 0" class="variables-info">
      <h4>变量说明 ({{ template.variables.length }}个)</h4>
      <div class="variables-list">
        <a-card 
          v-for="variable in validVariables" 
          :key="variable.name"
          size="small"
          class="variable-card"
        >
          <template #title>
            <div class="variable-header">
              <a-tag color="blue">{{ variable.name }}</a-tag>
              <a-tag color="green" v-if="variable.required">必填</a-tag>
              <a-tag color="orange" v-else>可选</a-tag>
              <span class="variable-type">{{ getVariableTypeLabel(variable.type) }}</span>
            </div>
          </template>
          
          <div class="variable-details">
            <div v-if="variable.description" class="variable-description">
              <strong>说明：</strong>{{ variable.description }}
            </div>
            <div v-if="variable.default" class="variable-default">
              <strong>默认值：</strong>{{ variable.default }}
            </div>
            <div v-if="variable.type === 'select' && variable.options && variable.options.length" class="variable-options">
              <strong>可选值：</strong>
              <a-tag v-for="option in variable.options" :key="option" style="margin: 2px;">
                {{ option }}
              </a-tag>
            </div>
          </div>
        </a-card>
      </div>
    </div>

    <!-- 使用示例 -->
    <div class="usage-example">
      <h4>使用示例</h4>
      <div class="example-form">
        <a-form layout="vertical">
          <a-form-item 
            v-for="variable in validVariables" 
            :key="variable.name"
            :label="variable.name"
            :required="variable.required"
          >
            <!-- 文本输入 -->
            <a-input 
              v-if="variable.type === 'text'"
              v-model:value="exampleValues[variable.name]"
              :placeholder="variable.description || `请输入${variable.name}`"
            />
            
            <!-- 数字输入 -->
            <a-input-number 
              v-else-if="variable.type === 'number'"
              v-model:value="exampleValues[variable.name]"
              :placeholder="variable.description || `请输入${variable.name}`"
              style="width: 100%"
            />
            
            <!-- 布尔值选择 -->
            <a-switch 
              v-else-if="variable.type === 'boolean'"
              v-model:checked="exampleValues[variable.name]"
            />
            
            <!-- 选择框 -->
            <a-select 
              v-else-if="variable.type === 'select'"
              v-model:value="exampleValues[variable.name]"
              :placeholder="variable.description || `请选择${variable.name}`"
              style="width: 100%"
            >
              <a-select-option 
                v-for="option in variable.options" 
                :key="option" 
                :value="option"
              >
                {{ option }}
              </a-select-option>
            </a-select>
          </a-form-item>
        </a-form>
      </div>
      
      <!-- 生成结果 -->
      <div class="generated-result">
        <h5>生成结果：</h5>
        <div class="result-display">
          <pre>{{ generatedContent }}</pre>
        </div>
        <div class="result-actions">
          <a-button @click="copyResult" size="small">
            <template #icon><CopyOutlined /></template>
            复制结果
          </a-button>
          <a-button @click="resetExample" size="small">
            <template #icon><ReloadOutlined /></template>
            重置示例
          </a-button>
        </div>
      </div>
    </div>

    <!-- 模板统计信息 -->
    <div class="template-stats">
      <h4>模板信息</h4>
      <a-descriptions :column="2" size="small">
        <a-descriptions-item label="创建时间">
          {{ formatDate(template.created_at) }}
        </a-descriptions-item>
        <a-descriptions-item label="更新时间">
          {{ formatDate(template.updated_at) }}
        </a-descriptions-item>
        <a-descriptions-item label="字符数">
          {{ template.content ? template.content.length : 0 }}
        </a-descriptions-item>
        <a-descriptions-item label="变量数">
          {{ template.variables ? template.variables.length : 0 }}
        </a-descriptions-item>
        <a-descriptions-item label="使用次数" v-if="template.use_count !== undefined">
          {{ template.use_count }}
        </a-descriptions-item>
        <a-descriptions-item label="最后使用" v-if="template.last_used_at">
          {{ formatDate(template.last_used_at) }}
        </a-descriptions-item>
      </a-descriptions>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { CopyOutlined, ReloadOutlined } from '@ant-design/icons-vue'
import dayjs from 'dayjs'

// Props
const props = defineProps({
  template: {
    type: Object,
    required: true,
    default: () => ({})
  }
})

// 响应式数据
const exampleValues = reactive({})

// 计算属性 - 过滤有效的变量
const validVariables = computed(() => {
  if (!props.template.variables) return []
  return props.template.variables.filter(variable => variable && variable.name)
})

// 计算属性 - 生成的内容
const generatedContent = computed(() => {
  let content = props.template.content || ''
  
  // 替换所有变量
  if (validVariables.value && validVariables.value.length > 0) {
    validVariables.value.forEach(variable => {
      const value = exampleValues[variable.name]
      if (value !== undefined && value !== null && value !== '') {
        const regex = new RegExp(`\\{\\{${variable.name}\\}\\}`, 'g')
        content = content.replace(regex, String(value))
      }
    })
  }
  
  return content
})

// 初始化示例值
const initExampleValues = () => {
  if (validVariables.value && validVariables.value.length > 0) {
    validVariables.value.forEach(variable => {
      // 使用默认值或者示例值
      let defaultValue = variable.default || ''
      
      // 根据类型设置默认示例值
      if (!defaultValue) {
        switch (variable.type) {
          case 'text':
            defaultValue = getExampleTextValue(variable.name)
            break
          case 'number':
            defaultValue = getExampleNumberValue(variable.name)
            break
          case 'boolean':
            defaultValue = false
            break
          case 'select':
            defaultValue = variable.options && variable.options.length > 0 ? variable.options[0] : ''
            break
          default:
            defaultValue = ''
        }
      }
      
      exampleValues[variable.name] = defaultValue
    })
  }
}

// 获取示例文本值
const getExampleTextValue = (variableName) => {
  const examples = {
    '用户名': '张三',
    '姓名': '李四',
    '名字': '王五',
    '任务': '分析市场趋势',
    '内容': '这是一个示例内容',
    '主题': '人工智能发展',
    '问题': '如何提高工作效率？',
    '语言': '中文',
    '格式': 'Markdown',
    '类型': '技术文档',
    '标题': '项目报告'
  }
  
  return examples[variableName] || `示例${variableName}`
}

// 获取示例数字值
const getExampleNumberValue = (variableName) => {
  const examples = {
    '数量': 5,
    '长度': 100,
    '时间': 30,
    '年龄': 25,
    '价格': 99.99,
    '评分': 4.5
  }
  
  return examples[variableName] || 1
}

// 获取变量类型标签
const getVariableTypeLabel = (type) => {
  const typeLabels = {
    'text': '文本',
    'number': '数字',
    'boolean': '布尔值',
    'select': '选择'
  }
  
  return typeLabels[type] || type
}

// 复制结果
const copyResult = async () => {
  try {
    await navigator.clipboard.writeText(generatedContent.value)
    message.success('已复制到剪贴板')
  } catch (error) {
    // 降级方案
    const textArea = document.createElement('textarea')
    textArea.value = generatedContent.value
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand('copy')
    document.body.removeChild(textArea)
    message.success('已复制到剪贴板')
  }
}

// 重置示例
const resetExample = () => {
  Object.keys(exampleValues).forEach(key => {
    delete exampleValues[key]
  })
  initExampleValues()
  message.info('已重置示例值')
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '-'
  return dayjs(dateString).format('YYYY-MM-DD HH:mm:ss')
}

// 监听template变化
watch(() => props.template, () => {
  initExampleValues()
}, { immediate: true, deep: true })

// 组件挂载
onMounted(() => {
  initExampleValues()
})
</script>

<style scoped>
.prompt-template-preview {
  max-height: 80vh;
  overflow-y: auto;
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.template-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.template-tags {
  display: flex;
  gap: 8px;
}

.template-description {
  margin-bottom: 24px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 4px solid #1890ff;
}

.template-description p {
  margin: 0;
  color: #666;
  line-height: 1.5;
}

.template-content {
  margin-bottom: 24px;
}

.template-content h4 {
  margin-bottom: 12px;
  font-size: 16px;
  font-weight: 600;
}

.content-display {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 16px;
  max-height: 300px;
  overflow-y: auto;
}

.content-display pre {
  margin: 0;
  font-family: 'Monaco', 'Consolas', 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.variables-info {
  margin-bottom: 24px;
}

.variables-info h4 {
  margin-bottom: 12px;
  font-size: 16px;
  font-weight: 600;
}

.variables-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.variable-card .variable-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.variable-type {
  color: #666;
  font-size: 12px;
  margin-left: auto;
}

.variable-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.variable-details > div {
  font-size: 14px;
  line-height: 1.4;
}

.variable-options .ant-tag {
  margin: 2px 4px 2px 0;
}

.usage-example {
  margin-bottom: 24px;
}

.usage-example h4 {
  margin-bottom: 12px;
  font-size: 16px;
  font-weight: 600;
}

.example-form {
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 16px;
}

.generated-result h5 {
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 600;
}

.result-display {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 12px;
  max-height: 200px;
  overflow-y: auto;
}

.result-display pre {
  margin: 0;
  font-family: 'Monaco', 'Consolas', 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.result-actions {
  display: flex;
  gap: 8px;
}

.template-stats h4 {
  margin-bottom: 12px;
  font-size: 16px;
  font-weight: 600;
}

/* 响应式 */
@media (max-width: 768px) {
  .template-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .variable-header {
    flex-wrap: wrap;
  }
  
  .result-actions {
    flex-direction: column;
  }
}
</style> 