<template>
  <div class="tool-tester">
    <a-card title="工具函数测试" :bordered="false">
      <template v-if="selectedTool">
        <a-descriptions bordered>
          <a-descriptions-item label="工具名称" :span="3">{{ selectedTool.name }}</a-descriptions-item>
          <a-descriptions-item label="描述" :span="3">{{ selectedTool.description }}</a-descriptions-item>
        </a-descriptions>
        
        <a-divider />
        
        <h3>参数配置</h3>
        <a-form
          :model="formState"
          name="toolTestForm"
          @submit="handleSubmit"
          :label-col="{ span: 4 }"
          :wrapper-col="{ span: 20 }"
        >
          <template v-for="param in selectedTool.parameters" :key="param.name">
            <a-form-item :label="param.name" :name="param.name" :required="param.required">
              <template v-if="param.type === 'string'">
                <a-input v-model:value="formState[param.name]" :placeholder="param.description || ''" />
              </template>
              <template v-else-if="param.type === 'boolean'">
                <a-switch v-model:checked="formState[param.name]" />
              </template>
              <template v-else-if="param.type === 'number' || param.type === 'integer'">
                <a-input-number 
                  v-model:value="formState[param.name]" 
                  style="width: 100%"
                  :placeholder="param.description || ''"
                />
              </template>
              <template v-else-if="param.type === 'array'">
                <a-textarea 
                  v-model:value="arrayInputs[param.name]"
                  :placeholder="'Enter JSON array: ' + (param.description || '')"
                  :rows="3"
                />
                <span class="param-hint">请输入JSON格式数组，如: ["value1", "value2"]</span>
              </template>
              <template v-else-if="param.type === 'object'">
                <a-textarea 
                  v-model:value="objectInputs[param.name]"
                  :placeholder="'Enter JSON object: ' + (param.description || '')"
                  :rows="4"
                />
                <span class="param-hint">请输入JSON格式对象，如: {"key": "value"}</span>
              </template>
              <template v-else>
                <a-input v-model:value="formState[param.name]" :placeholder="param.description || ''" />
              </template>
              <div class="param-description" v-if="param.description">
                {{ param.description }}
              </div>
            </a-form-item>
          </template>
          
          <a-form-item :wrapper-col="{ span: 20, offset: 4 }">
            <a-button type="primary" html-type="submit" :loading="loading">
              执行测试
            </a-button>
          </a-form-item>
        </a-form>
        
        <template v-if="testResults">
          <a-divider />
          <h3>测试结果</h3>
          <div class="test-result">
            <a-alert
              :type="testSuccess ? 'success' : 'error'"
              :message="testSuccess ? '测试成功' : '测试失败'"
              :description="testMessage"
              show-icon
              style="margin-bottom: 16px"
            />
            
            <div class="result-content">
              <a-tabs>
                <a-tab-pane key="formatted" tab="格式化结果">
                  <div class="formatted-result">
                    <pre v-if="formattedResult">{{ formattedResult }}</pre>
                    <a-empty v-else description="无数据" />
                  </div>
                </a-tab-pane>
                <a-tab-pane key="raw" tab="原始响应">
                  <div class="raw-result">
                    <pre>{{ testResults }}</pre>
                  </div>
                </a-tab-pane>
              </a-tabs>
            </div>
          </div>
        </template>
      </template>
      
      <template v-else>
        <div class="tool-selection">
          <p>请先选择一个工具进行测试</p>
          <a-select
            v-model:value="selectedToolId"
            placeholder="选择工具"
            style="width: 100%"
            show-search
            @change="selectTool"
          >
            <a-select-option v-for="tool in tools" :key="tool.id" :value="tool.id">
              {{ tool.name }}
            </a-select-option>
          </a-select>
        </div>
      </template>
    </a-card>
  </div>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue';
import { message } from 'ant-design-vue';

const props = defineProps({
  serverName: {
    type: String,
    required: true
  },
  tools: {
    type: Array,
    default: () => []
  }
});

// 状态
const selectedToolId = ref('');
const selectedTool = ref(null);
const loading = ref(false);
const formState = reactive({});
const arrayInputs = reactive({});
const objectInputs = reactive({});
const testResults = ref(null);
const testSuccess = ref(false);
const testMessage = ref('');

// 计算属性 - 格式化的结果
const formattedResult = computed(() => {
  if (!testResults.value || typeof testResults.value !== 'object') {
    return null;
  }
  
  try {
    // 尝试提取并格式化数据
    if (testResults.value.data) {
      return JSON.stringify(testResults.value.data, null, 2);
    } else {
      return JSON.stringify(testResults.value, null, 2);
    }
  } catch (error) {
    console.error('格式化结果失败:', error);
    return JSON.stringify(testResults.value);
  }
});

// 选择工具
const selectTool = (toolId) => {
  const tool = props.tools.find(t => t.id === toolId);
  if (tool) {
    selectedTool.value = tool;
    resetForm();
  }
};

// 监听工具列表变化
watch(() => props.tools, (newTools) => {
  if (selectedToolId.value && newTools.length > 0) {
    const tool = newTools.find(t => t.id === selectedToolId.value);
    if (tool) {
      selectedTool.value = tool;
      resetForm();
    } else {
      selectedTool.value = null;
    }
  }
}, { deep: true });

// 重置表单
const resetForm = () => {
  // 清空之前的状态
  Object.keys(formState).forEach(key => {
    delete formState[key];
  });
  
  Object.keys(arrayInputs).forEach(key => {
    delete arrayInputs[key];
  });
  
  Object.keys(objectInputs).forEach(key => {
    delete objectInputs[key];
  });
  
  // 为选定工具的每个参数设置默认值
  if (selectedTool.value && selectedTool.value.parameters) {
    selectedTool.value.parameters.forEach(param => {
      if (param.type === 'boolean') {
        formState[param.name] = false;
      } else if (param.type === 'array') {
        arrayInputs[param.name] = '[]';
      } else if (param.type === 'object') {
        objectInputs[param.name] = '{}';
      } else {
        formState[param.name] = '';
      }
    });
  }
  
  // 清空测试结果
  testResults.value = null;
};

// 处理表单提交
const handleSubmit = async (e) => {
  e.preventDefault();
  
  if (!selectedTool.value) {
    message.error('请先选择一个工具');
    return;
  }
  
  // 构建请求参数
  const parameters = { ...formState };
  
  // 解析数组和对象输入
  try {
    Object.keys(arrayInputs).forEach(key => {
      if (arrayInputs[key]) {
        parameters[key] = JSON.parse(arrayInputs[key]);
      }
    });
    
    Object.keys(objectInputs).forEach(key => {
      if (objectInputs[key]) {
        parameters[key] = JSON.parse(objectInputs[key]);
      }
    });
  } catch (error) {
    message.error(`JSON解析错误: ${error.message}`);
    return;
  }
  
  // 验证必填参数
  const missingParams = selectedTool.value.parameters
    .filter(param => param.required && !parameters[param.name])
    .map(param => param.name);
    
  if (missingParams.length > 0) {
    message.error(`请填写必填参数: ${missingParams.join(', ')}`);
    return;
  }
  
  // 发送测试请求
  loading.value = true;
  testResults.value = null;
  testSuccess.value = false;
  testMessage.value = '';
  
  try {
    const response = await fetch(`/api/mcp/servers/${props.serverName}/tools/${selectedTool.value.id}/test`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ parameters })
    });
    
    const data = await response.json();
    testResults.value = data;
    testSuccess.value = data.success === true;
    testMessage.value = data.message || (testSuccess.value ? '测试成功' : '测试失败');
    
    if (testSuccess.value) {
      message.success('工具测试成功');
    } else {
      message.error(`工具测试失败: ${testMessage.value}`);
    }
  } catch (error) {
    console.error('工具测试请求出错:', error);
    testSuccess.value = false;
    testMessage.value = `请求错误: ${error.message}`;
    message.error('工具测试请求出错');
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped lang="less">
.tool-tester {
  margin-bottom: 24px;
}

.tool-selection {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  
  p {
    margin-bottom: 16px;
  }
}

.param-description {
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
  margin-top: 4px;
}

.param-hint {
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
  display: block;
  margin-top: 4px;
}

.test-result {
  margin-top: 16px;
  
  .result-content {
    margin-top: 16px;
    
    .formatted-result,
    .raw-result {
      margin-top: 8px;
      
      pre {
        background-color: #f5f5f5;
        padding: 12px;
        border-radius: 4px;
        overflow: auto;
        max-height: 400px;
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'source-code-pro', monospace;
        font-size: 13px;
      }
    }
  }
}
</style>
