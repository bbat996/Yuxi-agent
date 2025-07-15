<template>
  <div class="chat-container" ref="chatContainerRef">
    <div
      class="sidebar-backdrop"
      v-if="state.isSidebarOpen && isSmallContainer"
      @click="toggleSidebar"
    ></div>
    <div class="chat">
      <div class="chat-header">
        <div class="header__left">
          <slot name="header-left" class="nav-btn"></slot>
        </div>
        <div class="header__center">
          <div @click="console.log(currentChat)" class="center-title">
            {{ currentChat?.title }}
          </div>
          <slot name="header-center"></slot>
        </div>
        <div class="header__right">
          <!-- 分享按钮 -->
          <div class="nav-btn" @click="shareChat" v-if="currentChatId && currentAgent">
            <ShareAltOutlined style="font-size: 18px" />
          </div>
          <!-- <div class="nav-btn test-history" @click="getAgentHistory" v-if="currentChatId && currentAgent">
            <ThunderboltOutlined />
          </div> -->
          <slot name="header-right"></slot>
        </div>
      </div>

      <div v-if="isLoading" class="chat-loading">
        <LoadingOutlined />
        <span>正在加载历史记录...</span>
      </div>

      <div class="chat-box" ref="messagesContainer">
        <div class="conv-box" v-for="(conv, index) in convs" :key="index">
          <AgentMessageComponent
            v-for="(message, index) in conv.messages"
            :message="message"
            :key="index"
            :is-processing="state.isProcessingRequest"
            :debug-mode="state.debug_mode"
            :show-refs="showMsgRefs(message)"
            @retry="retryMessage(message)"
          >
          </AgentMessageComponent>
          <!-- 显示对话最后一个消息使用的模型 -->
          <RefsComponent
            v-if="getLastMessage(conv)"
            :message="getLastMessage(conv)"
            :show-refs="['model', 'copy']"
            :is-latest-message="false"
          />
        </div>
        <div class="conv-box" v-if="onGoingConv.messages.length > 0">
          <AgentMessageComponent
            v-for="(message, index) in onGoingConv.messages"
            :message="message"
            :key="index"
            :is-processing="state.isProcessingRequest"
            :debug-mode="state.debug_mode"
            :show-refs="showMsgRefs(message)"
            @retry="retryMessage(message)"
          >
          </AgentMessageComponent>
        </div>

        <!-- 生成中的加载状态 -->
        <div
          class="generating-status"
          v-if="state.isProcessingRequest && !state.waitingServerResponse"
        >
          <div class="generating-indicator">
            <div class="loading-dots">
              <div></div>
              <div></div>
              <div></div>
            </div>
            <span class="generating-text">正在生成回复...</span>
          </div>
        </div>
      </div>
      <div class="bottom">
        <div class="message-input-wrapper">
          <MessageInputComponent
            v-model="userInput"
            :is-loading="state.isProcessingRequest"
            :disabled="!currentAgent"
            :send-button-disabled="!userInput || !currentAgent || state.isProcessingRequest"
            :placeholder="'输入问题...'"
            @send="handleSendMessage"
            @keydown="handleKeyDown"
          />
          <div class="bottom-actions">
            <p class="note" @click="getAgentHistory">请注意辨别内容的可靠性</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, nextTick, computed, onUnmounted, toRaw } from 'vue'
import { message } from 'ant-design-vue'
import MessageInputComponent from '@/components/message/MessageInputComponent.vue'
import AgentMessageComponent from '@/components/agent/AgentMessageComponent.vue'
import RefsComponent from '@/components/message/RefsComponent.vue'
import { chatApi, threadApi } from '@/apis/auth_api'

// 新增props属性，允许父组件传入agentId
const props = defineProps({
  agentId: {
    type: String,
    default: null
  },
  config: {
    type: Object,
    default: () => ({})
  },
  state: {
    type: Object,
    default: () => ({})
  }
})

// ==================== 状态管理 ====================

// UI状态
const state = reactive({
  ...props.state,
  debug_mode: computed(() => props.state.debug_mode ?? false),
  isSidebarOpen: localStorage.getItem('chat_sidebar_open') === 'true' || false,
  waitingServerResponse: false,
  isProcessingRequest: false,
  creatingNewChat: false,
  isInitialRender: true
})

// 容器宽度检测
const chatContainerRef = ref(null)
const containerWidth = ref(0)
const isSmallContainer = computed(() => containerWidth.value <= 520)
const isMediumContainer = computed(() => containerWidth.value <= 768)
let resizeObserver = null

// 滚动控制相关
const shouldAutoScroll = ref(true) // 是否应该自动滚动
const isUserScrolling = ref(false) // 用户是否正在滚动
let scrollTimer = null

// MCP调用日志和统计
const mcpLogs = ref([])
const chatStats = reactive({
  messageCount: 0,
  tokenCount: 0,
  toolCalls: 0,
  duration: 0,
  startTime: null
})

// 监听容器大小变化和滚动事件
onMounted(() => {
  // 初始计算容器宽度
  nextTick(() => {
    if (chatContainerRef.value) {
      // 初始时测量容器宽度
      containerWidth.value = chatContainerRef.value.offsetWidth

      resizeObserver = new ResizeObserver((entries) => {
        for (let entry of entries) {
          containerWidth.value = entry.contentRect.width
        }
      })

      resizeObserver.observe(chatContainerRef.value)
    }

    // 添加滚动监听
    const chatContainer = document.querySelector('.chat')
    if (chatContainer) {
      chatContainer.addEventListener('scroll', handleScroll, { passive: true })
    }
  })

  // 延迟移除初始渲染标记，防止切换动画
  setTimeout(() => {
    state.isInitialRender = false
  }, 300)
})

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
  }

  // 清理滚动监听器
  const chatContainer = document.querySelector('.chat')
  if (chatContainer) {
    chatContainer.removeEventListener('scroll', handleScroll)
  }
})

// ==================== 智能体信息面板相关方法 ====================

// 处理信息面板切换
const handleInfoPanelToggle = (collapsed) => {
  console.log('智能体信息面板切换:', collapsed)
}

// 组件卸载时清理定时器
onUnmounted(() => {
  if (scrollTimer) {
    clearTimeout(scrollTimer)
  }
})

const showMsgRefs = (msg) => {
  if (msg.isLast) {
    return ['copy']
  }
  return false
}

// 获取对话的最后一个消息
const getLastMessage = (conv) => {
  if (!conv || !conv.messages || conv.messages.length === 0) {
    return null
  }
  // 查找最后一个AI消息
  for (let i = conv.messages.length - 1; i >= 0; i--) {
    const message = conv.messages[i]
    if (message.type === 'ai') {
      return message
    }
  }
  return null
}

// DOM引用
const messagesContainer = ref(null)

// 数据状态
const agents = ref({}) // 智能体列表
const userInput = ref('') // 用户输入
const currentChatId = ref(null) // 当前对话ID
const chatsList = ref([]) // 对话列表
const isLoading = ref(false) // 是否处于加载状态

const convs = ref([])
const currentAgent = computed(() => agents.value[props.agentId])
const currentChat = computed(() => chatsList.value.find((chat) => chat.id === currentChatId.value))

const onGoingConv = reactive({
  msgChunks: {},
  messages: computed(() => {
    const msgs = Object.values(onGoingConv.msgChunks).map((msgs) => {
      return mergeMessageChunk(msgs)
    })
    return msgs.length > 0
      ? convertToolResultToMessages(msgs).filter((msg) => msg.type !== 'tool')
      : []
  })
})
const lastConv = computed(() => convs.value[convs.value.length - 1])
const lastConvMessages = computed(() => lastConv.value.messages[lastConv.value.messages.length - 1])

// ==================== 工具调用相关 ====================

// 工具调用相关
const toolCalls = ref([]) // 工具调用列表
const currentToolCallId = ref(null) // 当前工具调用ID
const currentRunId = ref(null) // 当前运行ID
const expandedToolCalls = ref(new Set()) // 展开的工具调用集合

// 创建新对话
const createNewChat = async () => {
  // 确保有AgentID
  if (!props.agentId) {
    console.warn('未指定AgentID，无法创建对话')
    return
  }

  // 如果当前对话正在创建，则不创建新对话
  if (state.creatingNewChat || state.isProcessingRequest) {
    console.warn('正在创建新对话或处理请求，无法创建新对话')
    return
  }

  if (currentChatId.value && convs.value.length === 0) {
    return
  }

  try {
    // 调用API创建新对话
    state.creatingNewChat = true
    const response = await threadApi.createThread(props.agentId, '新对话')
    if (!response || !response.id) {
      throw new Error('创建对话失败')
    }

    // 切换到新对话
    currentChatId.value = response.id
    resetThread()

    // 刷新对话列表
    loadChatsList()
  } catch (error) {
    console.error('创建对话失败:', error)
    message.error('创建对话失败')
  } finally {
    state.creatingNewChat = false
  }
}

// 重命名对话
const renameChat = async (data) => {
  let { chatId, title } = data

  if (!chatId || !title) {
    console.warn('未指定对话ID或标题，无法重命名对话')
    return
  }

  // 确保有AgentID
  if (!props.agentId) {
    console.warn('未指定AgentID，无法重命名对话')
    return
  }

  // 最长 30个字符，自动截断
  if (title.length > 30) {
    title = title.slice(0, 30)
  }

  try {
    // 调用API更新对话
    await threadApi.updateThread(chatId, title)

    // 刷新对话列表
    loadChatsList()
  } catch (error) {
    console.error('重命名对话失败:', error)
    message.error('重命名对话失败')
  }
}

// ==================== 状态管理函数 ====================

// 重试消息
const retryMessage = (msg) => {
  message.info('重试消息开发中')
  return
}

// 分享对话
const shareChat = () => {
  if (!currentChatId.value || !currentAgent.value) {
    message.warning('请先选择对话')
    return
  }

  try {
    // 生成HTML内容
    const htmlContent = generateChatHTML()

    // 创建下载链接
    const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')

    // 生成文件名
    const chatTitle = currentChat.value?.title || '新对话'
    const timestamp = new Date().toLocaleString('zh-CN').replace(/[:/\s]/g, '-')
    const filename = `${chatTitle}-${timestamp}.html`

    link.href = url
    link.download = filename
    link.style.display = 'none'

    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    // 清理URL对象
    URL.revokeObjectURL(url)

    message.success('对话已导出为HTML文件')
  } catch (error) {
    console.error('导出对话失败:', error)
    message.error('导出对话失败')
  }
}

// 生成对话的HTML内容
const generateChatHTML = () => {
  const chatTitle = currentChat.value?.title || '新对话'
  const agentName = currentAgent.value?.name || '智能助手'
  const agentDescription = currentAgent.value?.description || ''
  const exportTime = new Date().toLocaleString('zh-CN')

  // 获取所有对话消息
  const allMessages = []

  // 添加历史对话消息
  convs.value.forEach((conv) => {
    conv.messages.forEach((msg) => {
      allMessages.push(msg)
    })
  })

  // 添加当前进行中的对话消息
  onGoingConv.messages.forEach((msg) => {
    allMessages.push(msg)
  })

  if (allMessages.length === 0) {
    throw new Error('没有可导出的对话内容')
  }

  // 生成HTML内容
  let messagesHTML = ''

  allMessages.forEach((msg, index) => {
    const isUser = msg.type === 'human'
    const avatar = isUser ? '👤' : '🤖'
    const senderName = isUser ? '用户' : agentName
    const messageClass = isUser ? 'user-message' : 'ai-message'

    // 处理消息内容
    let content = msg.content.trim() || ''

    // 处理换行
    content = content.replace(/\n/g, '<br>')

    // 处理思考过程
    let reasoningHTML = ''
    if (!isUser && (msg.additional_kwargs?.reasoning_content || msg.reasoning_content)) {
      const reasoningContent = (msg.additional_kwargs?.reasoning_content || msg.reasoning_content)
        .trim()
        .replace(/\n/g, '<br>')
      reasoningHTML = `
        <div class="reasoning-section">
          <div class="reasoning-header">💭 思考过程</div>
          <div class="reasoning-content">${reasoningContent}</div>
        </div>
      `
    }

    // 处理工具调用
    let toolCallsHTML = ''
    if (msg.tool_calls && msg.tool_calls.length > 0) {
      toolCallsHTML = '<div class="tool-calls">'
      msg.tool_calls.forEach((toolCall) => {
        console.log(toolCall)
        const args = toolCall.function?.arguments
          ? JSON.parse(toolCall.function?.arguments)
          : toolCall?.args || '{}'
        toolCallsHTML += `
          <div class="tool-call">
            <div class="tool-call-header">
              <strong>🔧 ${toolCall.function?.name || '工具调用'}</strong>
            </div>
            <div class="tool-call-args">
              <pre>${JSON.stringify(args, null, 2)}</pre>
            </div>
            ${
              toolCall.tool_call_result
                ? `
              <div class="tool-call-result">
                <div class="tool-result-header">执行结果:</div>
                <div class="tool-result-content">${toolCall.tool_call_result.content || ''}</div>
              </div>
            `
                : ''
            }
          </div>
        `
      })
      toolCallsHTML += '</div>'
    }

    messagesHTML += `
      <div class="message ${messageClass}">
        <div class="message-header">
          <span class="avatar">${avatar}</span>
          <span class="sender">${senderName}</span>
          <span class="time">${new Date().toLocaleString('zh-CN')}</span>
        </div>
        <div class="message-content">
          ${reasoningHTML}
          ${content}
          ${toolCallsHTML}
        </div>
      </div>
    `
  })

  // 完整的HTML模板
  return `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${chatTitle} - 对话导出</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: white;
            margin: 0;
            padding: 0;
        }

        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            min-height: 100vh;
        }

        .header {
            background: #f8f9fa;
            border-bottom: 2px solid #e9ecef;
            padding: 24px;
            text-align: center;
        }

        .header h1 {
            font-size: 24px;
            margin-bottom: 8px;
            color: #212529;
            font-weight: 600;
        }

        .header .agent-info {
            font-size: 14px;
            color: #6c757d;
            margin-bottom: 12px;
        }

        .header .export-info {
            font-size: 12px;
            color: #868e96;
            padding-top: 12px;
            border-top: 1px solid #dee2e6;
        }

        .messages {
            padding: 32px 48px;
            max-width: 100%;
        }

        .message {
            margin-bottom: 32px;
            max-width: 100%;
        }

        .message:last-child {
            margin-bottom: 0;
        }

        .message-header {
            display: flex;
            align-items: center;
            margin-bottom: 12px;
            font-size: 14px;
            color: #666;
        }

        .avatar {
            font-size: 16px;
            margin-right: 8px;
        }

        .sender {
            font-weight: 600;
            margin-right: 12px;
        }

        .time {
            font-size: 12px;
            color: #999;
        }

        .message-content {
            padding: 16px 20px;
            border-radius: 8px;
            width: 100%;
            max-width: 100%;
        }

        .user-message .message-content {
            color: white;
            background: #1C6586;
            border: 1px solid #1C6586;
            width: fit-content;
        }

        .ai-message .message-content {
            background: white;
            border: 1px solid #e9ecef;
        }

        .reasoning-section {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 16px;
        }

        .reasoning-header {
            font-size: 13px;
            font-weight: 600;
            color: #495057;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
        }

        .reasoning-content {
            font-size: 14px;
            color: #6c757d;
            font-style: italic;
            line-height: 1.5;
        }

        .tool-calls {
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid #e9ecef;
        }

        .tool-call {
            background: #fff8e1;
            border: 1px solid #ffe082;
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 12px;
        }

        .tool-call:last-child {
            margin-bottom: 0;
        }

        .tool-call-header {
            font-size: 14px;
            color: #f57f17;
            margin-bottom: 8px;
            font-weight: 600;
        }

        .tool-call-args {
            background: rgba(0,0,0,0.04);
            border-radius: 4px;
            padding: 8px;
            margin-bottom: 8px;
        }

        .tool-call-args pre {
            font-size: 12px;
            color: #666;
            white-space: pre-wrap;
            word-break: break-all;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        }

        .tool-call-result {
            background: #e8f5e8;
            border: 1px solid #c8e6c9;
            border-radius: 4px;
            padding: 8px;
            word-break: break-all;
        }

        .tool-result-header {
            font-size: 12px;
            color: #2e7d32;
            font-weight: 600;
            margin-bottom: 4px;
        }

        .tool-result-content {
            font-size: 13px;
            color: #388e3c;
        }

        .footer {
            background: #f8f9fa;
            text-align: center;
            padding: 16px;
            font-size: 12px;
            color: #666;
            border-top: 1px solid #e9ecef;
        }

        .footer a {
            color: #007bff;
            text-decoration: none;
        }

        @media (max-width: 768px) {
            .messages {
                padding: 24px 16px;
            }

            .header {
                padding: 16px;
            }

            .user-message .message-content {
                margin-left: 10%;
            }

            .ai-message .message-content {
                margin-right: 10%;
            }
        }

        @media (max-width: 480px) {
            .user-message .message-content,
            .ai-message .message-content {
                margin-left: 0;
                margin-right: 0;
            }
        }

        @media print {
            body {
                background: white;
                margin: 0;
                padding: 0;
            }

            .container {
                box-shadow: none;
                border-radius: 0;
                max-width: 100%;
            }

            .header {
                background: #f8f9fa !important;
                -webkit-print-color-adjust: exact;
            }

            .messages {
                padding: 20px;
            }

            .user-message .message-content {
                background: #e3f2fd !important;
                -webkit-print-color-adjust: exact;
            }

            .reasoning-section {
                background: #f8f9fa !important;
                -webkit-print-color-adjust: exact;
            }

            .tool-call {
                background: #fff8e1 !important;
                -webkit-print-color-adjust: exact;
            }

            .tool-call-result {
                background: #e8f5e8 !important;
                -webkit-print-color-adjust: exact;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>${chatTitle}</h1>
            <div class="agent-info">
                智能体: ${agentName}
                ${agentDescription ? ` | ${agentDescription}` : ''}
            </div>
            <div class="export-info">
                导出时间: ${exportTime} | 共 ${allMessages.length} 条消息
            </div>
        </div>

        <div class="messages">
            ${messagesHTML}
        </div>

        <div class="footer">
            本对话由 Yuxi-Know 智能对话系统导出 | <a href="#">了解更多</a>
        </div>
    </div>
</body>
</html>
  `
}

// 重置线程
const resetThread = () => {
  convs.value = []
  toolCalls.value = []
  currentToolCallId.value = null
  currentRunId.value = null
  expandedToolCalls.value.clear()
}

// ==================== 消息处理 ====================

// 发送消息
const handleSendMessage = () => {
  if (!userInput.value || !currentAgent.value || state.isProcessingRequest) return
  const tempUserInput = userInput.value
  userInput.value = '' // 立即清空输入框
  // 确保UI更新后再发送消息
  nextTick(() => {
    sendMessageToServer(tempUserInput)
  })
}

// 使用文本发送消息
const sendMessageToServer = async (text) => {
  if (!text || !currentAgent.value || state.isProcessingRequest) return

  // 如果是第一条消息，以消息内容重命名对话
  if (convs.value.length === 0) {
    renameChat({ chatId: currentChatId.value, title: text })
  }

  // 发送消息时启用自动滚动
  shouldAutoScroll.value = true
  state.isProcessingRequest = true
  await scrollToBottom()

  // 设置请求参数
  const requestData = {
    query: text.trim(),
    config: {
      ...props.config,
      thread_id: currentChatId.value
    },
    meta: {
      request_id: currentAgent.value.name + '-' + new Date().getTime()
    }
  }

  try {
    state.waitingServerResponse = true

    const response = await chatApi.sendAgentMessage(currentAgent.value.name, requestData)
    if (!response.ok) {
      throw new Error('请求失败')
    }
    await handleStreamResponse(response)
  } catch (error) {
    handleSendMessageToServerError(error)
  } finally {
    state.waitingServerResponse = false
    state.isProcessingRequest = false
    await scrollToBottom()
  }
}

const handleSendMessageToServerError = (error) => {
  console.error('发送消息错误:', error)
  return
}

// 处理流式响应
const handleStreamResponse = async (response) => {
  try {
    const reader = response.body.getReader()
    let buffer = ''
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || '' // 保留最后一行可能不完整的内容

      for (const line of lines) {
        if (line.trim()) {
          try {
            const data = JSON.parse(line.trim())
            await processResponseChunk(data)
          } catch (e) {
            console.debug('解析JSON出错:', e.message)
          }
        }
      }
      await scrollToBottom()
    }
    // 处理缓冲区中可能剩余的内容
    if (buffer.trim()) {
      try {
        const data = JSON.parse(buffer.trim())
        await processResponseChunk(data)
      } catch (e) {
        console.warn('最终缓冲区内容无法解析:', buffer)
      }
    }
  } catch (error) {
    handleStreamResponseError(error)
  } finally {
    state.isProcessingRequest = false
    // await scrollToBottom();
  }
}

const handleStreamResponseError = (error) => {
  console.error('流式处理出错:', error)
  return
}

// 处理流数据
const processResponseChunk = async (data) => {
  // console.log("处理流数据:", data.msg);
  // if (data.msg.additional_kwargs?.tool_calls) {
  //   console.log("tool_calls", data.msg.additional_kwargs.tool_calls);
  // }
  if (data.status === 'init') {
    // 代表服务端收到请求并返回第一个响应
    state.waitingServerResponse = false
    console.log('处理流数据:', data.msg)
    onGoingConv.msgChunks[data.request_id] = [data.msg]
  } else if (data.status === 'loading') {
    if (data.msg.id) {
      if (!onGoingConv.msgChunks[data.msg.id]) {
        onGoingConv.msgChunks[data.msg.id] = []
      }
      onGoingConv.msgChunks[data.msg.id].push(data.msg)
    }
  } else if (data.status === 'error') {
    console.error('流式处理出错:', data.message)
    message.error(data.message)
  } else if (data.status === 'finished') {
    await getAgentHistory()
  }
  // await scrollToBottom();
}

// 初始化所有数据
const initAll = async () => {
  try {
    isLoading.value = true
    // 获取智能体列表
    setTimeout(async () => {
      await fetchAgents() // 加载智能体数据
      await loadChatsList() // 加载对话列表以及对话历史
      isLoading.value = false
    }, 100)
  } catch (error) {
    console.error('组件挂载出错:', error)
    message.error(`加载数据失败: ${error}`)
    isLoading.value = false
  }
}

// 获取智能体列表
const fetchAgents = async () => {
  try {
    const data = await chatApi.getAgents()
    // 将数组转换为对象
    agents.value = data.agents.reduce((acc, agent) => {
      acc[agent.name] = agent
      return acc
    }, {})
    console.log('agents', agents.value)
  } catch (error) {
    console.error('获取智能体错误:', error)
  }
}

// 从服务器对话列表
const loadChatsList = async () => {
  try {
    if (!props.agentId) {
      console.warn('未指定AgentID，无法加载状态')
      return
    }

    // 获取对话列表
    const threads = await threadApi.getThreads(props.agentId)

    if (threads && Array.isArray(threads) && threads.length > 0) {
      // 如果有对话，则加载最近的一个
      chatsList.value = threads
      currentChatId.value = threads[0].id // 假设已按更新时间排序
      await getAgentHistory()
    } else {
      // 如果没有对话，创建新对话
      await createNewChat()
    }
  } catch (error) {
    console.error('从服务器加载状态出错:', error)
  }
}

// 获取智能体历史记录
const getAgentHistory = async () => {
  if (!props.agentId || !currentChatId.value) {
    console.warn('未选择智能体或对话ID')
    return
  }

  try {
    console.log(`正在获取智能体[${props.agentId}]的历史记录，对话ID: ${currentChatId.value}`)
    const response = await chatApi.getAgentHistory(props.agentId, currentChatId.value)
    console.log('智能体历史记录:', response)

    // 如果成功获取历史记录并且是数组
    if (response && Array.isArray(response.history)) {
      // 将服务器格式的历史记录转换为组件格式
      onGoingConv.msgChunks = {}
      convs.value = convertServerHistoryToMessages(response.history)

      // 加载历史记录后，启用自动滚动并滚动到底部
      shouldAutoScroll.value = true
      await nextTick()
      await scrollToBottom()
    } else {
      message.warning('未找到历史记录或格式不正确')
    }
  } catch (error) {
    console.error('获取智能体历史记录出错:', error)
    message.error('获取历史记录失败')
  }
}

const convertToolResultToMessages = (msgs) => {
  const toolResponseMap = new Map()
  for (const item of msgs) {
    if (item.type === 'tool' && item.tool_call_id) {
      toolResponseMap.set(item.tool_call_id, item)
    }
  }

  const convertedMsgs = msgs.map((item) => {
    if (item.type === 'ai' && item.tool_calls && item.tool_calls.length > 0) {
      return {
        ...item,
        tool_calls: item.tool_calls.map((toolCall) => {
          const toolResponse = toolResponseMap.get(toolCall.id)
          return {
            ...toolCall,
            tool_call_result: toolResponse || null
          }
        })
      }
    }
    return item
  })

  // console.log("convertedMsgs", convertedMsgs);
  return convertedMsgs
}

const convertServerHistoryToMessages = (serverHistory) => {
  // 第一步：将所有tool消息与对应的tool call合并
  const mergedHistory = convertToolResultToMessages(serverHistory)

  // 第三步：按照对话分组
  const conversations = []
  let currentConv = null

  for (const item of mergedHistory) {
    if (item.type === 'human') {
      currentConv = {
        messages: [item],
        status: 'loading'
      }
      conversations.push(currentConv)
    } else if (item.type === 'ai' && currentConv) {
      currentConv.messages.push(item)

      if (item.response_metadata?.finish_reason === 'stop') {
        item.isLast = true
        currentConv.status = 'finished'
        currentConv = null
      }
    }
  }

  console.log('conversations', conversations)
  return conversations
}

// 组件挂载时加载状态
onMounted(async () => {
  await initAll()
})

// 监听agentId变化
onMounted(() => {
  watch(
    () => props.agentId,
    async (newAgentId, oldAgentId) => {
      try {
        console.log('智能体ID变化', oldAgentId, '->', newAgentId)

        // 如果变化了，重置会话并加载新数据
        if (newAgentId !== oldAgentId) {
          await initAll()
        }
      } catch (error) {
        console.error('智能体ID变化处理出错:', error)
        isLoading.value = false
      }
    }
  )
})

// 监听消息变化自动滚动
watch(
  [convs, () => onGoingConv.messages],
  () => {
    scrollToBottom()
  },
  { deep: true }
)

// ==================== 用户交互处理 ====================

// 检查是否在底部（允许一定误差）
const isAtBottom = () => {
  const container = document.querySelector('.chat')
  if (!container) return false

  const threshold = 100 // 距离底部100px内认为是在底部
  const isBottom =
    container.scrollHeight - container.scrollTop - container.clientHeight <= threshold
  return isBottom
}

// 处理滚动事件
const handleScroll = () => {
  if (scrollTimer) {
    clearTimeout(scrollTimer)
  }

  // 标记用户正在滚动
  isUserScrolling.value = true

  // 检查是否在底部
  const atBottom = isAtBottom()
  shouldAutoScroll.value = atBottom

  // 滚动结束后一段时间重置用户滚动状态
  scrollTimer = setTimeout(() => {
    isUserScrolling.value = false
  }, 150)
}

// 智能滚动到底部
const scrollToBottom = async () => {
  await nextTick()

  // 只有在应该自动滚动时才执行
  if (!shouldAutoScroll.value) return

  const container = document.querySelector('.chat')
  if (!container) return

  const scrollOptions = { top: container.scrollHeight, behavior: 'smooth' }

  // 多次尝试滚动以确保成功
  container.scrollTo(scrollOptions)
  setTimeout(() => {
    if (shouldAutoScroll.value) {
      container.scrollTo(scrollOptions)
    }
  }, 50)
  setTimeout(() => {
    if (shouldAutoScroll.value) {
      container.scrollTo(scrollOptions)
    }
  }, 150)
  setTimeout(() => {
    if (shouldAutoScroll.value) {
      container.scrollTo({ top: container.scrollHeight, behavior: 'auto' })
    }
  }, 300)
}

const toggleSidebar = () => {
  state.isSidebarOpen = !state.isSidebarOpen
  localStorage.setItem('chat_sidebar_open', state.isSidebarOpen)
  console.log('toggleSidebar', state.isSidebarOpen)
}

// 处理键盘事件
const handleKeyDown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    // 只有在满足条件时才发送
    if (userInput.value.trim() && currentAgent.value && !state.isProcessingRequest) {
      const tempUserInput = userInput.value
      userInput.value = '' // 立即清空输入框
      // 使用异步调用确保清空先发生
      setTimeout(() => {
        sendMessageToServer(tempUserInput)
      }, 0)
    }
  }
}

const mergeMessageChunk = (chunks) => {
  if (chunks.length === 0) return null

  // 以第一个chunk为基础
  for (const c of chunks) {
    if (c.additional_kwargs?.tool_calls) {
      console.warn('chunks', toRaw(c))
      break
    }
  }
  // 深拷贝第一个chunk作为结果
  const result = JSON.parse(JSON.stringify(chunks[0]))
  console.debug('result', toRaw(result))

  result.content = result.content || ''
  result.additional_kwargs = result.additional_kwargs || {}
  result.additional_kwargs.reasoning_content = result.additional_kwargs?.reasoning_content || ''

  // 合并其他chunks
  for (let i = 1; i < chunks.length; i++) {
    const chunk = chunks[i]

    // 合并content
    result.content += chunk.content || ''
    result.additional_kwargs.reasoning_content += chunk.additional_kwargs?.reasoning_content || ''

    // 如果是当前chunk没有的 key, value, 或者当前 result[key] 为空，则添加到result中
    for (const key in chunk) {
      if (!result[key]) {
        result[key] = JSON.parse(JSON.stringify(chunk[key]))
      }
    }

    // 合并tool_calls (如果存在)
    if (chunk.additional_kwargs?.tool_calls) {
      if (!result.additional_kwargs) result.additional_kwargs = {}
      if (!result.additional_kwargs.tool_calls) result.additional_kwargs.tool_calls = []

      for (const toolCall of chunk.additional_kwargs.tool_calls) {
        const existingToolCall = result.additional_kwargs.tool_calls.find(
          (t) => t.id === toolCall.id || t.index === toolCall.index
        )

        if (existingToolCall) {
          // 合并相同ID的tool call
          existingToolCall.function.arguments += toolCall.function.arguments
        } else {
          // 添加新的tool call
          result.additional_kwargs.tool_calls.push(JSON.parse(JSON.stringify(toolCall)))
        }
      }
    }
  }

  if (result.type === 'AIMessageChunk') {
    result.type = 'ai'
    if (result.additional_kwargs?.tool_calls) {
      result.tool_calls = result.additional_kwargs.tool_calls
    }
  }
  return result
}
</script>

<style lang="less" scoped>
@import '@/assets/css/main.css';

.chat-container {
  display: flex;
  width: 100%;
  height: 100%;
  position: relative;
}

.sidebar-backdrop {
  display: none; /* 默认隐藏，通过v-if控制显示 */
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.4);
  z-index: 99;
  animation: fadeIn 0.3s ease;
}

.floating-sidebar {
  position: absolute !important;
  z-index: 100;
  height: 100%;
  left: 0;
  top: 0;
  transform: translateX(0);
  transition: transform 0.3s ease;
  width: 80% !important;
  max-width: 300px;

  &.no-transition {
    transition: none !important;
  }

  &.collapsed {
    transform: translateX(-100%);
  }
}

.chat {
  position: relative;
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-x: hidden;
  background: white;
  position: relative;
  box-sizing: border-box;
  overflow-y: scroll;
  transition: all 0.3s ease;

  .chat-header {
    user-select: none;
    position: sticky;
    top: 0;
    z-index: 10;
    background-color: white;
    height: var(--header-height);
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    border-bottom: 1px solid var(--main-light-3);

    .header__left,
    .header__right,
    .header__center {
      display: flex;
      align-items: center;
    }

    .center-title {
      max-width: 200px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }

  .nav-btn {
    height: 2.5rem;
    display: flex;
    justify-content: center;
    align-items: center;
    border-radius: 8px;
    color: var(--gray-900);
    cursor: pointer;
    font-size: 15px;
    width: auto;
    padding: 0.5rem 1rem;
    transition: background-color 0.3s;

    .text {
      margin-left: 10px;
    }

    &:hover {
      background-color: var(--main-light-3);
    }

    .nav-btn-icon {
      width: 1.5rem;
      height: 1.5rem;
    }
  }
}

.chat-examples {
  padding: 0 50px;
  text-align: center;
  position: absolute;
  top: 20%;
  width: 100%;
  z-index: 9;
  animation: slideInUp 0.5s ease-out;

  h1 {
    margin-bottom: 20px;
    font-size: 1.2rem;
    color: var(--gray-900);
  }

  p {
    color: var(--gray-700);
  }
}

.chat-loading {
  padding: 0 50px;
  text-align: center;
  position: absolute;
  top: 20%;
  width: 100%;
  z-index: 9;
  animation: slideInUp 0.5s ease-out;

  span {
    margin-left: 8px;
    color: var(--gray-700);
  }
}

.chat-box {
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
  flex-grow: 1;
  padding: 1rem 2rem;
  display: flex;
  flex-direction: column;

  .tool-calls-container {
    width: 100%;
    margin-top: 10px;

    .tool-call-container {
      margin-bottom: 10px;

      &:last-child {
        margin-bottom: 0;
      }
    }
  }
}

.conv-box {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.bottom {
  position: sticky;
  bottom: 0;
  width: 100%;
  margin: 0 auto;
  padding: 4px 2rem 0 2rem;
  background: white;

  .message-input-wrapper {
    width: 100%;
    max-width: 800px;
    margin: 0 auto;

    .bottom-actions {
      display: flex;
      justify-content: center;
      align-items: center;
    }

    .note {
      font-size: small;
      color: #ccc;
      margin: 4px 0;
      user-select: none;
    }
  }
}

.conversation-list::-webkit-scrollbar {
  position: absolute;
  width: 4px;
  height: 4px;
}

.conversation-list::-webkit-scrollbar-track {
  background: transparent;
  border-radius: 4px;
}

.conversation-list::-webkit-scrollbar-thumb {
  background: var(--gray-400);
  border-radius: 4px;
}

.conversation-list::-webkit-scrollbar-thumb:hover {
  background: rgb(100, 100, 100);
  border-radius: 4px;
}

.chat::-webkit-scrollbar {
  position: absolute;
  width: 4px;
  height: 4px;
}

.chat::-webkit-scrollbar-track {
  background: transparent;
  border-radius: 4px;
}

.chat::-webkit-scrollbar-thumb {
  background: var(--gray-400);
  border-radius: 4px;
}

.chat::-webkit-scrollbar-thumb:hover {
  background: rgb(100, 100, 100);
  border-radius: 4px;
}

.loading-dots {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.loading-dots div {
  width: 8px;
  height: 8px;
  margin: 0 4px;
  background-color: var(--gray-700);
  border-radius: 50%;
  opacity: 0.3;
  animation: pulse 0.5s infinite ease-in-out both;
}

.loading-dots div:nth-child(1) {
  animation-delay: -0.32s;
}

.loading-dots div:nth-child(2) {
  animation-delay: -0.16s;
}

.generating-status {
  display: flex;
  justify-content: flex-start;
  padding: 0.8rem 0;
  animation: fadeInUp 0.3s ease-out;
}

.generating-indicator {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  background: var(--gray-100);
  border-radius: 12px;
  border: 1px solid var(--gray-200);

  .generating-text {
    margin-left: 12px;
    color: var(--gray-700);
    font-size: 14px;
  }
}

.toggle-sidebar {
  cursor: pointer;

  &.nav-btn {
    height: 2.5rem;
    display: flex;
    justify-content: center;
    align-items: center;
    border-radius: 8px;
    color: var(--gray-900);
    cursor: pointer;
    font-size: 15px;
    width: auto;
    padding: 0.5rem 1rem;
    transition: background-color 0.3s;
    overflow: hidden;

    .text {
      margin-left: 10px;
    }

    &:hover {
      background-color: var(--main-light-3);
    }

    .nav-btn-icon {
      width: 1.5rem;
      height: 1.5rem;
    }
  }
}

@keyframes pulse {
  0%,
  80%,
  100% {
    transform: scale(0.8);
    opacity: 0.3;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

@keyframes swing-in-top-fwd {
  0% {
    transform: rotateX(-100deg);
    transform-origin: top;
    opacity: 0;
  }
  100% {
    transform: rotateX(0deg);
    transform-origin: top;
    opacity: 1;
  }
}

@keyframes slideInUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

@media (max-width: 768px) {
  .chat-sidebar.collapsed {
    width: 0;
    border: none;
  }

  .chat-header {
    .header__left {
      .text {
        display: none;
      }
    }
  }
}

@media (max-width: 520px) {
  .sidebar-backdrop {
    display: block;
  }

  .chat-box {
    padding: 1rem 1rem;
  }

  .bottom {
    padding: 0.5rem 0.5rem;
  }

  .chat-header {
    padding: 0.5rem 1rem !important;

    .nav-btn {
      font-size: 14px !important;
      padding: 0.4rem 0.8rem !important;
    }
  }

  .floating-sidebar {
    position: fixed;
    z-index: 100;
    height: 100%;
    left: 0;
    top: 0;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    transform: translateX(0);
    transition: transform 0.3s ease;
    width: 80% !important;
    max-width: 300px;

    &.collapsed {
      transform: translateX(-100%);
    }
  }
}

.hide-text {
  display: none;
}
</style>