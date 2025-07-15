<template>
  <div class="agent-management layout-container">
    <!-- 智能体列表视图 -->
    <div class="agent-list-view">
      <!-- 页面头部 -->
      <HeaderComponent 
        title="智能体管理" 
        description="创建、编辑和管理您的自定义智能体"
        :loading="loading"
      />

      <!-- 智能体列表 -->
      <div class="agents">
        <div class="new-agent agentcard" @click="showAddModal = true">
          <div class="top">
            <div class="icon"><PlusOutlined /></div>
            <div class="info">
              <h3>创建智能体</h3>
            </div>
          </div>
          <p>创建自定义智能体，配置角色、能力和工具，打造专属的AI助手。</p>
        </div>
        
        <div
          v-for="agent in agents"
          :key="agent.agent_id"
          class="agent agentcard"
          @click="handleView(agent)"
        >
          <div class="top">
            <div class="icon">
              <a-avatar :size="40" :src="agent.avatar || undefined">
                <template #icon v-if="!agent.avatar">
                  <RobotOutlined v-if="agent.agent_type === 'chatbot'" />
                  <ToolOutlined v-else-if="agent.agent_type === 'react'" />
                  <UserOutlined v-else />
                </template>
              </a-avatar>
            </div>
            <div class="info">
              <h3>{{ agent.name }}</h3>
              <p>
                <span>{{ agent.agent_type || 'custom' }}</span>
              </p>
            </div>
          </div>
          <a-tooltip :title="agent.description || '暂无描述'">
            <p class="description">{{ agent.description || '暂无描述' }}</p>
          </a-tooltip>
          <div class="tags">
            <a-tag color="blue" v-if="agent.agent_type">{{
              getAgentTypeLabel(agent.agent_type)
            }}</a-tag>
            <a-tag color="green" v-if="agent.scope">{{ getScopeLabel(agent.scope) }}</a-tag>
            <a-tag color="orange" v-if="agent.is_favorite">收藏</a-tag>
          </div>
          <div class="actions">
            <a-button size="small" @click.stop="handleStartChat(agent)">对话</a-button>
            <a-button size="small" @click.stop="handleEdit(agent)">编辑</a-button>
            <a-button size="small" @click.stop="handleDuplicate(agent)">复制</a-button>
            <a-button size="small" danger @click.stop="handleDelete(agent)">删除</a-button>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="!loading && agents.length === 0" class="agent-empty">
        <a-empty>
          <template #description>
            <span>还没有智能体，快来创建第一个吧！</span>
          </template>
        </a-empty>
      </div>
    </div>

    <!-- 创建智能体模态框 -->
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

    <!-- 智能体详情模态框 -->
    <AgentDetailModal 
      v-model:visible="detailModalVisible" 
      :agent-id="selectedAgentId" 
      @chat="handleStartChat"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import { PlusOutlined, RobotOutlined, ToolOutlined, UserOutlined, UploadOutlined } from '@ant-design/icons-vue'
import { getAgents, deleteAgent as deleteAgentApi, duplicateAgent, createAgent } from '@/apis/agent_api'
import AgentDetailModal from '@/components/agent/AgentDetailModal.vue'
import HeaderComponent from '@/components/HeaderComponent.vue'

const router = useRouter()

// 响应式数据
const loading = ref(false)
const agents = ref([])

// 创建智能体相关
const showAddModal = ref(false)
const newAgentName = ref('')
const newAgentDesc = ref('')
const newAgentType = ref('chatbot')
const addingAgent = ref(false)

// 头像上传相关
const avatarFileList = ref([])
const avatarPreview = ref('')
const avatarFile = ref(null)

const detailModalVisible = ref(false)
const selectedAgentId = ref('')

// 获取智能体类型标签
const getAgentTypeLabel = (type) => {
  const typeMap = {
    chatbot: '聊天助手',
    react: 'ReAct',
    custom: '自定义'
  }
  return typeMap[type] || type
}

// 获取范围标签
const getScopeLabel = (scope) => {
  const scopeMap = {
    mine: '我的',
    public: '公开'
  }
  return scopeMap[scope] || scope
}

// 获取智能体列表
const fetchAgents = async () => {
  try {
    loading.value = true
    
    const params = {
      page: 1,
      page_size: 100, // 获取更多数据，简化分页
      sort_by: 'created_at',
      sort_order: 'desc'
    }

    const response = await getAgents(params)
    
    if (response.success) {
      agents.value = response.data.agents
    } else {
      message.error(response.message || '获取智能体列表失败')
    }
  } catch (error) {
    console.error('获取智能体列表失败:', error)
    const errorMessage = error.message || '获取智能体列表失败'
    message.error(errorMessage)
  } finally {
    loading.value = false
  }
}

// 头像上传前验证
const beforeAvatarUpload = (file) => {
  const isJpgOrPng = file.type === 'image/jpeg' || file.type === 'image/png'
  if (!isJpgOrPng) {
    message.error('只能上传 JPG/PNG 格式的图片!')
    return false
  }
  const isLt2M = file.size / 1024 / 1024 < 2
  if (!isLt2M) {
    message.error('图片大小不能超过 2MB!')
    return false
  }
  
  // 创建预览
  const reader = new FileReader()
  reader.onload = (e) => {
    avatarPreview.value = e.target.result
  }
  reader.readAsDataURL(file)
  
  avatarFile.value = file
  return false // 阻止自动上传
}

// 重置表单
const resetForm = () => {
  newAgentName.value = ''
  newAgentDesc.value = ''
  avatarFileList.value = []
  avatarPreview.value = ''
  avatarFile.value = null
}

// 取消操作
const handleCancel = () => {
  showAddModal.value = false
  resetForm()
}

// 创建智能体
const addAgent = async () => {
  if (!newAgentName.value.trim()) {
    message.warning('请输入智能体名称')
    return
  }
  addingAgent.value = true
  try {
    // 准备智能体数据
    const agentData = {
      name: newAgentName.value,
      description: newAgentDesc.value,
      agent_type: newAgentType.value
    }
    
    // 如果有头像文件，先转换为base64
    if (avatarFile.value) {
      try {
        const base64Data = await new Promise((resolve, reject) => {
          const reader = new FileReader()
          reader.onload = (e) => resolve(e.target.result)
          reader.onerror = reject
          reader.readAsDataURL(avatarFile.value)
        })
        agentData.avatar = base64Data
        console.log('头像已转换为base64数据')
      } catch (error) {
        console.error('转换头像为base64失败:', error)
      }
    }
    
    // 创建智能体
    const res = await createAgent(agentData)
    
    if (res.success) {
      const agentId = res.data.agent_id
      console.log('智能体创建成功，ID:', agentId)
      
      if (avatarFile.value) {
        message.success('智能体创建成功，头像已包含在创建数据中')
      } else {
        message.success('新增智能体成功')
      }
      
      showAddModal.value = false
      resetForm()
      
      // 立即刷新列表
      fetchAgents()
    } else {
      message.error(res.message || '新增智能体失败')
    }
  } catch (e) {
    console.error('创建智能体异常:', e)
    // 使用接口返回的具体错误信息
    const errorMessage = e.message || '新增智能体失败'
    message.error(errorMessage)
  } finally {
    addingAgent.value = false
  }
}

// 编辑智能体
const handleEdit = (agent) => {
  router.push(`/agent/edit/${agent.agent_id}`)
}



// 删除智能体
const handleDelete = (agent) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除智能体"${agent.name}"吗？此操作无法撤销。`,
    okText: '删除',
    okType: 'danger',
    cancelText: '取消',
    async onOk() {
      try {
        const response = await deleteAgentApi(agent.agent_id)
        if (response.success) {
          message.success('智能体删除成功')
          fetchAgents()
            } else {
      message.error(response.message || '删除失败')
    }
      } catch (error) {
        console.error('删除智能体失败:', error)
        const errorMessage = error.message || '删除失败'
        message.error(errorMessage)
      }
    }
  })
}

// 复制智能体
const handleDuplicate = async (agent) => {
  try {
    const newName = `${agent.name} - 副本`
    const response = await duplicateAgent(agent.agent_id, { new_name: newName })
    
    if (response.success) {
      message.success('智能体复制成功')
      fetchAgents()
    } else {
      message.error(response.message || '复制失败')
    }
  } catch (error) {
    console.error('复制智能体失败:', error)
    const errorMessage = error.message || '复制失败'
    message.error(errorMessage)
  }
}

// 查看智能体详情
const handleView = (agent) => {
  selectedAgentId.value = agent.agent_id
  detailModalVisible.value = true
}

// 开始聊天
const handleStartChat = (agent) => {
  // 关闭详情模态框
  detailModalVisible.value = false
  
  // 跳转到智能体聊天页面
  router.push(`/agent/chat?agent_id=${agent.agent_id}`)
}

// 组件挂载
onMounted(() => {
  fetchAgents()
})
</script>

<style lang="less" scoped>
.agent-management {
  padding: 0;
}

.agent-list-view {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.agents {
  padding: 20px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;

  .new-agent {
    background-color: #f0f3f4;
  }
}

.agent {
  background-color: white;
  box-shadow: 0px 1px 2px 0px rgba(16, 24, 40, 0.06), 0px 1px 3px 0px rgba(16, 24, 40, 0.1);
  border: 2px solid white;
  transition: box-shadow 0.2s ease-in-out;

  &:hover {
    box-shadow: 0px 4px 6px -2px rgba(16, 24, 40, 0.03), 0px 12px 16px -4px rgba(16, 24, 40, 0.08);
  }
}

.agentcard,
.agent {
  width: 100%;
  padding: 20px;
  border-radius: 12px;
  height: 200px;
  cursor: pointer;
  position: relative;

  .top {
    display: flex;
    align-items: center;
    height: 50px;
    margin-bottom: 10px;

    .icon {
      width: 50px;
      height: 50px;
      font-size: 28px;
      margin-right: 10px;
      display: flex;
      justify-content: center;
      align-items: center;
      background-color: #f5f8ff;
      border-radius: 8px;
      border: 1px solid #e0eaff;
      color: var(--main-color);
    }

    .info {
      h3,
      p {
        margin: 0;
        color: black;
      }

      h3 {
        font-size: 16px;
        font-weight: bold;
      }

      p {
        color: var(--gray-900);
        font-size: small;
      }
    }
  }

  .description {
    color: var(--gray-900);
    overflow: hidden;
    display: -webkit-box;
    line-clamp: 2;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    text-overflow: ellipsis;
    margin-bottom: 10px;
    font-size: 14px;
  }

  .tags {
    margin-bottom: 10px;
  }

  .actions {
    position: absolute;
    bottom: 15px;
    right: 15px;
    display: flex;
    gap: 8px;
    opacity: 0;
    transition: opacity 0.2s ease-in-out;
  }

  &:hover .actions {
    opacity: 1;
  }
}

.agent-empty {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 400px;
  flex-direction: column;
  color: var(--gray-900);
}

.agent-edit-container {
  width: 100%;
  height: calc(100vh - 48px);
  overflow: hidden;
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

/* 响应式设计 */
@media (max-width: 1200px) {
  .agents {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  }
}

@media (max-width: 768px) {
  .agents {
    padding: 16px;
    grid-template-columns: 1fr;
  }
  
  .agentcard,
  .agent {
    height: auto;
    min-height: 180px;
  }
}
</style> 