<template>
  <div class="api-settings-component">
    <div class="settings-header">
      <h3>API 接口设置</h3>
      <p>配置智能体的 API 接口参数，用于第三方系统集成</p>
    </div>

    <a-card class="settings-card">
      <a-form layout="vertical" :model="apiSettings">
        <a-form-item label="API 状态">
          <a-switch 
            v-model:checked="apiSettings.enabled" 
            @change="handleStatusChange"
          />
          <span class="status-text">{{ apiSettings.enabled ? '已启用' : '已禁用' }}</span>
        </a-form-item>

        <a-divider />

        <div class="settings-content" :class="{ disabled: !apiSettings.enabled }">
          <a-form-item label="API 密钥">
            <div class="api-key-field">
              <a-input-password 
                v-model:value="apiSettings.api_key" 
                :disabled="true"
                placeholder="API 密钥将自动生成"
              />
              <a-button 
                type="primary" 
                :disabled="!apiSettings.enabled"
                @click="regenerateApiKey"
              >
                重新生成
              </a-button>
              <a-button 
                type="text" 
                :disabled="!apiSettings.enabled"
                @click="copyApiKey"
              >
                <template #icon><CopyOutlined /></template>
                复制
              </a-button>
            </div>
          </a-form-item>

          <a-form-item label="调用频率限制">
            <a-input-number 
              v-model:value="apiSettings.rate_limit" 
              :min="1" 
              :max="1000"
              :disabled="!apiSettings.enabled"
              style="width: 100%"
              placeholder="每分钟最大调用次数"
              addon-after="次/分钟"
            />
          </a-form-item>

          <a-form-item label="IP 白名单">
            <a-select
              v-model:value="apiSettings.ip_whitelist_mode"
              :disabled="!apiSettings.enabled"
              style="width: 100%"
            >
              <a-select-option value="none">不限制 IP</a-select-option>
              <a-select-option value="whitelist">启用 IP 白名单</a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item v-if="apiSettings.ip_whitelist_mode === 'whitelist'">
            <a-textarea
              v-model:value="apiSettings.ip_whitelist"
              :disabled="!apiSettings.enabled"
              placeholder="请输入允许访问的 IP 地址，每行一个"
              :auto-size="{ minRows: 3, maxRows: 6 }"
            />
            <div class="form-help-text">每行输入一个 IP 地址，支持 IPv4 和 IPv6</div>
          </a-form-item>

          <a-form-item label="请求来源限制">
            <a-select
              v-model:value="apiSettings.origin_mode"
              :disabled="!apiSettings.enabled"
              style="width: 100%"
            >
              <a-select-option value="none">不限制来源</a-select-option>
              <a-select-option value="whitelist">启用来源白名单</a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item v-if="apiSettings.origin_mode === 'whitelist'">
            <a-textarea
              v-model:value="apiSettings.origin_whitelist"
              :disabled="!apiSettings.enabled"
              placeholder="请输入允许的域名，每行一个，例如：https://example.com"
              :auto-size="{ minRows: 3, maxRows: 6 }"
            />
            <div class="form-help-text">每行输入一个域名，必须包含协议前缀（http:// 或 https://）</div>
          </a-form-item>

          <a-divider />

          <div class="api-documentation">
            <h4>API 文档</h4>
            <p>使用以下接口调用您的智能体：</p>
            
            <div class="code-block">
              <div class="code-header">
                <span>请求示例</span>
                <a-button type="text" size="small" @click="copyCode">
                  <template #icon><CopyOutlined /></template>
                  复制
                </a-button>
              </div>
              <pre><code>curl -X POST "{{ apiEndpoint }}"
  -H "Content-Type: application/json"
  -H "Authorization: Bearer {{ apiSettings.api_key }}"
  -d '{
    "message": "你好，智能体",
    "conversation_id": "optional-conversation-id"
  }'</code></pre>
            </div>

            <div class="api-params">
              <h5>参数说明</h5>
              <ul>
                <li><strong>message</strong>: 发送给智能体的消息内容</li>
                <li><strong>conversation_id</strong>: (可选) 对话 ID，用于维持对话上下文</li>
              </ul>
            </div>
          </div>
        </div>
      </a-form>

      <div class="settings-actions">
        <a-button type="primary" @click="saveSettings" :loading="saving">保存设置</a-button>
      </div>
    </a-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { CopyOutlined } from '@ant-design/icons-vue';

const props = defineProps({
  agentId: {
    type: String,
    required: true
  }
});

const emit = defineEmits(['update:settings', 'change']);

// API 设置
const apiSettings = reactive({
  enabled: false,
  api_key: '',
  rate_limit: 60,
  ip_whitelist_mode: 'none',
  ip_whitelist: '',
  origin_mode: 'none',
  origin_whitelist: ''
});

// 状态
const saving = ref(false);

// API 端点
const apiEndpoint = computed(() => {
  return `https://api.yuxi.ai/v1/agents/${props.agentId}/chat`;
});

// 处理状态变更
const handleStatusChange = (checked) => {
  if (checked && !apiSettings.api_key) {
    // 如果启用且没有 API 密钥，则生成一个
    apiSettings.api_key = generateApiKey();
  }
};

// 生成 API 密钥
const generateApiKey = () => {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  const prefix = 'sk-yuxi-';
  let result = prefix;
  for (let i = 0; i < 24; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
};

// 重新生成 API 密钥
const regenerateApiKey = () => {
  apiSettings.api_key = generateApiKey();
  message.success('API 密钥已重新生成');
};

// 复制 API 密钥
const copyApiKey = () => {
  navigator.clipboard.writeText(apiSettings.api_key)
    .then(() => {
      message.success('API 密钥已复制到剪贴板');
    })
    .catch(() => {
      message.error('复制失败，请手动复制');
    });
};

// 复制代码示例
const copyCode = () => {
  const code = `curl -X POST "${apiEndpoint.value}"
  -H "Content-Type: application/json"
  -H "Authorization: Bearer ${apiSettings.api_key}"
  -d '{
    "message": "你好，智能体",
    "conversation_id": "optional-conversation-id"
  }'`;

  navigator.clipboard.writeText(code)
    .then(() => {
      message.success('代码示例已复制到剪贴板');
    })
    .catch(() => {
      message.error('复制失败，请手动复制');
    });
};

// 保存设置
const saveSettings = async () => {
  try {
    saving.value = true;
    
    // 这里应该调用 API 保存设置
    // await saveApiSettings(props.agentId, apiSettings);
    
    // 模拟 API 调用
    await new Promise(resolve => setTimeout(resolve, 500));
    
    emit('update:settings', { ...apiSettings });
    emit('change', { ...apiSettings });
    
    message.success('API 设置已保存');
  } catch (error) {
    console.error('保存 API 设置失败:', error);
    message.error('保存 API 设置失败');
  } finally {
    saving.value = false;
  }
};

// 加载设置
const loadSettings = async () => {
  try {
    // 这里应该调用 API 获取设置
    // const response = await getApiSettings(props.agentId);
    // Object.assign(apiSettings, response.data);
    
    // 模拟 API 数据
    Object.assign(apiSettings, {
      enabled: true,
      api_key: 'sk-yuxi-example12345678901234567890',
      rate_limit: 100,
      ip_whitelist_mode: 'none',
      ip_whitelist: '',
      origin_mode: 'none',
      origin_whitelist: ''
    });
  } catch (error) {
    console.error('加载 API 设置失败:', error);
    message.error('加载 API 设置失败');
  }
};

onMounted(() => {
  loadSettings();
});
</script>

<style scoped>
.api-settings-component {
  height: 100%;
}

.settings-header {
  margin-bottom: 24px;
}

.settings-header h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #262626;
}

.settings-header p {
  color: #8c8c8c;
  margin: 0;
  font-size: 14px;
}

.settings-card {
  margin-bottom: 24px;
}

.status-text {
  margin-left: 8px;
  color: #8c8c8c;
}

.settings-content.disabled {
  opacity: 0.6;
}

.api-key-field {
  display: flex;
  gap: 8px;
}

.form-help-text {
  font-size: 12px;
  color: #8c8c8c;
  margin-top: 4px;
}

.api-documentation {
  margin-top: 16px;
}

.api-documentation h4 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
}

.api-documentation p {
  margin-bottom: 12px;
}

.code-block {
  background-color: #f5f5f5;
  border-radius: 4px;
  margin-bottom: 16px;
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background-color: #e8e8e8;
  border-top-left-radius: 4px;
  border-top-right-radius: 4px;
}

.code-header span {
  font-weight: 500;
}

.code-block pre {
  margin: 0;
  padding: 12px;
  overflow-x: auto;
}

.code-block pre code {
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace;
  white-space: pre;
}

.api-params h5 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
}

.api-params ul {
  padding-left: 20px;
}

.api-params ul li {
  margin-bottom: 4px;
}

.settings-actions {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}
</style>
