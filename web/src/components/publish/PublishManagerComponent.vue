<template>
  <div class="publish-manager-component">
    <div class="publish-header">
      <h2 class="publish-title">发布渠道</h2>
      <p class="publish-description">管理智能体的发布渠道和接入方式</p>
    </div>
    
    <div class="publish-content">
      <div class="tab-navigation">
        <div 
          v-for="tab in tabs" 
          :key="tab.key" 
          :class="['tab-item', { active: activeTab === tab.key }]"
          @click="activeTab = tab.key"
        >
          <span class="tab-icon"><component :is="tab.icon" /></span>
          <span class="tab-label">{{ tab.label }}</span>
        </div>
      </div>
      
      <div class="tab-content">
        <transition name="fade" mode="out-in">
          <div v-if="activeTab === 'channels'" key="channels" class="tab-pane">
            <PublishChannelComponent 
              :agent-id="agentId" 
              :channels="channels"
              @update:channels="updateChannels"
              @change="handleChannelsChange"
            />
          </div>
          
          <div v-else-if="activeTab === 'api'" key="api" class="tab-pane">
            <ApiSettingsComponent 
              :agent-id="agentId"
              :settings="apiSettings"
              @update:settings="updateApiSettings"
              @change="handleApiSettingsChange"
            />
          </div>
          
          <div v-else-if="activeTab === 'embed'" key="embed" class="tab-pane">
            <EmbedCodeComponent 
              :agent-id="agentId"
              :settings="embedSettings"
              @update:settings="updateEmbedSettings"
              @change="handleEmbedSettingsChange"
            />
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { GlobalOutlined, ApiOutlined, CodeOutlined } from '@ant-design/icons-vue';
import PublishChannelComponent from './PublishChannelComponent.vue';
import ApiSettingsComponent from './ApiSettingsComponent.vue';
import EmbedCodeComponent from './EmbedCodeComponent.vue';

const props = defineProps({
  agentId: {
    type: String,
    required: true
  }
});

const emit = defineEmits(['update:publishConfig', 'change']);

// 标签页配置
const tabs = [
  { key: 'channels', label: '发布渠道', icon: GlobalOutlined },
  { key: 'api', label: 'API 接口', icon: ApiOutlined },
  { key: 'embed', label: '网站嵌入', icon: CodeOutlined }
];

// 当前激活的标签页
const activeTab = ref('channels');

// 渠道列表
const channels = ref([]);

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

// 更新渠道列表
const updateChannels = (newChannels) => {
  channels.value = newChannels;
  updatePublishConfig();
};

// 更新 API 设置
const updateApiSettings = (newSettings) => {
  Object.assign(apiSettings, newSettings);
  updatePublishConfig();
};

// 更新嵌入设置
const updateEmbedSettings = (newSettings) => {
  Object.assign(embedSettings, newSettings);
  updatePublishConfig();
};

// 处理渠道变更
const handleChannelsChange = (newChannels) => {
  updateChannels(newChannels);
};

// 处理 API 设置变更
const handleApiSettingsChange = (newSettings) => {
  updateApiSettings(newSettings);
};

// 处理嵌入设置变更
const handleEmbedSettingsChange = (newSettings) => {
  updateEmbedSettings(newSettings);
};

// 更新发布配置
const updatePublishConfig = () => {
  const publishConfig = {
    channels: channels.value,
    api_settings: { ...apiSettings },
    embed_settings: { ...embedSettings }
  };
  
  emit('update:publishConfig', publishConfig);
  emit('change', publishConfig);
};

// 加载发布配置
const loadPublishConfig = async () => {
  try {
    // 这里应该调用 API 获取发布配置
    // const response = await getPublishConfig(props.agentId);
    // if (response.success) {
    //   channels.value = response.data.channels || [];
    //   Object.assign(apiSettings, response.data.api_settings || {});
    //   Object.assign(embedSettings, response.data.embed_settings || {});
    // }
    
    // 模拟 API 数据
    channels.value = [
      {
        id: 'channel_1',
        type: 'web',
        name: '网页访问',
        description: '通过网页链接访问智能体',
        status: 'active',
        config: {
          access_type: 'public',
          url: `https://yuxi.ai/agent/${props.agentId}`
        }
      },
      {
        id: 'channel_2',
        type: 'api',
        name: 'API接口',
        description: '通过API接口调用智能体',
        status: 'inactive',
        config: {
          api_key: 'sk-api-example12345',
          rate_limit: 100
        }
      }
    ];
    
    Object.assign(apiSettings, {
      enabled: true,
      api_key: 'sk-yuxi-example12345678901234567890',
      rate_limit: 100,
      ip_whitelist_mode: 'none',
      ip_whitelist: '',
      origin_mode: 'none',
      origin_whitelist: ''
    });
    
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
    console.error('加载发布配置失败:', error);
    message.error('加载发布配置失败');
  }
};

onMounted(() => {
  loadPublishConfig();
});
</script>

<style scoped>
.publish-manager-component {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #fff;
  border-radius: 8px;
}

.publish-header {
  padding: 24px 32px;
  border-bottom: 1px solid #f0f0f0;
}

.publish-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  color: #262626;
}

.publish-description {
  margin: 8px 0 0;
  color: #8c8c8c;
  font-size: 14px;
}

.publish-content {
  display: flex;
  flex: 1;
  height: calc(100vh - 220px);
}

.tab-navigation {
  width: 200px;
  border-right: 1px solid #f0f0f0;
  background-color: #fafafa;
  padding: 16px 0;
}

.tab-item {
  display: flex;
  align-items: center;
  padding: 12px 24px;
  cursor: pointer;
  transition: all 0.3s;
  color: #595959;
  border-left: 3px solid transparent;
}

.tab-item:hover {
  color: #1890ff;
  background-color: #e6f7ff;
}

.tab-item.active {
  color: #1890ff;
  background-color: #e6f7ff;
  border-left: 3px solid #1890ff;
}

.tab-icon {
  margin-right: 12px;
  font-size: 16px;
  display: flex;
  align-items: center;
}

.tab-label {
  font-size: 14px;
  font-weight: 500;
}

.tab-content {
  flex: 1;
  padding: 24px 32px;
  overflow-y: auto;
}

.tab-pane {
  height: 100%;
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
