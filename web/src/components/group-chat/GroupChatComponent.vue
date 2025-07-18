<template>
  <div class="group-chat-container">
    <!-- 群聊头部 -->
    <div class="chat-header">
      <div class="header-left">
        <a-avatar :size="40" :src="currentChat?.avatar">
          {{ currentChat?.name?.charAt(0)?.toUpperCase() }}
        </a-avatar>
        <div class="chat-info">
          <div class="chat-name">{{ currentChat?.name }}</div>
          <div class="chat-status">
            {{ currentChat?.member_count }} 个成员 · 
            {{ onlineMembers.length }} 人在线
          </div>
        </div>
      </div>
      
      <div class="header-right">
        <a-space>
          <!-- 搜索消息 -->
          <a-button type="text" @click="showSearchModal = true">
            <template #icon>
              <SearchOutlined />
            </template>
          </a-button>
          
          <!-- 文件管理 -->
          <a-button type="text" @click="showFileManager = true">
            <template #icon>
              <FileOutlined />
            </template>
          </a-button>
          
          <!-- 成员管理 -->
          <a-button type="text" @click="showMemberPanel = !showMemberPanel">
            <template #icon>
              <TeamOutlined />
            </template>
          </a-button>
          
          <!-- 更多操作 -->
          <a-dropdown placement="bottomRight">
            <a-button type="text">
              <template #icon>
                <MoreOutlined />
              </template>
            </a-button>
            <template #overlay>
              <a-menu>
                <a-menu-item key="info" @click="showChatInfo = true">
                  <InfoCircleOutlined />
                  群聊信息
                </a-menu-item>
                <a-menu-item key="notification">
                  <BellOutlined />
                  通知设置
                </a-menu-item>
                <a-menu-divider />
                <a-menu-item key="clear" @click="clearMessages">
                  <ClearOutlined />
                  清空消息
                </a-menu-item>
                <a-menu-item key="leave" danger @click="leaveChat">
                  <LogoutOutlined />
                  退出群聊
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </a-space>
      </div>
    </div>

    <!-- 主体内容区域 -->
    <div class="chat-content" :class="{ 'with-member-panel': showMemberPanel }">
      <!-- 消息区域 -->
      <div class="message-area">
        <!-- 消息列表 -->
        <div ref="messageListRef" class="message-list" @scroll="handleScroll">
          <div v-if="loadingHistory" class="loading-more">
            <a-spin size="small" />
            <span>加载历史消息...</span>
          </div>
          
          <!-- 消息项 -->
          <div
            v-for="message in messages"
            :key="message.id"
            class="message-item"
            :class="{ 'own-message': message.sender_id === currentUserId }"
          >
            <div class="message-content">
              <!-- 发送者信息 -->
              <div class="sender-info" v-if="message.sender_id !== currentUserId">
                <a-avatar :size="32" :src="getSenderAvatar(message.sender_id)">
                  {{ getSenderName(message.sender_id)?.charAt(0)?.toUpperCase() }}
                </a-avatar>
                <span class="sender-name">{{ getSenderName(message.sender_id) }}</span>
                <span class="sender-type" v-if="getSenderType(message.sender_id) === 'agent'">
                  (智能体)
                </span>
              </div>
              
              <!-- 消息主体 -->
              <div class="message-body">
                <!-- 文本消息 -->
                <div v-if="message.message_type === 'text'" class="text-message">
                  <div v-html="renderMessage(message.content)"></div>
                  
                  <!-- @提及显示 -->
                  <div v-if="message.metadata?.mentions?.length" class="mentions">
                    <a-tag
                      v-for="mention in message.metadata.mentions"
                      :key="mention.member_id"
                      size="small"
                      color="blue"
                    >
                      @{{ mention.display_name }}
                    </a-tag>
                  </div>
                </div>
                
                <!-- 文件消息 -->
                <div v-else-if="message.message_type === 'file'" class="file-message">
                  <div
                    v-for="file in message.metadata?.files"
                    :key="file.id"
                    class="file-item"
                    @click="downloadFile(file)"
                  >
                    <component
                      :is="getFileIcon(file.filename)"
                      :style="{ fontSize: '20px', color: getFileIconColor(file.filename) }"
                    />
                    <div class="file-info">
                      <div class="file-name">{{ file.filename }}</div>
                      <div class="file-size">{{ formatFileSize(file.file_size) }}</div>
                    </div>
                    <DownloadOutlined class="download-icon" />
                  </div>
                </div>
                
                <!-- 系统消息 -->
                <div v-else-if="message.message_type === 'system'" class="system-message">
                  <div class="system-content">{{ message.content }}</div>
                </div>
                
                <!-- 工具调用结果 -->
                <div v-else-if="message.message_type === 'tool_call'" class="tool-message">
                  <div class="tool-header">
                    <ToolOutlined />
                    <span>工具调用结果</span>
                  </div>
                  <div class="tool-content">
                    <pre>{{ JSON.stringify(message.metadata, null, 2) }}</pre>
                  </div>
                </div>
              </div>
              
              <!-- 消息时间和状态 -->
              <div class="message-footer">
                <span class="message-time">{{ formatTime(message.created_at) }}</span>
                <span v-if="message.edited_at" class="edited-mark">(已编辑)</span>
                
                <!-- 消息操作 -->
                <div class="message-actions">
                  <a-dropdown placement="topRight" :trigger="['click']">
                    <a-button type="text" size="small">
                      <template #icon>
                        <MoreOutlined />
                      </template>
                    </a-button>
                    <template #overlay>
                      <a-menu>
                        <a-menu-item key="reply" @click="replyMessage(message)">
                          <ReplyOutlined />
                          回复
                        </a-menu-item>
                        <a-menu-item key="copy" @click="copyMessage(message)">
                          <CopyOutlined />
                          复制
                        </a-menu-item>
                        <a-menu-item 
                          key="edit" 
                          @click="editMessage(message)"
                          v-if="canEditMessage(message)"
                        >
                          <EditOutlined />
                          编辑
                        </a-menu-item>
                        <a-menu-item 
                          key="delete" 
                          danger 
                          @click="deleteMessage(message)"
                          v-if="canDeleteMessage(message)"
                        >
                          <DeleteOutlined />
                          删除
                        </a-menu-item>
                      </a-menu>
                    </template>
                  </a-dropdown>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 正在输入指示器 -->
          <div v-if="typingUsers.length > 0" class="typing-indicator">
            <div class="typing-content">
              <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <span class="typing-text">
                {{ getTypingText() }}
              </span>
            </div>
          </div>
        </div>
        
        <!-- 消息输入区域 -->
        <div class="message-input-area">
          <MessageInput
            :members="members"
            :placeholder="getInputPlaceholder()"
            @send-message="handleSendMessage"
          />
        </div>
      </div>
      
      <!-- 成员面板 -->
      <div v-if="showMemberPanel" class="member-panel">
        <div class="panel-header">
          <h4>群成员 ({{ members.length }})</h4>
          <a-button type="text" @click="showMemberPanel = false">
            <template #icon>
              <CloseOutlined />
            </template>
          </a-button>
        </div>
        
        <div class="member-list">
          <!-- 在线成员 -->
          <div v-if="onlineMembers.length > 0" class="member-section">
            <div class="section-title">在线 - {{ onlineMembers.length }}</div>
            <div
              v-for="member in onlineMembers"
              :key="member.id"
              class="member-item"
            >
              <a-avatar :size="32" :src="member.avatar">
                {{ (member.display_name || member.name)?.charAt(0)?.toUpperCase() }}
              </a-avatar>
              <div class="member-info">
                <div class="member-name">
                  {{ member.display_name || member.name }}
                  <a-tag v-if="member.role === 'admin'" size="small" color="gold">管理员</a-tag>
                </div>
                <div class="member-status">
                  <span class="online-dot"></span>
                  {{ member.member_type === 'agent' ? '智能体' : '在线' }}
                </div>
              </div>
              
              <!-- 成员操作 -->
              <div class="member-actions" v-if="canManageMembers">
                <a-dropdown placement="bottomRight">
                  <a-button type="text" size="small">
                    <template #icon>
                      <MoreOutlined />
                    </template>
                  </a-button>
                  <template #overlay>
                    <a-menu>
                      <a-menu-item key="profile">
                        <UserOutlined />
                        查看资料
                      </a-menu-item>
                      <a-menu-item key="role" v-if="member.role !== 'admin'">
                        <CrownOutlined />
                        设为管理员
                      </a-menu-item>
                      <a-menu-divider />
                      <a-menu-item key="remove" danger>
                        <DeleteOutlined />
                        移出群聊
                      </a-menu-item>
                    </a-menu>
                  </template>
                </a-dropdown>
              </div>
            </div>
          </div>
          
          <!-- 离线成员 -->
          <div v-if="offlineMembers.length > 0" class="member-section">
            <div class="section-title">离线 - {{ offlineMembers.length }}</div>
            <div
              v-for="member in offlineMembers"
              :key="member.id"
              class="member-item offline"
            >
              <a-avatar :size="32" :src="member.avatar">
                {{ (member.display_name || member.name)?.charAt(0)?.toUpperCase() }}
              </a-avatar>
              <div class="member-info">
                <div class="member-name">
                  {{ member.display_name || member.name }}
                  <a-tag v-if="member.role === 'admin'" size="small" color="gold">管理员</a-tag>
                </div>
                <div class="member-status">
                  <span class="offline-dot"></span>
                  离线
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 添加成员按钮 -->
        <div class="add-member-section" v-if="canManageMembers">
          <a-button type="dashed" block @click="showAddMemberModal = true">
            <template #icon>
              <PlusOutlined />
            </template>
            添加成员
          </a-button>
        </div>
      </div>
    </div>

    <!-- 文件管理抽屉 -->
    <FileManagerDrawer
      v-model:visible="showFileManager"
      :group-id="currentChat?.id"
      :members="members"
      :current-user-id="currentUserId"
      :can-manage-files="canManageFiles"
      @file-uploaded="handleFileUploaded"
    />

    <!-- 添加成员模态框 -->
    <a-modal
      v-model:open="showAddMemberModal"
      title="添加成员"
      @ok="handleAddMember"
      :confirmLoading="addingMember"
    >
      <a-form layout="vertical">
        <a-form-item label="选择成员类型">
          <a-radio-group v-model:value="addMemberForm.type">
            <a-radio value="user">用户</a-radio>
            <a-radio value="agent">智能体</a-radio>
          </a-radio-group>
        </a-form-item>
        
        <a-form-item label="选择成员">
          <a-select
            v-model:value="addMemberForm.members"
            mode="multiple"
            placeholder="请选择要添加的成员"
            :loading="loadingAvailableMembers"
            style="width: 100%"
          >
            <a-select-option
              v-for="member in availableMembers"
              :key="member.id"
              :value="member.id"
            >
              {{ member.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 消息搜索模态框 -->
    <a-modal
      v-model:open="showSearchModal"
      title="搜索消息"
      :footer="null"
      width="600"
    >
      <div class="search-container">
        <a-input
          v-model:value="searchQuery"
          placeholder="搜索消息内容..."
          @input="handleSearchInput"
        >
          <template #prefix>
            <SearchOutlined />
          </template>
        </a-input>
        
        <div class="search-results" v-if="searchResults.length > 0">
          <div
            v-for="result in searchResults"
            :key="result.id"
            class="search-result-item"
            @click="jumpToMessage(result)"
          >
            <div class="result-sender">{{ getSenderName(result.sender_id) }}</div>
            <div class="result-content" v-html="highlightSearchText(result.content)"></div>
            <div class="result-time">{{ formatTime(result.created_at) }}</div>
          </div>
        </div>
        
        <div v-else-if="searchQuery && !searchLoading" class="no-results">
          <a-empty description="未找到相关消息" />
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { message } from 'ant-design-vue'
import {
  SearchOutlined,
  FileOutlined,
  TeamOutlined,
  MoreOutlined,
  InfoCircleOutlined,
  BellOutlined,
  ClearOutlined,
  LogoutOutlined,
  DownloadOutlined,
  ToolOutlined,
  ReplyOutlined,
  CopyOutlined,
  EditOutlined,
  DeleteOutlined,
  CloseOutlined,
  UserOutlined,
  CrownOutlined,
  PlusOutlined,
  FileImageOutlined,
  FileTextOutlined,
  FileWordOutlined,
  FileExcelOutlined,
  FilePdfOutlined,
  FileZipOutlined,
  VideoCameraOutlined,
  AudioOutlined,
  FileOutlined as DefaultFileIcon
} from '@ant-design/icons-vue'

import MessageInput from './MessageInput.vue'
import FileManagerDrawer from './FileManagerDrawer.vue'
import { groupChatApi } from '@/apis/group_chat_api'

// Props
const props = defineProps({
  currentChat: {
    type: Object,
    default: null
  },
  currentUserId: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['message-sent', 'leave-chat'])

// 响应式数据
const messages = ref([])
const members = ref([])
const typingUsers = ref([])
const showMemberPanel = ref(false)
const showFileManager = ref(false)
const showSearchModal = ref(false)
const showAddMemberModal = ref(false)
const showChatInfo = ref(false)

// 消息相关
const messageListRef = ref()
const loadingHistory = ref(false)
const loadingMessages = ref(false)
const currentPage = ref(1)
const hasMoreMessages = ref(true)

// 搜索相关
const searchQuery = ref('')
const searchResults = ref([])
const searchLoading = ref(false)

// 添加成员
const addingMember = ref(false)
const loadingAvailableMembers = ref(false)
const availableMembers = ref([])
const addMemberForm = reactive({
  type: 'user',
  members: []
})

// 计算属性
const onlineMembers = computed(() => {
  return members.value.filter(member => 
    member.member_type === 'agent' || member.is_online
  )
})

const offlineMembers = computed(() => {
  return members.value.filter(member => 
    member.member_type === 'user' && !member.is_online
  )
})

const canManageMembers = computed(() => {
  const currentMember = members.value.find(m => m.id === props.currentUserId)
  return currentMember?.role === 'admin'
})

const canManageFiles = computed(() => {
  return canManageMembers.value
})

// 方法
const loadMessages = async (page = 1, loadMore = false) => {
  if (!props.currentChat?.id) return
  
  try {
    if (loadMore) {
      loadingHistory.value = true
    } else {
      loadingMessages.value = true
    }
    
    const result = await groupChatApi.getMessages(props.currentChat.id, {
      page,
      limit: 50
    })
    
    if (loadMore) {
      messages.value = [...result.data, ...messages.value]
    } else {
      messages.value = result.data
    }
    
    hasMoreMessages.value = result.data.length === 50
    
    if (!loadMore) {
      await nextTick()
      scrollToBottom()
    }
  } catch (error) {
    message.error('加载消息失败：' + error.message)
  } finally {
    loadingHistory.value = false
    loadingMessages.value = false
  }
}

const loadMembers = async () => {
  if (!props.currentChat?.id) return
  
  try {
    const result = await groupChatApi.getMembers(props.currentChat.id)
    members.value = result.data
  } catch (error) {
    message.error('加载成员列表失败：' + error.message)
  }
}

const handleSendMessage = async (data) => {
  try {
    const { message: messageData, files } = data
    
    // 发送消息
    const result = await groupChatApi.sendMessage(props.currentChat.id, messageData)
    
    // 如果有文件，上传文件
    if (files && files.length > 0) {
      for (const file of files) {
        await groupChatApi.uploadFile(props.currentChat.id, file)
      }
    }
    
    // 重新加载消息
    await loadMessages()
    
    emit('message-sent', result.data)
  } catch (error) {
    message.error('发送消息失败：' + error.message)
  }
}

const handleScroll = (e) => {
  const { scrollTop } = e.target
  
  // 滚动到顶部时加载更多历史消息
  if (scrollTop === 0 && hasMoreMessages.value && !loadingHistory.value) {
    currentPage.value++
    loadMessages(currentPage.value, true)
  }
}

const scrollToBottom = () => {
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight
  }
}

const getSenderName = (senderId) => {
  const member = members.value.find(m => m.id === senderId)
  return member ? (member.display_name || member.name) : '未知用户'
}

const getSenderAvatar = (senderId) => {
  const member = members.value.find(m => m.id === senderId)
  return member?.avatar
}

const getSenderType = (senderId) => {
  const member = members.value.find(m => m.id === senderId)
  return member?.member_type
}

const renderMessage = (content) => {
  // 处理@提及高亮
  return content.replace(/@(\S+)/g, '<span class="mention">@$1</span>')
}

const getInputPlaceholder = () => {
  if (!props.currentChat) return '请选择群聊'
  return `在 ${props.currentChat.name} 中发消息...`
}

const getTypingText = () => {
  if (typingUsers.value.length === 1) {
    return `${typingUsers.value[0]} 正在输入...`
  } else if (typingUsers.value.length === 2) {
    return `${typingUsers.value[0]} 和 ${typingUsers.value[1]} 正在输入...`
  } else {
    return `${typingUsers.value.length} 人正在输入...`
  }
}

// 文件相关方法
const getFileIcon = (filename) => {
  const ext = filename.split('.').pop()?.toLowerCase()
  
  if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'].includes(ext)) {
    return FileImageOutlined
  } else if (['txt', 'md', 'log'].includes(ext)) {
    return FileTextOutlined
  } else if (['doc', 'docx'].includes(ext)) {
    return FileWordOutlined
  } else if (['xls', 'xlsx'].includes(ext)) {
    return FileExcelOutlined
  } else if (['pdf'].includes(ext)) {
    return FilePdfOutlined
  } else if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) {
    return FileZipOutlined
  } else if (['mp4', 'avi', 'mov', 'wmv', 'flv'].includes(ext)) {
    return VideoCameraOutlined
  } else if (['mp3', 'wav', 'flac', 'aac'].includes(ext)) {
    return AudioOutlined
  }
  
  return DefaultFileIcon
}

const getFileIconColor = (filename) => {
  const ext = filename.split('.').pop()?.toLowerCase()
  
  if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'].includes(ext)) {
    return '#52c41a'
  } else if (['doc', 'docx'].includes(ext)) {
    return '#1890ff'
  } else if (['xls', 'xlsx'].includes(ext)) {
    return '#52c41a'
  } else if (['pdf'].includes(ext)) {
    return '#ff4d4f'
  } else if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) {
    return '#fa8c16'
  } else if (['mp4', 'avi', 'mov', 'wmv', 'flv'].includes(ext)) {
    return '#722ed1'
  } else if (['mp3', 'wav', 'flac', 'aac'].includes(ext)) {
    return '#eb2f96'
  }
  
  return '#666'
}

const downloadFile = async (file) => {
  try {
    const result = await groupChatApi.downloadFile(props.currentChat.id, file.id)
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([result]))
    const link = document.createElement('a')
    link.href = url
    link.download = file.filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    message.error('文件下载失败：' + error.message)
  }
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) { // 1分钟内
    return '刚刚'
  } else if (diff < 3600000) { // 1小时内
    return Math.floor(diff / 60000) + '分钟前'
  } else if (diff < 86400000) { // 1天内
    return Math.floor(diff / 3600000) + '小时前'
  } else if (diff < 604800000) { // 1周内
    return Math.floor(diff / 86400000) + '天前'
  } else {
    return date.toLocaleDateString()
  }
}

// 消息操作
const canEditMessage = (msg) => {
  return msg.sender_id === props.currentUserId && msg.message_type === 'text'
}

const canDeleteMessage = (msg) => {
  return msg.sender_id === props.currentUserId || canManageMembers.value
}

const replyMessage = (msg) => {
  // 实现回复消息功能
  console.log('回复消息:', msg)
}

const copyMessage = async (msg) => {
  try {
    await navigator.clipboard.writeText(msg.content)
    message.success('消息已复制到剪贴板')
  } catch (error) {
    message.error('复制失败')
  }
}

const editMessage = (msg) => {
  // 实现编辑消息功能
  console.log('编辑消息:', msg)
}

const deleteMessage = async (msg) => {
  try {
    await groupChatApi.deleteMessage(props.currentChat.id, msg.id)
    message.success('消息已删除')
    await loadMessages()
  } catch (error) {
    message.error('删除消息失败：' + error.message)
  }
}

// 搜索相关
const handleSearchInput = () => {
  if (searchQuery.value.trim()) {
    performSearch()
  } else {
    searchResults.value = []
  }
}

const performSearch = async () => {
  if (!searchQuery.value.trim()) return
  
  try {
    searchLoading.value = true
    const result = await groupChatApi.getMessages(props.currentChat.id, {
      search: searchQuery.value,
      limit: 50
    })
    searchResults.value = result.data
  } catch (error) {
    message.error('搜索失败：' + error.message)
  } finally {
    searchLoading.value = false
  }
}

const highlightSearchText = (content) => {
  if (!searchQuery.value) return content
  
  const regex = new RegExp(`(${searchQuery.value})`, 'gi')
  return content.replace(regex, '<mark>$1</mark>')
}

const jumpToMessage = (msg) => {
  // 实现跳转到消息功能
  showSearchModal.value = false
  console.log('跳转到消息:', msg)
}

// 其他操作
const clearMessages = () => {
  // 实现清空消息功能
  console.log('清空消息')
}

const leaveChat = () => {
  emit('leave-chat', props.currentChat)
}

const handleFileUploaded = () => {
  loadMessages()
}

const handleAddMember = async () => {
  try {
    addingMember.value = true
    
    for (const memberId of addMemberForm.members) {
      await groupChatApi.addMember(props.currentChat.id, {
        member_type: addMemberForm.type,
        member_id: memberId,
        role: 'member'
      })
    }
    
    message.success('成员添加成功')
    showAddMemberModal.value = false
    addMemberForm.members = []
    await loadMembers()
  } catch (error) {
    message.error('添加成员失败：' + error.message)
  } finally {
    addingMember.value = false
  }
}

// 生命周期
watch(() => props.currentChat, (newChat) => {
  if (newChat?.id) {
    currentPage.value = 1
    hasMoreMessages.value = true
    loadMessages()
    loadMembers()
  }
}, { immediate: true })

onMounted(() => {
  // 可以在这里设置WebSocket连接来实时接收消息
})

onUnmounted(() => {
  // 清理WebSocket连接
})
</script>

<style scoped>
.group-chat-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: white;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  background: white;
  z-index: 10;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-info .chat-name {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 2px;
}

.chat-info .chat-status {
  font-size: 12px;
  color: #666;
}

.chat-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.chat-content.with-member-panel {
  padding-right: 300px;
}

.message-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  scroll-behavior: smooth;
}

.loading-more {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  color: #666;
  font-size: 12px;
}

.message-item {
  margin-bottom: 16px;
}

.message-item.own-message {
  display: flex;
  justify-content: flex-end;
}

.message-item.own-message .message-content {
  background: #1890ff;
  color: white;
  border-radius: 12px 12px 4px 12px;
}

.message-content {
  max-width: 70%;
  background: #f5f5f5;
  border-radius: 12px 12px 12px 4px;
  padding: 12px;
  position: relative;
}

.sender-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.sender-name {
  font-size: 13px;
  font-weight: 500;
  color: #333;
}

.sender-type {
  font-size: 11px;
  color: #999;
}

.message-body {
  margin-bottom: 8px;
}

.text-message {
  line-height: 1.5;
}

.mentions {
  margin-top: 8px;
}

.file-message .file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.file-message .file-item:hover {
  background: rgba(255, 255, 255, 0.9);
}

.file-info .file-name {
  font-size: 13px;
  font-weight: 500;
}

.file-info .file-size {
  font-size: 11px;
  color: #999;
}

.system-message {
  text-align: center;
  color: #999;
  font-size: 12px;
  font-style: italic;
  padding: 8px;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 6px;
}

.tool-message {
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  overflow: hidden;
}

.tool-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f5f5f5;
  border-bottom: 1px solid #d9d9d9;
  font-size: 12px;
  font-weight: 500;
}

.tool-content {
  padding: 12px;
  font-family: 'Monaco', 'Courier New', monospace;
  font-size: 11px;
  background: #fafafa;
}

.message-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  color: #999;
}

.message-time {
  margin-right: 8px;
}

.edited-mark {
  font-style: italic;
}

.message-actions {
  opacity: 0;
  transition: opacity 0.2s;
}

.message-item:hover .message-actions {
  opacity: 1;
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  color: #666;
  font-size: 12px;
}

.typing-dots {
  display: flex;
  gap: 2px;
}

.typing-dots span {
  width: 4px;
  height: 4px;
  background: #999;
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-dots span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

.message-input-area {
  padding: 16px;
  border-top: 1px solid #f0f0f0;
  background: white;
}

.member-panel {
  position: absolute;
  top: 0;
  right: 0;
  width: 300px;
  height: 100%;
  background: white;
  border-left: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.panel-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.member-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.member-section {
  margin-bottom: 16px;
}

.section-title {
  font-size: 12px;
  color: #666;
  font-weight: 500;
  margin-bottom: 8px;
  text-transform: uppercase;
}

.member-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.member-item:hover {
  background: #f5f5f5;
}

.member-item.offline {
  opacity: 0.6;
}

.member-info {
  flex: 1;
  min-width: 0;
}

.member-name {
  font-size: 13px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;
}

.member-status {
  font-size: 11px;
  color: #666;
  display: flex;
  align-items: center;
  gap: 4px;
}

.online-dot {
  width: 6px;
  height: 6px;
  background: #52c41a;
  border-radius: 50%;
}

.offline-dot {
  width: 6px;
  height: 6px;
  background: #999;
  border-radius: 50%;
}

.member-actions {
  opacity: 0;
  transition: opacity 0.2s;
}

.member-item:hover .member-actions {
  opacity: 1;
}

.add-member-section {
  padding: 16px;
  border-top: 1px solid #f0f0f0;
}

.search-container {
  padding: 16px 0;
}

.search-results {
  margin-top: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.search-result-item {
  padding: 12px;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.search-result-item:hover {
  background: #f5f5f5;
}

.result-sender {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.result-content {
  font-size: 14px;
  margin-bottom: 4px;
  line-height: 1.4;
}

.result-time {
  font-size: 11px;
  color: #999;
}

.no-results {
  margin-top: 32px;
  text-align: center;
}

/* 提及高亮样式 */
:deep(.mention) {
  color: #1890ff;
  background: rgba(24, 144, 255, 0.1);
  padding: 1px 4px;
  border-radius: 3px;
  font-weight: 500;
}

/* 搜索高亮样式 */
:deep(mark) {
  background: #fff2d7;
  padding: 1px 2px;
  border-radius: 2px;
}
</style> 