<template>
  <div class="mcp-skill-preview">
    <!-- 技能基础信息 -->
    <div class="skill-header">
      <h3>{{ skill.name }}</h3>
      <div class="skill-tags">
        <a-tag v-if="skill.category" color="blue">{{ skill.category }}</a-tag>
        <a-tag v-if="skill.is_verified" color="green">已验证</a-tag>
        <a-tag v-else color="orange">未验证</a-tag>
        <a-tag v-if="skill.version" color="purple">v{{ skill.version }}</a-tag>
      </div>
    </div>

    <div v-if="skill.description" class="skill-description">
      <p>{{ skill.description }}</p>
    </div>

    <!-- MCP服务器信息 -->
    <div class="server-info">
      <h4>MCP服务器信息</h4>
      <a-descriptions :column="1" size="small" bordered>
        <a-descriptions-item label="服务器地址">
          {{ skill.mcp_server }}
        </a-descriptions-item>
        <a-descriptions-item label="连接状态">
          <a-tag color="green" v-if="connectionStatus === 'connected'">已连接</a-tag>
          <a-tag color="red" v-else-if="connectionStatus === 'disconnected'">未连接</a-tag>
          <a-tag color="orange" v-else>未知</a-tag>
        </a-descriptions-item>
      </a-descriptions>
    </div>

    <!-- MCP配置 -->
    <div v-if="skill.mcp_config" class="config-section">
      <h4>MCP连接配置</h4>
      <div class="config-display">
        <pre>{{ formatJSON(skill.mcp_config) }}</pre>
      </div>
    </div>

    <!-- 工具Schema -->
    <div v-if="skill.tool_schema" class="schema-section">
      <h4>工具Schema定义</h4>
      <div class="schema-display">
        <pre>{{ formatJSON(skill.tool_schema) }}</pre>
      </div>
    </div>

    <!-- 默认参数 -->
    <div v-if="skill.parameters && Object.keys(skill.parameters).length > 0" class="params-section">
      <h4>默认参数配置</h4>
      <div class="params-display">
        <pre>{{ formatJSON(skill.parameters) }}</pre>
      </div>
    </div>

    <!-- 技能测试 -->
    <div class="test-section">
      <h4>技能测试</h4>
      <div class="test-controls">
        <a-button type="primary" @click="testSkill" :loading="testing">
          <template #icon><PlayCircleOutlined /></template>
          测试连接
        </a-button>
        <a-button @click="showTestParams = !showTestParams">
          <template #icon><SettingOutlined /></template>
          {{ showTestParams ? '隐藏' : '显示' }}测试参数
        </a-button>
      </div>
      
      <!-- 测试参数输入 -->
      <div v-if="showTestParams" class="test-params">
        <h5>测试参数：</h5>
        <a-textarea
          v-model:value="testParamsString"
          placeholder='请输入测试参数JSON，如：{"param1": "value1"}'
          :rows="4"
        />
      </div>
      
      <!-- 测试结果 -->
      <div v-if="testResult" class="test-result">
        <h5>测试结果：</h5>
        <a-alert
          :type="testResult.success ? 'success' : 'error'"
          :message="testResult.success ? '测试成功' : '测试失败'"
          :description="testResult.message"
          show-icon
        />
        <div v-if="testResult.data" class="test-data">
          <pre>{{ formatJSON(testResult.data) }}</pre>
        </div>
      </div>
    </div>

    <!-- 技能统计信息 -->
    <div class="skill-stats">
      <h4>技能信息</h4>
      <a-descriptions :column="2" size="small">
        <a-descriptions-item label="创建时间">
          {{ formatDate(skill.created_at) }}
        </a-descriptions-item>
        <a-descriptions-item label="更新时间">
          {{ formatDate(skill.updated_at) }}
        </a-descriptions-item>
        <a-descriptions-item label="创建者">
          {{ skill.created_by || '-' }}
        </a-descriptions-item>
        <a-descriptions-item label="状态">
          <a-tag v-if="skill.is_active" color="green">激活</a-tag>
          <a-tag v-else color="red">停用</a-tag>
        </a-descriptions-item>
      </a-descriptions>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { PlayCircleOutlined, SettingOutlined } from '@ant-design/icons-vue'
import { templateAPI } from '@/apis/template_api'
import dayjs from 'dayjs'

// Props
const props = defineProps({
  skill: {
    type: Object,
    required: true,
    default: () => ({})
  }
})

// 响应式数据
const testing = ref(false)
const showTestParams = ref(false)
const testParamsString = ref('{}')
const testResult = ref(null)
const connectionStatus = ref('unknown')

// 计算属性
const testParams = computed(() => {
  try {
    return JSON.parse(testParamsString.value)
  } catch {
    return {}
  }
})

// 格式化JSON
const formatJSON = (obj) => {
  try {
    return JSON.stringify(obj, null, 2)
  } catch {
    return String(obj)
  }
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '-'
  return dayjs(dateString).format('YYYY-MM-DD HH:mm:ss')
}

// 测试技能
const testSkill = async () => {
  try {
    testing.value = true
    testResult.value = null
    
    const response = await templateAPI.testMCPSkill(props.skill.skill_id, testParams.value)
    
    testResult.value = {
      success: response.success,
      message: response.message || (response.success ? '连接测试成功' : '连接测试失败'),
      data: response.data
    }
    
    // 更新连接状态
    connectionStatus.value = response.success ? 'connected' : 'disconnected'
    
  } catch (error) {
    console.error('测试技能失败:', error)
    testResult.value = {
      success: false,
      message: '测试请求失败: ' + error.message,
      data: null
    }
    connectionStatus.value = 'disconnected'
  } finally {
    testing.value = false
  }
}

// 检查连接状态
const checkConnection = async () => {
  // 可以在这里实现连接状态检查逻辑
  // 暂时设为未知状态
  connectionStatus.value = 'unknown'
}

// 组件挂载
onMounted(() => {
  checkConnection()
})
</script>

<style scoped>
.mcp-skill-preview {
  max-height: 80vh;
  overflow-y: auto;
}

.skill-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.skill-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.skill-tags {
  display: flex;
  gap: 8px;
}

.skill-description {
  margin-bottom: 24px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 4px solid #1890ff;
}

.skill-description p {
  margin: 0;
  color: #666;
  line-height: 1.5;
}

.server-info,
.config-section,
.schema-section,
.params-section,
.test-section,
.skill-stats {
  margin-bottom: 24px;
}

.server-info h4,
.config-section h4,
.schema-section h4,
.params-section h4,
.test-section h4,
.skill-stats h4 {
  margin-bottom: 12px;
  font-size: 16px;
  font-weight: 600;
}

.config-display,
.schema-display,
.params-display {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 16px;
  max-height: 300px;
  overflow-y: auto;
}

.config-display pre,
.schema-display pre,
.params-display pre {
  margin: 0;
  font-family: 'Monaco', 'Consolas', 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.test-controls {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.test-params {
  margin-bottom: 16px;
}

.test-params h5 {
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 600;
}

.test-result {
  padding: 16px;
  background: #fafafa;
  border-radius: 6px;
}

.test-result h5 {
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 600;
}

.test-data {
  margin-top: 12px;
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  padding: 12px;
  max-height: 200px;
  overflow-y: auto;
}

.test-data pre {
  margin: 0;
  font-family: 'Monaco', 'Consolas', 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 响应式 */
@media (max-width: 768px) {
  .skill-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .test-controls {
    flex-direction: column;
  }
}
</style> 