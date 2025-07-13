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
          <span @click="editAgent(item)"><EditOutlined /></span>
          <span @click="deleteAgent(item)"><DeleteOutlined /></span>
        </template>
        <div class="card-header">
          <span class="agent-name">{{ item.name }}</span>
        </div>
        <div class="agent-desc">{{ item.description || '暂无描述' }}</div>
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
    <a-modal v-model:open="showAddModal" title="新增智能体" @ok="addAgent" :confirm-loading="addingAgent" @cancel="showAddModal = false">
      <a-form layout="vertical">
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
import { message, Modal } from 'ant-design-vue';
import { getAgents, createAgent, deleteAgent as deleteAgentApi } from '@/apis/agent_api';
import { EditOutlined, DeleteOutlined, ExclamationCircleOutlined } from '@ant-design/icons-vue';
const emit = defineEmits(['edit-agent'])
const agents = ref([]);
const loading = ref(false);
const showAddModal = ref(false);
const newAgentName = ref('');
const newAgentDesc = ref('');
const newAgentType = ref('chatbot');
const addingAgent = ref(false);
const defaultAgentId = ref(null);
const settingDefault = ref(false);
const pagination = ref({ page: 1, page_size: 10, total: 0 });

const fetchAgents = async () => {
  loading.value = true;
  try {
    const res = await getAgents({ page: pagination.value.page, page_size: pagination.value.page_size });
    if (res.success) {
      agents.value = res.data.agents;
      pagination.value.total = res.data.pagination.total;
      const defaultAgent = agents.value.find(a => a.instance);
      defaultAgentId.value = defaultAgent ? defaultAgent.agent_id : null;
    } else {
      message.error(res.message || '获取智能体列表失败');
    }
  } catch (e) {
    message.error('获取智能体列表异常');
  } finally {
    loading.value = false;
  }
};

const addAgent = async () => {
  if (!newAgentName.value.trim()) {
    message.warning('请输入智能体名称');
    return;
  }
  addingAgent.value = true;
  try {
    const res = await createAgent({
      name: newAgentName.value,
      description: newAgentDesc.value,
      agent_type: newAgentType.value
    });
    if (res.success) {
      message.success('新增智能体成功');
      showAddModal.value = false;
      newAgentName.value = '';
      newAgentDesc.value = '';
      fetchAgents();
    } else {
      message.error(res.message || '新增智能体失败');
    }
  } catch (e) {
    message.error('新增智能体异常');
  } finally {
    addingAgent.value = false;
  }
};


const onPageChange = (page) => {
  pagination.value.page = page;
  fetchAgents();
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
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.agent-name {
  font-weight: bold;
  font-size: 16px;
}
.agent-desc {
  color: #888;
  font-size: 14px;
  margin-top: 4px;
}
</style> 