<template>
  <div class="embed-code-component">
    <div class="embed-header">
      <h3>网站嵌入代码</h3>
      <p>将智能体嵌入到您的网站中，为访客提供智能对话服务</p>
    </div>

    <a-card class="embed-card">
      <a-form layout="vertical" :model="embedSettings">
        <a-form-item label="嵌入状态">
          <a-switch 
            v-model:checked="embedSettings.enabled" 
            @change="handleStatusChange"
          />
          <span class="status-text">{{ embedSettings.enabled ? '已启用' : '已禁用' }}</span>
        </a-form-item>

        <a-divider />

        <div class="embed-content" :class="{ disabled: !embedSettings.enabled }">
          <a-form-item label="嵌入模式">
            <a-radio-group v-model:value="embedSettings.mode" :disabled="!embedSettings.enabled">
              <a-radio value="chat">聊天窗口</a-radio>
              <a-radio value="button">悬浮按钮</a-radio>
              <a-radio value="inline">内联嵌入</a-radio>
            </a-radio-group>
          </a-form-item>

          <a-form-item label="允许的域名">
            <a-textarea
              v-model:value="embedSettings.allowed_domains"
              :disabled="!embedSettings.enabled"
              placeholder="请输入允许嵌入的域名，每行一个，例如：example.com"
              :auto-size="{ minRows: 3, maxRows: 6 }"
            />
            <div class="form-help-text">每行输入一个域名，不需要包含协议前缀。留空表示允许所有域名</div>
          </a-form-item>

          <a-divider />

          <div class="appearance-settings">
            <h4>外观设置</h4>
            
            <a-row :gutter="16">
              <a-col :span="12">
                <a-form-item label="主题颜色">
                  <a-input 
                    v-model:value="embedSettings.theme_color" 
                    :disabled="!embedSettings.enabled"
                    placeholder="#1890ff"
                    addon-before="#"
                  />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="位置">
                  <a-select 
                    v-model:value="embedSettings.position" 
                    :disabled="!embedSettings.enabled || embedSettings.mode === 'inline'"
                  >
                    <a-select-option value="bottom-right">右下角</a-select-option>
                    <a-select-option value="bottom-left">左下角</a-select-option>
                    <a-select-option value="top-right">右上角</a-select-option>
                    <a-select-option value="top-left">左上角</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
            </a-row>

            <a-row :gutter="16">
              <a-col :span="12">
                <a-form-item label="欢迎语">
                  <a-input 
                    v-model:value="embedSettings.welcome_message" 
                    :disabled="!embedSettings.enabled"
                    placeholder="您好！有什么可以帮助您的吗？"
                  />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="按钮文本">
                  <a-input 
                    v-model:value="embedSettings.button_text" 
                    :disabled="!embedSettings.enabled || embedSettings.mode !== 'button'"
                    placeholder="联系客服"
                  />
                </a-form-item>
              </a-col>
            </a-row>

            <a-form-item label="窗口标题">
              <a-input 
                v-model:value="embedSettings.window_title" 
                :disabled="!embedSettings.enabled"
                placeholder="智能客服"
              />
            </a-form-item>
          </div>

          <a-divider />

          <div class="embed-preview">
            <h4>预览</h4>
            <div class="preview-container">
              <div class="preview-frame" :class="embedSettings.mode">
                <div 
                  class="chat-window" 
                  v-if="embedSettings.mode === 'chat' || (embedSettings.mode === 'button' && showPreviewChat)"
                  :style="{ 
                    borderColor: embedSettings.theme_color ? `#${embedSettings.theme_color}` : '#1890ff'
                  }"
                >
                  <div class="chat-header" :style="{ 
                    backgroundColor: embedSettings.theme_color ? `#${embedSettings.theme_color}` : '#1890ff'
                  }">
                    {{ embedSettings.window_title || '智能客服' }}
                  </div>
                  <div class="chat-body">
                    <div class="chat-message bot">
                      <div class="message-content">
                        {{ embedSettings.welcome_message || '您好！有什么可以帮助您的吗？' }}
                      </div>
                    </div>
                  </div>
                  <div class="chat-input">
                    <input type="text" placeholder="输入消息..." disabled />
                    <button :style="{ 
                      backgroundColor: embedSettings.theme_color ? `#${embedSettings.theme_color}` : '#1890ff'
                    }">发送</button>
                  </div>
                </div>
                
                <div 
                  class="chat-button" 
                  v-if="embedSettings.mode === 'button'"
                  @click="togglePreviewChat"
                  :style="{ 
                    backgroundColor: embedSettings.theme_color ? `#${embedSettings.theme_color}` : '#1890ff',
                    [embedSettings.position.split('-')[0]]: '20px',
                    [embedSettings.position.split('-')[1]]: '20px'
                  }"
                >
                  {{ embedSettings.button_text || '联系客服' }}
                </div>
                
                <div 
                  class="inline-chat" 
                  v-if="embedSettings.mode === 'inline'"
                  :style="{ 
                    borderColor: embedSettings.theme_color ? `#${embedSettings.theme_color}` : '#1890ff'
                  }"
                >
                  <div class="chat-header" :style="{ 
                    backgroundColor: embedSettings.theme_color ? `#${embedSettings.theme_color}` : '#1890ff'
                  }">
                    {{ embedSettings.window_title || '智能客服' }}
                  </div>
                  <div class="chat-body">
                    <div class="chat-message bot">
                      <div class="message-content">
                        {{ embedSettings.welcome_message || '您好！有什么可以帮助您的吗？' }}
                      </div>
                    </div>
                  </div>
                  <div class="chat-input">
                    <input type="text" placeholder="输入消息..." disabled />
                    <button :style="{ 
                      backgroundColor: embedSettings.theme_color ? `#${embedSettings.theme_color}` : '#1890ff'
                    }">发送</button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <a-divider />

          <div class="embed-code">
            <div class="code-header">
              <h4>嵌入代码</h4>
              <a-button type="primary" size="small" @click="copyEmbedCode">
                <template #icon><CopyOutlined /></template>
                复制代码
              </a-button>
            </div>
            <a-alert 
              v-if="embedSettings.allowed_domains && embedSettings.allowed_domains.trim() !== ''" 
              message="注意：只有在允许的域名列表中的网站才能使用此嵌入代码" 
              type="info" 
              show-icon 
              style="margin-bottom: 16px"
            />
            <div class="code-block">
              <pre><code>{{ generateEmbedCode() }}</code></pre>
            </div>
          </div>
        </div>
      </a-form>

      <div class="embed-actions">
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

// 嵌入设置
const embedSettings = reactive({
  enabled: false,
  mode: 'chat',
  allowed_domains: '',
  theme_color: '1890ff',
  position: 'bottom-right',
  welcome_message: '您好！有什么可以帮助您的吗？',
  button_text: '联系客服',
  window_title: '智能客服'
});

// 状态
const saving = ref(false);
const showPreviewChat = ref(false);

// 处理状态变更
const handleStatusChange = (checked) => {
  // 可以在这里添加额外的逻辑
};

// 切换预览聊天窗口
const togglePreviewChat = () => {
  showPreviewChat.value = !showPreviewChat.value;
};

// 生成嵌入代码
const generateEmbedCode = () => {
  if (!embedSettings.enabled) {
    return '// 请先启用嵌入功能';
  }

  return `<script src="https://cdn.yuxi.ai/embed.js" id="yuxi-embed" 
  data-agent-id="${props.agentId}"
  data-mode="${embedSettings.mode}"
  data-position="${embedSettings.position}"
  data-theme-color="${embedSettings.theme_color}"
  data-welcome-message="${embedSettings.welcome_message}"
  data-button-text="${embedSettings.button_text}"
  data-window-title="${embedSettings.window_title}">
<\/script>`;
};

// 复制嵌入代码
const copyEmbedCode = () => {
  navigator.clipboard.writeText(generateEmbedCode())
    .then(() => {
      message.success('嵌入代码已复制到剪贴板');
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
    // await saveEmbedSettings(props.agentId, embedSettings);
    
    // 模拟 API 调用
    await new Promise(resolve => setTimeout(resolve, 500));
    
    emit('update:settings', { ...embedSettings });
    emit('change', { ...embedSettings });
    
    message.success('嵌入设置已保存');
  } catch (error) {
    console.error('保存嵌入设置失败:', error);
    message.error('保存嵌入设置失败');
  } finally {
    saving.value = false;
  }
};

// 加载设置
const loadSettings = async () => {
  try {
    // 这里应该调用 API 获取设置
    // const response = await getEmbedSettings(props.agentId);
    // Object.assign(embedSettings, response.data);
    
    // 模拟 API 数据
    Object.assign(embedSettings, {
      enabled: true,
      mode: 'button',
      allowed_domains: 'example.com\nyourwebsite.com',
      theme_color: '1890ff',
      position: 'bottom-right',
      welcome_message: '您好！我是智能助手，有什么可以帮您？',
      button_text: '咨询智能助手',
      window_title: '智能客服'
    });
  } catch (error) {
    console.error('加载嵌入设置失败:', error);
    message.error('加载嵌入设置失败');
  }
};

onMounted(() => {
  loadSettings();
});
</script>

<style scoped>
.embed-code-component {
  height: 100%;
}

.embed-header {
  margin-bottom: 24px;
}

.embed-header h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #262626;
}

.embed-header p {
  color: #8c8c8c;
  margin: 0;
  font-size: 14px;
}

.embed-card {
  margin-bottom: 24px;
}

.status-text {
  margin-left: 8px;
  color: #8c8c8c;
}

.embed-content.disabled {
  opacity: 0.6;
}

.form-help-text {
  font-size: 12px;
  color: #8c8c8c;
  margin-top: 4px;
}

.appearance-settings h4 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
}

.embed-preview {
  margin-bottom: 24px;
}

.embed-preview h4 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
}

.preview-container {
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  padding: 16px;
  background-color: #fafafa;
  height: 400px;
  position: relative;
  overflow: hidden;
}

.preview-frame {
  position: relative;
  width: 100%;
  height: 100%;
}

.preview-frame.button .chat-window {
  position: absolute;
  bottom: 80px;
  right: 20px;
  width: 320px;
  height: 400px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  border-radius: 8px;
  overflow: hidden;
  background-color: white;
  border: 1px solid #1890ff;
  display: flex;
  flex-direction: column;
}

.preview-frame.chat .chat-window {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 320px;
  height: 400px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  border-radius: 8px;
  overflow: hidden;
  background-color: white;
  border: 1px solid #1890ff;
  display: flex;
  flex-direction: column;
}

.preview-frame.inline .inline-chat {
  width: 100%;
  height: 100%;
  border: 1px solid #1890ff;
  border-radius: 8px;
  overflow: hidden;
  background-color: white;
  display: flex;
  flex-direction: column;
}

.chat-button {
  position: absolute;
  padding: 8px 16px;
  border-radius: 20px;
  background-color: #1890ff;
  color: white;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  font-size: 14px;
  font-weight: 500;
  z-index: 10;
}

.chat-header {
  background-color: #1890ff;
  color: white;
  padding: 12px 16px;
  font-weight: 500;
  font-size: 14px;
}

.chat-body {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  background-color: #f9f9f9;
}

.chat-message {
  margin-bottom: 12px;
  display: flex;
}

.chat-message.bot {
  justify-content: flex-start;
}

.chat-message.bot .message-content {
  background-color: white;
  border: 1px solid #e8e8e8;
  border-radius: 8px 8px 8px 0;
}

.chat-message.user {
  justify-content: flex-end;
}

.chat-message.user .message-content {
  background-color: #e6f7ff;
  border: 1px solid #91d5ff;
  border-radius: 8px 8px 0 8px;
}

.message-content {
  padding: 8px 12px;
  max-width: 80%;
  word-break: break-word;
}

.chat-input {
  display: flex;
  padding: 8px;
  border-top: 1px solid #f0f0f0;
  background-color: white;
}

.chat-input input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  margin-right: 8px;
  outline: none;
}

.chat-input input:focus {
  border-color: #40a9ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.chat-input button {
  padding: 0 16px;
  background-color: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.chat-input button:hover {
  background-color: #40a9ff;
}

.embed-code .code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.embed-code .code-header h4 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
}

.code-block {
  background-color: #f5f5f5;
  border-radius: 4px;
  padding: 16px;
  overflow-x: auto;
}

.code-block pre {
  margin: 0;
}

.code-block pre code {
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace;
  white-space: pre-wrap;
  word-break: break-all;
}

.embed-actions {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}
</style>
