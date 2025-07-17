<template>
  <div class="publish-channel-component">
    <div class="channel-header">
      <h3>发布渠道管理</h3>
      <p>将您的智能体发布到不同的渠道，让更多人使用</p>
    </div>

    <div class="channel-list">
      <a-empty v-if="channels.length === 0" description="暂无发布渠道">
        <template #extra>
          <a-button type="primary" @click="showAddChannelModal">添加渠道</a-button>
        </template>
      </a-empty>

      <div v-else class="channel-cards">
        <a-card v-for="channel in channels" :key="channel.id" class="channel-card">
          <template #cover>
            <div class="channel-cover" :class="channel.type">
              <component :is="getChannelIcon(channel.type)" class="channel-icon" />
            </div>
          </template>
          <a-card-meta :title="channel.name">
            <template #description>
              <div class="channel-description">
                <p>{{ channel.description }}</p>
                <a-tag :color="getStatusColor(channel.status)">{{ getStatusText(channel.status) }}</a-tag>
              </div>
            </template>
          </a-card-meta>
          <div class="channel-actions">
            <a-button type="text" @click="editChannel(channel)">
              <template #icon><EditOutlined /></template>
              编辑
            </a-button>
            <a-button type="text" @click="toggleChannelStatus(channel)">
              <template #icon>
                <component :is="channel.status === 'active' ? 'PauseCircleOutlined' : 'PlayCircleOutlined'" />
              </template>
              {{ channel.status === 'active' ? '暂停' : '启用' }}
            </a-button>
            <a-button type="text" danger @click="confirmDeleteChannel(channel)">
              <template #icon><DeleteOutlined /></template>
              删除
            </a-button>
          </div>
        </a-card>

        <div class="add-channel-card">
          <a-button type="dashed" block @click="showAddChannelModal">
            <PlusOutlined /> 添加渠道
          </a-button>
        </div>
      </div>
    </div>

    <!-- 添加/编辑渠道弹窗 -->
    <a-modal
      :visible="channelModalVisible"
      :title="isEditing ? '编辑渠道' : '添加渠道'"
      @update:visible="channelModalVisible = $event"
      @ok="handleChannelSubmit"
      @cancel="handleChannelCancel"
      :confirmLoading="submitting"
    >
      <a-form :model="channelForm" :rules="channelRules" ref="channelFormRef" layout="vertical">
        <a-form-item name="type" label="渠道类型">
          <a-select v-model:value="channelForm.type" placeholder="请选择渠道类型" :disabled="isEditing">
            <a-select-option value="web">网页链接</a-select-option>
            <a-select-option value="api">API接口</a-select-option>
            <a-select-option value="wechat">微信公众号</a-select-option>
            <a-select-option value="dingtalk">钉钉机器人</a-select-option>
            <a-select-option value="feishu">飞书机器人</a-select-option>
          </a-select>
        </a-form-item>
        
        <a-form-item name="name" label="渠道名称">
          <a-input v-model:value="channelForm.name" placeholder="请输入渠道名称" />
        </a-form-item>
        
        <a-form-item name="description" label="渠道描述">
          <a-textarea v-model:value="channelForm.description" placeholder="请输入渠道描述" :auto-size="{ minRows: 2, maxRows: 4 }" />
        </a-form-item>

        <!-- 根据不同渠道类型显示不同的配置项 -->
        <template v-if="channelForm.type === 'web'">
          <a-form-item name="config.url" label="访问链接">
            <a-input v-model:value="channelForm.config.url" placeholder="系统生成的访问链接" disabled />
          </a-form-item>
          <a-form-item name="config.access_type" label="访问权限">
            <a-radio-group v-model:value="channelForm.config.access_type">
              <a-radio value="public">公开访问</a-radio>
              <a-radio value="private">需要登录</a-radio>
              <a-radio value="password">密码访问</a-radio>
            </a-radio-group>
          </a-form-item>
          <a-form-item v-if="channelForm.config.access_type === 'password'" name="config.password" label="访问密码">
            <a-input-password v-model:value="channelForm.config.password" placeholder="请设置访问密码" />
          </a-form-item>
        </template>

        <template v-else-if="channelForm.type === 'api'">
          <a-form-item name="config.api_key" label="API密钥">
            <a-input-password v-model:value="channelForm.config.api_key" placeholder="系统生成的API密钥" disabled>
              <template #addonAfter>
                <a-button type="link" size="small" @click="regenerateApiKey">重新生成</a-button>
              </template>
            </a-input-password>
          </a-form-item>
          <a-form-item name="config.rate_limit" label="调用频率限制">
            <a-input-number v-model:value="channelForm.config.rate_limit" placeholder="每分钟最大调用次数" style="width: 100%" />
          </a-form-item>
        </template>

        <template v-else-if="['wechat', 'dingtalk', 'feishu'].includes(channelForm.type)">
          <a-form-item name="config.webhook" label="Webhook地址">
            <a-input v-model:value="channelForm.config.webhook" placeholder="请输入Webhook地址" />
          </a-form-item>
          <a-form-item name="config.token" label="验证Token">
            <a-input v-model:value="channelForm.config.token" placeholder="请输入验证Token" />
          </a-form-item>
        </template>
      </a-form>
    </a-modal>

    <!-- 删除确认弹窗 -->
    <a-modal
      :visible="deleteModalVisible"
      title="删除渠道"
      @update:visible="deleteModalVisible = $event"
      @ok="handleDeleteConfirm"
      @cancel="deleteModalVisible = false"
      :okButtonProps="{ danger: true, loading: deleting }"
      okText="删除"
      cancelText="取消"
    >
      <p>确定要删除渠道 "{{ currentChannel?.name }}" 吗？此操作不可恢复。</p>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { 
  EditOutlined, DeleteOutlined, PlusOutlined, 
  PlayCircleOutlined, PauseCircleOutlined,
  GlobalOutlined, ApiOutlined, WechatOutlined, DingtalkOutlined, RobotOutlined
} from '@ant-design/icons-vue';

const props = defineProps({
  agentId: {
    type: String,
    required: true
  }
});

const emit = defineEmits(['update:channels', 'change']);

// 渠道列表
const channels = ref([]);

// 添加/编辑渠道弹窗
const channelModalVisible = ref(false);
const isEditing = ref(false);
const submitting = ref(false);
const channelFormRef = ref(null);

// 删除确认弹窗
const deleteModalVisible = ref(false);
const deleting = ref(false);
const currentChannel = ref(null);

// 渠道表单
const channelForm = reactive({
  id: '',
  type: 'web',
  name: '',
  description: '',
  status: 'inactive',
  config: {
    access_type: 'public',
    password: '',
    url: '',
    api_key: '',
    rate_limit: 60,
    webhook: '',
    token: ''
  }
});

// 表单验证规则
const channelRules = {
  type: [{ required: true, message: '请选择渠道类型' }],
  name: [{ required: true, message: '请输入渠道名称' }],
  description: [{ required: true, message: '请输入渠道描述' }],
  'config.webhook': [{ required: true, message: '请输入Webhook地址', trigger: 'blur' }],
  'config.token': [{ required: true, message: '请输入验证Token', trigger: 'blur' }],
  'config.password': [{ required: true, message: '请设置访问密码', trigger: 'blur' }],
  'config.rate_limit': [{ required: true, message: '请设置调用频率限制', type: 'number' }]
};

// 获取渠道图标
const getChannelIcon = (type) => {
  const iconMap = {
    web: GlobalOutlined,
    api: ApiOutlined,
    wechat: WechatOutlined,
    dingtalk: DingtalkOutlined,
    feishu: RobotOutlined
  };
  return iconMap[type] || GlobalOutlined;
};

// 获取状态颜色
const getStatusColor = (status) => {
  return status === 'active' ? 'green' : 'orange';
};

// 获取状态文本
const getStatusText = (status) => {
  return status === 'active' ? '已启用' : '未启用';
};

// 显示添加渠道弹窗
const showAddChannelModal = () => {
  isEditing.value = false;
  resetChannelForm();
  // 生成默认值
  channelForm.config.url = `https://yuxi.ai/agent/${props.agentId}`;
  channelForm.config.api_key = generateRandomApiKey();
  channelModalVisible.value = true;
};

// 编辑渠道
const editChannel = (channel) => {
  isEditing.value = true;
  Object.assign(channelForm, JSON.parse(JSON.stringify(channel)));
  channelModalVisible.value = true;
};

// 切换渠道状态
const toggleChannelStatus = async (channel) => {
  try {
    const newStatus = channel.status === 'active' ? 'inactive' : 'active';
    // 这里应该调用API更新状态
    // await updateChannelStatus(channel.id, newStatus);
    
    // 模拟API调用
    const updatedChannels = channels.value.map(c => {
      if (c.id === channel.id) {
        return { ...c, status: newStatus };
      }
      return c;
    });
    
    channels.value = updatedChannels;
    emit('update:channels', updatedChannels);
    emit('change', updatedChannels);
    
    message.success(`已${newStatus === 'active' ? '启用' : '暂停'}渠道`);
  } catch (error) {
    console.error('更新渠道状态失败:', error);
    message.error('更新渠道状态失败');
  }
};

// 确认删除渠道
const confirmDeleteChannel = (channel) => {
  currentChannel.value = channel;
  deleteModalVisible.value = true;
};

// 处理删除确认
const handleDeleteConfirm = async () => {
  if (!currentChannel.value) return;
  
  try {
    deleting.value = true;
    // 这里应该调用API删除渠道
    // await deleteChannel(currentChannel.value.id);
    
    // 模拟API调用
    const updatedChannels = channels.value.filter(c => c.id !== currentChannel.value.id);
    channels.value = updatedChannels;
    emit('update:channels', updatedChannels);
    emit('change', updatedChannels);
    
    message.success('渠道已删除');
    deleteModalVisible.value = false;
  } catch (error) {
    console.error('删除渠道失败:', error);
    message.error('删除渠道失败');
  } finally {
    deleting.value = false;
  }
};

// 重置渠道表单
const resetChannelForm = () => {
  channelForm.id = '';
  channelForm.type = 'web';
  channelForm.name = '';
  channelForm.description = '';
  channelForm.status = 'inactive';
  channelForm.config = {
    access_type: 'public',
    password: '',
    url: '',
    api_key: '',
    rate_limit: 60,
    webhook: '',
    token: ''
  };
};

// 生成随机API密钥
const generateRandomApiKey = () => {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  for (let i = 0; i < 32; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
};

// 重新生成API密钥
const regenerateApiKey = () => {
  channelForm.config.api_key = generateRandomApiKey();
};

// 处理渠道表单提交
const handleChannelSubmit = async () => {
  try {
    await channelFormRef.value.validate();
    submitting.value = true;
    
    // 构建保存数据
    const saveData = {
      ...channelForm,
      agent_id: props.agentId
    };
    
    if (isEditing.value) {
      // 这里应该调用API更新渠道
      // await updateChannel(saveData);
      
      // 模拟API调用
      const updatedChannels = channels.value.map(c => {
        if (c.id === channelForm.id) {
          return { ...saveData };
        }
        return c;
      });
      
      channels.value = updatedChannels;
      message.success('渠道已更新');
    } else {
      // 这里应该调用API创建渠道
      // const response = await createChannel(saveData);
      
      // 模拟API调用
      const newChannel = {
        ...saveData,
        id: `channel_${Date.now()}`
      };
      
      channels.value.push(newChannel);
      message.success('渠道已创建');
    }
    
    emit('update:channels', channels.value);
    emit('change', channels.value);
    channelModalVisible.value = false;
  } catch (error) {
    console.error('保存渠道失败:', error);
    message.error('表单验证失败，请检查输入');
  } finally {
    submitting.value = false;
  }
};

// 处理渠道表单取消
const handleChannelCancel = () => {
  channelModalVisible.value = false;
};

// 加载渠道数据
const loadChannels = async () => {
  try {
    // 这里应该调用API获取渠道列表
    // const response = await getChannels(props.agentId);
    // channels.value = response.data || [];
    
    // 模拟API数据
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
  } catch (error) {
    console.error('加载渠道列表失败:', error);
    message.error('加载渠道列表失败');
  }
};

onMounted(() => {
  loadChannels();
});
</script>

<style scoped>
.publish-channel-component {
  height: 100%;
}

.channel-header {
  margin-bottom: 24px;
}

.channel-header h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #262626;
}

.channel-header p {
  color: #8c8c8c;
  margin: 0;
  font-size: 14px;
}

.channel-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.channel-card {
  position: relative;
}

.channel-cover {
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.channel-cover.web { background-color: #e6f7ff; }
.channel-cover.api { background-color: #f6ffed; }
.channel-cover.wechat { background-color: #fcffe6; }
.channel-cover.dingtalk { background-color: #fff2e8; }
.channel-cover.feishu { background-color: #f9f0ff; }

.channel-icon {
  font-size: 48px;
}

.channel-icon.web { color: #1890ff; }
.channel-icon.api { color: #52c41a; }
.channel-icon.wechat { color: #faad14; }
.channel-icon.dingtalk { color: #fa8c16; }
.channel-icon.feishu { color: #722ed1; }

.channel-description {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.channel-description p {
  margin: 0;
  color: #595959;
}

.channel-actions {
  margin-top: 16px;
  display: flex;
  justify-content: space-between;
}

.add-channel-card {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 200px;
  border: 1px dashed #d9d9d9;
  border-radius: 2px;
  background-color: #fafafa;
  transition: all 0.3s;
}

.add-channel-card:hover {
  border-color: #1890ff;
}

</style>
