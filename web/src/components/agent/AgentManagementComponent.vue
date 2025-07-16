<template>
  <div class="agent-management">
    <div class="header">
      <h3>智能体管理</h3>
      <a-button type="primary" @click="showAddModal = true">新增智能体</a-button>
    </div>
    <div class="agent-card-list">
      <a-card
        v-for="item in agents"
        :key="item.agent_id"
        class="agent-card"
        :hoverable="true"
      >
        <template #actions>
          <span @click="startChat(item)" title="开始对话"><MessageOutlined /></span>
          <span @click="editAgent(item)" title="编辑"><EditOutlined /></span>
          <span @click="deleteAgent(item)" title="删除"><DeleteOutlined /></span>
        </template>
        <div class="card-header">
          <div class="agent-avatar">
            <a-avatar :size="40" :src="item.avatar || undefined">
              <template #icon v-if="!item.avatar">
                <RobotOutlined />
              </template>
            </a-avatar>
          </div>
          <div class="agent-info">
            <span class="agent-name">{{ item.name }}</span>
            <div class="agent-desc">{{ item.description || '暂无描述' }}</div>
          </div>
        </div>
      </a-card>
    </div>
    <a-pagination
      v-if="pagination.total > pagination.page_size"
      :current="pagination.page"
      :page-size="pagination.page_size"
      :total="pagination.total"
      @change="onPageChange"
      style="margin-top: 16px; text-align: right;"
    />
    <a-modal v-model:open="showAddModal" title="新增智能体" @ok="addAgent" :confirm-loading="addingAgent" @cancel="handleCancel">
      <a-form layout="vertical">
        <!-- 头像上传区域 -->
        <a-form-item label="头像">
          <div class="avatar-upload-section">
            <div class="avatar-preview">
              <a-avatar :size="80" :src="avatarPreview || undefined">
                <template #icon v-if="!avatarPreview">
                  <RobotOutlined />
                </template>
              </a-avatar>
            </div>
            <div class="avatar-upload">
              <a-upload
                v-model:fileList="avatarFileList"
                name="avatar"
                :max-count="1"
                :before-upload="beforeAvatarUpload"
                :show-upload-list="false"
                accept="image/*"
              >
                <a-button type="dashed">
                  <template #icon><UploadOutlined /></template>
                  上传头像
                </a-button>
              </a-upload>
              <div class="upload-hint">
                支持 JPG、PNG 格式，建议尺寸 200x200 像素
              </div>
            </div>
          </div>
        </a-form-item>
        <a-form-item label="名称" required>
          <a-input v-model:value="newAgentName" placeholder="输入智能体名称" />
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="newAgentDesc" placeholder="输入描述（可选，最多200字）" :maxlength="200" :auto-size="{ minRows: 3, maxRows: 6 }" />
        </a-form-item>
        <a-form-item label="类型">
          <a-select v-model:value="newAgentType" disabled>
            <a-select-option value="chatbot">对话智能体</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { h, ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { message, Modal } from 'ant-design-vue';
import { getAgents, createAgent, deleteAgent as deleteAgentApi, uploadAgentAvatar } from '@/apis/agent_api';
import { EditOutlined, DeleteOutlined, ExclamationCircleOutlined, RobotOutlined, UploadOutlined, MessageOutlined } from '@ant-design/icons-vue';
const emit = defineEmits(['edit-agent'])
const router = useRouter();
const agents = ref([]);
const loading = ref(false);
const showAddModal = ref(false);
const newAgentName = ref('');
const newAgentDesc = ref('');
const newAgentType = ref('chatbot');
const addingAgent = ref(false);

const pagination = ref({ page: 1, page_size: 10, total: 0 });

// 头像上传相关
const avatarFileList = ref([]);
const avatarPreview = ref('');
const avatarFile = ref(null);

const fetchAgents = async () => {
  loading.value = true;
  try {
    const res = await getAgents({ page: pagination.value.page, page_size: pagination.value.page_size });
    if (res.success) {
      agents.value = res.data.agents;
      pagination.value.total = res.data.pagination.total;

      
      // 调试信息：检查智能体数据是否包含头像
      console.log('获取到的智能体列表:', agents.value);
      agents.value.forEach(agent => {
        console.log(`智能体 ${agent.name} (ID: ${agent.agent_id}) 的头像:`, agent.avatar);
      });
    } else {
      message.error(res.message || '获取智能体列表失败');
    }
  } catch (e) {
    console.error('获取智能体列表异常:', e);
    message.error('获取智能体列表异常');
  } finally {
    loading.value = false;
  }
};

// 头像上传前验证
const beforeAvatarUpload = (file) => {
  const isJpgOrPng = file.type === 'image/jpeg' || file.type === 'image/png';
  if (!isJpgOrPng) {
    message.error('只能上传 JPG/PNG 格式的图片!');
    return false;
  }
  const isLt2M = file.size / 1024 / 1024 < 2;
  if (!isLt2M) {
    message.error('图片大小不能超过 2MB!');
    return false;
  }
  
  // 创建预览
  const reader = new FileReader();
  reader.onload = (e) => {
    avatarPreview.value = e.target.result;
  };
  reader.readAsDataURL(file);
  
  avatarFile.value = file;
  return false; // 阻止自动上传
};

// 重置表单
const resetForm = () => {
  newAgentName.value = '';
  newAgentDesc.value = '';
  avatarFileList.value = [];
  avatarPreview.value = '';
  avatarFile.value = null;
};

// 取消操作
const handleCancel = () => {
  showAddModal.value = false;
  resetForm();
};

const addAgent = async () => {
  if (!newAgentName.value.trim()) {
    message.warning('请输入智能体名称');
    return;
  }
  addingAgent.value = true;
  try {
    // 准备智能体数据
    const agentData = {
      name: newAgentName.value,
      description: newAgentDesc.value,
      agent_type: newAgentType.value
    };
    
    // 如果有头像文件，先转换为base64
    if (avatarFile.value) {
      try {
        const base64Data = await new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = (e) => resolve(e.target.result);
          reader.onerror = reject;
          reader.readAsDataURL(avatarFile.value);
        });
        agentData.avatar = base64Data;
        console.log('头像已转换为base64数据');
      } catch (error) {
        console.error('转换头像为base64失败:', error);
      }
    }
    
    // 创建智能体
    const res = await createAgent(agentData);
    
    if (res.success) {
      const agentId = res.data.agent_id;
      console.log('智能体创建成功，ID:', agentId);
      
      if (avatarFile.value) {
        message.success('智能体创建成功，头像已包含在创建数据中');
      } else {
        message.success('新增智能体成功');
      }
      
      showAddModal.value = false;
      resetForm();
      
      // 立即刷新列表
      fetchAgents();
    } else {
      message.error(res.message || '新增智能体失败');
    }
  } catch (e) {
    console.error('创建智能体异常:', e);
    message.error('新增智能体异常');
  } finally {
    addingAgent.value = false;
  }
};


const onPageChange = (page) => {
  pagination.value.page = page;
  fetchAgents();
};

const startChat = (item) => {
  router.push('/agent');
};

const editAgent = (item) => {
  emit('edit-agent', item.agent_id)
};
const deleteAgent = (item) => {
  Modal.confirm({
    title: '确认删除该智能体？',
    icon: h(ExclamationCircleOutlined),
    content: `名称：${item.name}`,
    okText: '删除',
    okType: 'danger',
    cancelText: '取消',
    async onOk() {
      try {
        const res = await deleteAgentApi(item.agent_id);
        if (res.success) {
          message.success('删除成功');
          fetchAgents();
        } else {
          message.error(res.message || '删除失败');
        }
      } catch (e) {
        message.error('删除异常');
      }
    }
  });
};

onMounted(() => {
  fetchAgents();
});

</script>

<style scoped>
.agent-management {
  padding: 20px;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.agent-card-list {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}
.agent-card {
  width: 300px;
  min-height: 120px;
}
.card-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 8px;
}
.agent-avatar {
  flex-shrink: 0;
}
.agent-info {
  flex: 1;
  min-width: 0;
}
.agent-name {
  font-weight: bold;
  font-size: 16px;
  display: block;
  margin-bottom: 4px;
}
.agent-desc {
  color: #888;
  font-size: 14px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 头像上传区域样式 */
.avatar-upload-section {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.avatar-preview {
  flex-shrink: 0;
}

.avatar-upload {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.upload-hint {
  font-size: 12px;
  color: #999;
  line-height: 1.4;
}
</style> 