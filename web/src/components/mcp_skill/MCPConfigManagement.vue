<template>
  <div class="mcp-config-management">

    <!-- MCP功能列表 -->
    <div class="mcp-functions-section">
      <div class="section-header">
        <h4>MCP功能列表</h4>
        <div class="stats-info">
          <a-space>
            <span>总计: {{ totalServersCount }} 个服务器</span>
            <span>功能函数: {{ totalFunctionsCount }} 个</span>
          </a-space>
        </div>
        <a-space>
          <a-button type="primary" @click="showAddServerModal" :icon="h(PlusOutlined)">
            添加外部MCP
          </a-button>
          <a-input-search v-model:value="searchKeyword" placeholder="搜索MCP名称或描述" style="width: 200px"
            @search="handleSearch" @change="handleSearch" />
        </a-space>
      </div>

      <a-spin :spinning="loading.functions">
        <a-table :data-source="filteredServers" :columns="tableColumns" :pagination="false"
          :row-key="(record) => record.serverKey" class="mcp-servers-table" :row-class-name="getRowClassName">
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'name'">
              <div class="server-name-cell">
                <div class="server-name">{{ record.serverKey || '未知服务器' }}</div>
                <div class="server-description">{{ record.module_path || '无描述' }}</div>
                <div class="server-type">
                  <a-tag :color="record.is_external ? 'orange' : 'blue'" size="small">
                    {{ record.is_external ? '外部' : '内置' }}
                  </a-tag>
                </div>
              </div>
            </template>



            <template v-else-if="column.key === 'status'">
              <a-tag :color="(record.enabled !== false) ? 'green' : 'red'" size="small">
                {{ (record.enabled !== false) ? '启用' : '禁用' }}
              </a-tag>
            </template>

            <template v-else-if="column.key === 'functions'">
              <div class="functions-cell">
                <span class="functions-count">{{ getFunctionsCount(record) }} 个功能</span>
                <div v-if="getServerTools(record).length > 0" class="functions-preview">
                  <a-tag v-for="tool in getServerTools(record).slice(0, 2)"
                    :key="tool.name || tool.function_name || tool.id" color="cyan" size="small">
                    {{ getToolDisplayName(tool) }}
                  </a-tag>
                  <a-tag v-if="getServerTools(record).length > 2" color="default" size="small">
                    +{{ getServerTools(record).length - 2 }}个
                  </a-tag>
                </div>
                <div v-else class="no-functions">
                  <span class="text-muted">暂无功能函数</span>
                </div>
              </div>
            </template>

            <template v-else-if="column.key === 'enabled'">
              <a-switch :checked="record.enabled !== false"
                :loading="loading.toggle && currentToggleServer === record.serverKey"
                @change="(checked) => toggleServerStatus(record, checked)" size="small" />
            </template>

            <template v-else-if="column.key === 'actions'">
              <a-space>
                <a-button size="small" type="primary" @click="viewServerDetail(record)" :icon="h(EyeOutlined)">
                  详情
                </a-button>
                <a-button v-if="!record.is_external" size="small" @click="editServer(record)" :icon="h(EditOutlined)">
                  编辑
                </a-button>
                <a-button v-if="record.is_external" size="small" danger @click="deleteServer(record)" :icon="h(DeleteOutlined)">
                  删除
                </a-button>
              </a-space>
            </template>
          </template>
        </a-table>
      </a-spin>

      <!-- 空状态 -->
      <a-empty v-if="!loading.functions && filteredServers.length === 0" class="empty-state">
        <template #description>
          <span v-if="searchKeyword">没有找到符合条件的MCP服务器</span>
          <span v-else>没有可用的MCP服务器</span>
        </template>
      </a-empty>
    </div>

    <!-- 服务器详情模态框 -->
    <a-modal v-model:open="serverDetailVisible" title="服务器详情" width="900px" :footer="null">
      <div v-if="currentServer">
        <div class="server-detail-header">
          <h4>{{ currentServer.serverKey || '未知服务器' }}</h4>
          <div class="server-tags">
            <a-tag :color="(currentServer.enabled !== false) ? 'green' : 'red'">
              {{ (currentServer.enabled !== false) ? '启用' : '禁用' }}
            </a-tag>
            <a-tag :color="currentServer.is_external ? 'orange' : 'blue'">
              {{ currentServer.is_external ? '外部' : '内置' }}
            </a-tag>
          </div>
        </div>

        <a-descriptions :column="2" bordered class="server-info">
          <a-descriptions-item label="服务器名称">{{ currentServer.serverKey || '未知服务器' }}</a-descriptions-item>
          <a-descriptions-item label="模块路径">{{ currentServer.module_path || '无描述' }}</a-descriptions-item>
          <a-descriptions-item label="类名">{{ currentServer.class_name || '无描述' }}</a-descriptions-item>
          <a-descriptions-item label="配置路径">{{ currentServer.config_path || '无描述' }}</a-descriptions-item>
        </a-descriptions>

        <div v-if="getServerTools(currentServer).length > 0" class="functions-section">
          <h4>功能函数列表 ({{ getServerTools(currentServer).length }} 个):</h4>
          <a-list :data-source="getServerTools(currentServer)" size="large" class="functions-list">
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta>
                  <template #title>
                    <div class="function-title">
                      <span class="function-name">{{ getToolDisplayName(item) }}</span>
                      <a-tag v-if="item.category" color="blue" size="small">{{ item.category }}</a-tag>
                    </div>
                  </template>
                  <template #description>
                    <div class="function-description">
                      <p>{{ item.description || '无描述' }}</p>
                      <div v-if="item.parameters" class="function-schema">
                        <h6>输入参数:</h6>
                        <pre>{{ JSON.stringify(item.parameters, null, 2) }}</pre>
                      </div>
                    </div>
                  </template>
                </a-list-item-meta>
              </a-list-item>
            </template>
          </a-list>
        </div>
        <div v-else class="no-functions">
          <a-empty description="该服务器暂无功能函数" />
        </div>
      </div>
    </a-modal>

    <!-- 添加/编辑服务器模态框 -->
    <a-modal v-model:open="serverFormVisible" :title="serverFormMode === 'add' ? '添加外部MCP服务器' : '编辑MCP服务器'" 
      width="600px" @ok="handleServerFormSubmit" @cancel="handleServerFormCancel" :confirmLoading="loading.submit">
      <a-form ref="serverFormRef" :model="serverForm" :rules="serverFormRules" layout="vertical">
        <a-form-item label="服务器名称" name="serverKey">
          <a-input v-model:value="serverForm.serverKey" placeholder="请输入服务器名称" 
            :disabled="serverFormMode === 'edit'" />
        </a-form-item>
        <a-form-item label="模块路径" name="module_path">
          <a-input v-model:value="serverForm.module_path" placeholder="请输入模块路径" />
        </a-form-item>
        <a-form-item label="类名" name="class_name">
          <a-input v-model:value="serverForm.class_name" placeholder="请输入类名" />
        </a-form-item>
        <a-form-item label="配置路径" name="config_path">
          <a-input v-model:value="serverForm.config_path" placeholder="请输入配置路径" />
        </a-form-item>
        <a-form-item label="启用状态" name="enabled">
          <a-switch v-model:checked="serverForm.enabled" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, h } from 'vue'
import { message, Modal } from 'ant-design-vue'
import {
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  PlusOutlined
} from '@ant-design/icons-vue'
import { mcpConfigApi } from '@/apis/mcp_api'

// 状态管理
const loading = reactive({
  functions: false,
  toggle: false,
  submit: false
})

// 当前正在切换状态的服务器
const currentToggleServer = ref('')

// 数据状态
const servers = ref({})
const searchKeyword = ref('')

// 模态框状态
const serverDetailVisible = ref(false)
const currentServer = ref(null)
const serverFormVisible = ref(false)
const serverFormMode = ref('add') // 'add' | 'edit'

// 表单相关
const serverFormRef = ref()
const serverForm = reactive({
  serverKey: '',
  module_path: '',
  class_name: '',
  config_path: '',
  enabled: true
})

const serverFormRules = {
  serverKey: [
    { required: true, message: '请输入服务器名称' },
    { min: 1, max: 100, message: '服务器名称长度为1-100个字符' }
  ],
  module_path: [
    { required: true, message: '请输入模块路径' }
  ],
  class_name: [
    { required: true, message: '请输入类名' }
  ]
}

// 表格列定义
const tableColumns = [
  {
    title: '服务器名称',
    key: 'name',
    width: 300,
    ellipsis: true
  },
  {
    title: '功能函数',
    key: 'functions',
    width: 200,
    ellipsis: true
  },
  {
    title: '启用/禁用',
    key: 'enabled',
    width: 100,
    align: 'center'
  },
  {
    title: '状态',
    key: 'status',
    width: 80,
    align: 'center'
  },
  {
    title: '操作',
    key: 'actions',
    width: 180,
    align: 'center',
    fixed: 'right'
  }
]

// 计算属性
const isDevelopment = computed(() => {
  return import.meta.env.MODE === 'development'
})

const totalServersCount = computed(() => {
  return Object.keys(servers.value).length
})



const totalFunctionsCount = computed(() => {
  return Object.values(servers.value).reduce((sum, server) => {
    return sum + getServerTools(server).length
  }, 0)
})

const filteredServers = computed(() => {
  // 将对象转换为数组，包含服务器名称
  let filtered = Object.entries(servers.value).map(([key, server]) => ({
    ...server,
    serverKey: key // 添加服务器键名
  }))

  // 按服务器类型过滤（新数据结构中没有类型字段，暂时跳过）
  // if (selectedServerType.value) {
  //   filtered = filtered.filter(server => {
  //     const serverType = server.type || server.server_type || 'external'
  //     return serverType === selectedServerType.value
  //   })
  // }

  // 按搜索关键词过滤
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    filtered = filtered.filter(server => {
      const name = server.serverKey || ''
      const tools = getServerTools(server)

      return name.toLowerCase().includes(keyword) ||
        tools.some(tool => {
          const toolName = getToolDisplayName(tool).toLowerCase()
          const toolDesc = (tool.description || '').toLowerCase()
          return toolName.includes(keyword) || toolDesc.includes(keyword)
        })
    })
  }

  return filtered
})

// 方法
const getFunctionsCount = (server) => {
  return getServerTools(server).length
}

const getServerTools = (server) => {
  // 新的数据结构：直接使用 server.tools
  let tools = []

  // 调试服务器数据结构（仅在开发环境）
  if (isDevelopment.value) {
    console.log('服务器数据结构:', {
      hasTools: !!server.tools,
      serverKeys: Object.keys(server)
    })
  }

  // 直接使用 tools 字段
  if (server.tools && Array.isArray(server.tools)) {
    tools = server.tools
  }

  // 确保返回的是数组
  if (!Array.isArray(tools)) {
    if (isDevelopment.value) {
      console.warn('服务器工具数据不是数组:', tools)
    }
    tools = []
  }

  // 调试信息（仅在开发环境）
  if (isDevelopment.value && tools.length > 0) {
    console.log(`服务器有 ${tools.length} 个工具:`, tools.slice(0, 3))
  }

  return tools
}

const getToolDisplayName = (tool) => {
  // 新的数据结构：直接使用 tool.name
  if (tool.name) {
    return tool.name
  } else {
    if (isDevelopment.value) {
      console.warn('工具缺少名称字段:', tool)
    }
    return '未知工具'
  }
}

const refreshServers = async () => {
  try {
    loading.functions = true
    const response = await mcpConfigApi.getServers()
    if (response.success) {
      // 新的数据结构：直接使用 response.data.servers
      servers.value = response.data.servers || {}

      if (isDevelopment.value) {
        console.log('获取到的服务器数据:', servers.value)
        console.log('服务器数量:', Object.keys(servers.value).length)

        // 打印每个服务器的基本信息
        Object.entries(servers.value).forEach(([key, server]) => {
          console.log(`服务器 ${key}:`, {
            name: key, // 使用 key 作为服务器名称
            enabled: server.enabled,
            toolsCount: getServerTools(server).length
          })
        })
      }
    } else {
      message.error(response.message || '获取服务器列表失败')
    }
  } catch (error) {
    console.error('获取服务器列表失败:', error)
    message.error('获取服务器列表失败')
  } finally {
    loading.functions = false
  }
}

const viewServerDetail = (server) => {
  try {
    console.log('查看服务器详情:', server.serverKey)
    currentServer.value = server
    serverDetailVisible.value = true
  } catch (error) {
    console.error('显示服务器详情失败:', error)
    message.error('显示服务器详情失败')
  }
}

const showAddServerModal = () => {
  serverFormMode.value = 'add'
  resetServerForm()
  serverFormVisible.value = true
}

const editServer = (server) => {
  serverFormMode.value = 'edit'
  resetServerForm()
  
  // 填充表单数据
  serverForm.serverKey = server.serverKey
  serverForm.module_path = server.module_path || ''
  serverForm.class_name = server.class_name || ''
  serverForm.config_path = server.config_path || ''
  serverForm.enabled = server.enabled !== false
  
  serverFormVisible.value = true
}

const deleteServer = (server) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除服务器 "${server.serverKey}" 吗？此操作不可恢复。`,
    okText: '删除',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      try {
        const response = await mcpConfigApi.deleteServer(server.serverKey)
        if (response.success) {
          message.success('服务器删除成功')
          await refreshServers()
        } else {
          message.error(response.message || '删除服务器失败')
        }
      } catch (error) {
        console.error('删除服务器失败:', error)
        message.error('删除服务器失败')
      }
    }
  })
}

const resetServerForm = () => {
  serverForm.serverKey = ''
  serverForm.module_path = ''
  serverForm.class_name = ''
  serverForm.config_path = ''
  serverForm.enabled = true
}

const handleServerFormSubmit = async () => {
  try {
    await serverFormRef.value.validate()
    loading.submit = true

    const formData = {
      serverKey: serverForm.serverKey,
      module_path: serverForm.module_path,
      class_name: serverForm.class_name,
      config_path: serverForm.config_path,
      enabled: serverForm.enabled,
      is_external: serverFormMode.value === 'add'
    }

    let response
    if (serverFormMode.value === 'add') {
      response = await mcpConfigApi.addExternalServer(formData)
    } else {
      response = await mcpConfigApi.updateServerConfig(serverForm.serverKey, formData)
    }

    if (response.success) {
      message.success(`服务器${serverFormMode.value === 'add' ? '添加' : '更新'}成功`)
      serverFormVisible.value = false
      await refreshServers()
    } else {
      message.error(response.message || `服务器${serverFormMode.value === 'add' ? '添加' : '更新'}失败`)
    }
  } catch (error) {
    console.error('提交服务器表单失败:', error)
    message.error(`服务器${serverFormMode.value === 'add' ? '添加' : '更新'}失败`)
  } finally {
    loading.submit = false
  }
}

const handleServerFormCancel = () => {
  serverFormVisible.value = false
  resetServerForm()
}

const toggleServerStatus = async (server, checked) => {
  const serverName = server.serverKey
  try {
    currentToggleServer.value = serverName
    loading.toggle = true

    const response = await mcpConfigApi.toggleServerStatus(serverName, checked)
    
    if (response.success) {
      // 更新本地状态
      server.enabled = checked
      message.success(`${serverName} ${checked ? '启用' : '禁用'}成功`)
    } else {
      message.error(response.message || '切换服务器状态失败')
    }
  } catch (error) {
    console.error('切换服务器状态失败:', error)
    message.error('切换服务器状态失败')
  } finally {
    loading.toggle = false
    currentToggleServer.value = ''
  }
}

const getRowClassName = (record) => {
  return record.enabled === false ? 'disabled-row' : ''
}



const handleSearch = () => {
  // 搜索处理会自动触发 filteredServers 计算属性
  console.log('搜索关键词:', searchKeyword.value)
}



// 初始化
onMounted(async () => {
  await refreshServers()
})
</script>

<style lang="less" scoped>
.mcp-config-management {
  .description {
    color: var(--gray-600);
    margin-bottom: 24px;
  }

  .stats-info {
    margin-bottom: 24px;
    padding: 16px 20px;
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    color: var(--gray-600);
    font-size: 0.9em;
    font-weight: 500;
  }

  .stats-card {
    margin-bottom: 24px;
  }

  .mcp-functions-section {
    .section-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
      padding: 0 4px;

      h4 {
        margin: 0;
        font-size: 18px;
        font-weight: 600;
        color: #1e293b;
      }
    }

    .mcp-servers-table {
      background: #ffffff;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);

      :deep(.ant-table-thead > tr > th) {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border-bottom: 1px solid #e2e8f0;
        font-weight: 600;
        color: #475569;
        padding: 16px 12px;
      }

      :deep(.ant-table-tbody > tr > td) {
        padding: 16px 12px;
        border-bottom: 1px solid #f1f5f9;
        vertical-align: top;
      }

      :deep(.ant-table-tbody > tr:hover > td) {
        background: #f8fafc;
      }

      :deep(.ant-table-tbody > tr.disabled-row > td) {
        background: #f8fafc;
        opacity: 0.6;
      }

      .server-name-cell {
        .server-name {
          font-weight: 600;
          color: #1e293b;
          margin-bottom: 4px;
          font-size: 14px;
        }

        .server-description {
          color: #64748b;
          font-size: 12px;
          line-height: 1.4;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
          margin-bottom: 4px;
        }

        .server-type {
          display: flex;
          gap: 4px;
        }
      }

      .functions-cell {
        .functions-count {
          display: block;
          font-size: 12px;
          color: #475569;
          margin-bottom: 6px;
          font-weight: 500;
        }

        .functions-preview {
          display: flex;
          flex-wrap: wrap;
          gap: 4px;
        }

        .no-functions {
          font-size: 12px;
          color: #94a3b8;
          font-style: italic;
        }
      }
    }
  }
}

.server-detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e2e8f0;

  h4 {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
    color: #1e293b;
  }

  .server-tags {
    display: flex;
    gap: 8px;
  }
}

.server-info {
  margin-bottom: 24px;
}

.functions-section {
  h4 {
    margin-bottom: 16px;
    font-size: 16px;
    font-weight: 600;
    color: #1e293b;
  }
}

.functions-list {
  .function-title {
    display: flex;
    align-items: center;
    gap: 10px;

    .function-name {
      font-weight: 600;
      color: #1e293b;
    }
  }

  .function-description {
    p {
      margin-bottom: 10px;
      color: #475569;
      line-height: 1.5;
    }

    .function-schema {
      margin-top: 12px;

      h6 {
        margin-bottom: 6px;
        font-size: 13px;
        font-weight: 600;
        color: #374151;
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }

      pre {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        padding: 12px;
        border-radius: 8px;
        font-size: 12px;
        overflow-x: auto;
        border: 1px solid #e2e8f0;
        color: #475569;
      }
    }
  }
}

.no-functions {
  text-align: center;
  padding: 40px 24px;
}

.empty-state {
  margin-top: 60px;
}

// 优化标签样式
:deep(.ant-tag) {
  border-radius: 6px;
  font-weight: 500;
  font-size: 12px;
  padding: 2px 8px;
  border: none;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;

  &.ant-tag-green {
    background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
    color: #166534;
  }

  &.ant-tag-red {
    background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
    color: #dc2626;
  }

  &.ant-tag-blue {
    background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
    color: #1e40af;
  }

  &.ant-tag-orange {
    background: linear-gradient(135deg, #fed7aa 0%, #fdba74 100%);
    color: #c2410c;
  }

  &.ant-tag-cyan {
    background: linear-gradient(135deg, #cffafe 0%, #a5f3fc 100%);
    color: #0e7490;
  }

  &.ant-tag-default {
    background: #f1f5f9;
    color: #64748b;
  }
}

// 表格按钮样式
:deep(.ant-table-tbody) {
  .ant-btn {
    border-radius: 6px;
    font-weight: 500;
    height: 28px;
    padding: 0 10px;
    font-size: 12px;

    &.ant-btn-primary {
      background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
      border: none;

      &:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
      }
    }

    &.ant-btn-default {
      border: 1px solid #e2e8f0;
      color: #475569;

      &:hover {
        border-color: #3b82f6;
        color: #3b82f6;
      }
    }

    &.ant-btn-dangerous {
      background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
      border: none;
      color: white;

      &:hover {
        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
      }
    }
  }
}
</style>