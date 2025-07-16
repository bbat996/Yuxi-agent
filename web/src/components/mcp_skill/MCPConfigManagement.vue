<template>
  <div class="mcp-config-management">

    <!-- 操作按钮 -->
    <div class="action-bar">
      <a-space>
        <a-button @click="refreshAllData" :loading="loading.all" :icon="h(ReloadOutlined)">
          刷新数据
        </a-button>
        <a-button @click="reloadConfig" :loading="loading.reload" :icon="h(SyncOutlined)">
          重新加载配置
        </a-button>
        <a-button @click="validateConfig" :loading="loading.validation" :icon="h(SafetyOutlined)">
          验证配置
        </a-button>
      </a-space>
      
      <!-- 统计信息 -->
      <div class="stats-info">
        <a-space>
          <span>总计: {{ totalServersCount }} 个服务器</span>
          <span>内部: {{ builtinServersCount }} 个</span>
          <span>外部: {{ externalServersCount }} 个</span>
          <span>功能函数: {{ totalFunctionsCount }} 个</span>
        </a-space>
      </div>
    </div>



    <!-- MCP功能列表 -->
    <div class="mcp-functions-section">
      <div class="section-header">
        <h4>MCP功能列表</h4>
        <a-space>
          <a-select v-model:value="selectedServerType" placeholder="服务器类型" style="width: 120px"
            @change="handleServerTypeChange">
            <a-select-option value="">全部</a-select-option>
            <a-select-option value="builtin">内部</a-select-option>
            <a-select-option value="external">外部</a-select-option>
          </a-select>
          <a-input-search v-model:value="searchKeyword" placeholder="搜索MCP名称或描述" style="width: 200px"
            @search="handleSearch" @change="handleSearch" />
        </a-space>
      </div>

      <a-spin :spinning="loading.functions">
        <a-row :gutter="[16, 16]">
          <a-col v-for="server in filteredServers" :key="server.name" :xs="24" :sm="12" :md="8" :lg="6">
            <a-card :title="server.name || server.server_name || '未知服务器'" class="mcp-server-card"
              :class="{ 'disabled': !(server.enabled !== false) }" :hoverable="true">
              <template #extra>
                <a-space>
                  <a-tag :color="(server.enabled !== false) ? 'green' : 'red'">
                    {{ (server.enabled !== false) ? '启用' : '禁用' }}
                  </a-tag>
                  <a-tag :color="(server.type || server.server_type) === 'builtin' ? 'blue' : 'orange'">
                    {{ (server.type || server.server_type) === 'builtin' ? '内部' : '外部' }}
                  </a-tag>
                </a-space>
              </template>

              <div class="server-content">
                <div class="server-description">
                  <p>{{ server.description || server.server_description || '无描述' }}</p>
                </div>

                <div class="server-functions">
                  <h5>功能函数 ({{ getFunctionsCount(server) }})</h5>
                  <div class="functions-list">
                    <div v-if="getServerTools(server).length > 0" class="functions-grid">
                      <a-tag v-for="tool in getServerTools(server).slice(0, 3)" :key="tool.name || tool.function_name || tool.id"
                        color="cyan" size="small">
                        {{ getToolDisplayName(tool) }}
                      </a-tag>
                      <a-tag v-if="getServerTools(server).length > 3" color="default" size="small">
                        +{{ getServerTools(server).length - 3 }}个
                      </a-tag>
                    </div>
                    <div v-else class="no-functions">
                      <span class="text-muted">暂无功能函数</span>
                    </div>
                  </div>
                </div>

                <div class="server-actions">
                  <a-space>
                    <a-button size="small" type="primary" @click="viewServerDetail(server.name || server.server_name)" :icon="h(EyeOutlined)">
                      详情
                    </a-button>
                    <a-button size="small" @click="viewFunctions(server)" :icon="h(FunctionOutlined)">
                      功能
                    </a-button>
                  </a-space>
                </div>
              </div>
            </a-card>
          </a-col>
        </a-row>
      </a-spin>

      <!-- 空状态 -->
      <a-empty v-if="!loading.functions && filteredServers.length === 0" class="empty-state">
        <template #description>
          <span v-if="searchKeyword || selectedServerType">没有找到符合条件的MCP服务器</span>
          <span v-else>没有可用的MCP服务器</span>
        </template>
      </a-empty>
    </div>

    <!-- 服务器详情模态框 -->
    <a-modal v-model:open="serverDetailVisible" title="服务器详情" width="800px" :footer="null">
      <div v-if="currentServer">
        <a-descriptions :column="2" bordered>
          <a-descriptions-item label="服务器名称">{{ currentServer.name || currentServer.server_name || '未知服务器'
          }}</a-descriptions-item>
          <a-descriptions-item label="类型">
            <a-tag :color="(currentServer.type || currentServer.server_type) === 'builtin' ? 'blue' : 'orange'">
              {{ (currentServer.type || currentServer.server_type) === 'builtin' ? '内部' : '外部' }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="描述">{{ currentServer.description || currentServer.server_description || '无描述'
          }}</a-descriptions-item>
          <a-descriptions-item label="状态">
            <a-tag :color="(currentServer.enabled !== false) ? 'green' : 'red'">
              {{ (currentServer.enabled !== false) ? '启用' : '禁用' }}
            </a-tag>
          </a-descriptions-item>
        </a-descriptions>

        <div v-if="currentServer.tools_by_category || getServerTools(currentServer).length > 0" class="tools-section">
          <h4>功能函数分类:</h4>
          <a-collapse v-if="currentServer.tools_by_category">
            <a-collapse-panel v-for="(tools, category) in currentServer.tools_by_category" :key="category"
              :header="`${category} (${tools.length})`">
              <a-list :data-source="tools" size="small">
                <template #renderItem="{ item }">
                  <a-list-item>
                    <a-list-item-meta>
                      <template #title>{{ item.name || item.function_name }}</template>
                      <template #description>{{ item.description || '无描述' }}</template>
                    </a-list-item-meta>
                  </a-list-item>
                </template>
              </a-list>
            </a-collapse-panel>
          </a-collapse>
          <div v-else>
            <a-list :data-source="getServerTools(currentServer)" size="small">
              <template #renderItem="{ item }">
                <a-list-item>
                  <a-list-item-meta>
                    <template #title>{{ getToolDisplayName(item) }}</template>
                    <template #description>{{ item.description || '无描述' }}</template>
                  </a-list-item-meta>
                </a-list-item>
              </template>
            </a-list>
          </div>
        </div>
      </div>
    </a-modal>

    <!-- 功能函数详情模态框 -->
    <a-modal v-model:open="functionsDetailVisible" title="功能函数详情" width="900px" :footer="null">
      <div v-if="currentServerForFunctions">
        <div class="functions-header">
          <h4>{{ currentServerForFunctions.name || currentServerForFunctions.server_name || '未知服务器' }} - 功能函数列表</h4>
          <p class="server-description">{{ currentServerForFunctions.description ||
            currentServerForFunctions.server_description || '无描述' }}</p>
        </div>

        <div v-if="getServerTools(currentServerForFunctions).length > 0" class="functions-list">
          <a-list :data-source="getServerTools(currentServerForFunctions)" size="large">
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
                      <div v-if="item.inputSchema || item.schema" class="function-schema">
                        <h6>输入参数:</h6>
                        <pre>{{ JSON.stringify(item.inputSchema || item.schema, null, 2) }}</pre>
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
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, h } from 'vue'
import { message } from 'ant-design-vue'
import {
  ReloadOutlined,
  SafetyOutlined,
  SyncOutlined,
  EyeOutlined,
  FunctionOutlined
} from '@ant-design/icons-vue'
import { mcpConfigApi } from '@/apis/mcp_api'

// 状态管理
const loading = reactive({
  all: false,
  servers: false,
  validation: false,
  reload: false,
  functions: false
})

// 数据状态
const servers = ref({})
const configValid = ref(true)
const validationErrors = ref([])
const searchKeyword = ref('')
const selectedServerType = ref('')

// 模态框状态
const serverDetailVisible = ref(false)
const currentServer = ref(null)
const functionsDetailVisible = ref(false)
const currentServerForFunctions = ref(null)

// 计算属性
const totalServersCount = computed(() => {
  return Object.keys(servers.value).length
})

const builtinServersCount = computed(() => {
  return Object.values(servers.value).filter(server => {
    const serverType = server.type || server.server_type || 'external'
    return serverType === 'builtin'
  }).length
})

const externalServersCount = computed(() => {
  return Object.values(servers.value).filter(server => {
    const serverType = server.type || server.server_type || 'external'
    return serverType === 'external'
  }).length
})

const totalFunctionsCount = computed(() => {
  return Object.values(servers.value).reduce((sum, server) => {
    return sum + getServerTools(server).length
  }, 0)
})

const filteredServers = computed(() => {
  let filtered = Object.values(servers.value)

  // 按服务器类型过滤
  if (selectedServerType.value) {
    filtered = filtered.filter(server => {
      const serverType = server.type || server.server_type || 'external'
      return serverType === selectedServerType.value
    })
  }

  // 按搜索关键词过滤
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    filtered = filtered.filter(server => {
      const name = server.name || server.server_name || ''
      const description = server.description || server.server_description || ''
      const tools = getServerTools(server)

      return name.toLowerCase().includes(keyword) ||
        description.toLowerCase().includes(keyword) ||
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
  // 尝试多种可能的数据结构
  let tools = []
  
  if (server.tools && Array.isArray(server.tools)) {
    tools = server.tools
  } else if (server.functions && Array.isArray(server.functions)) {
    tools = server.functions
  } else if (server.tools_by_category && typeof server.tools_by_category === 'object') {
    // 如果按分类组织，则展平所有工具
    tools = Object.values(server.tools_by_category).flat()
  } else if (server.server_tools && Array.isArray(server.server_tools)) {
    tools = server.server_tools
  } else if (server.server_functions && Array.isArray(server.server_functions)) {
    tools = server.server_functions
  }
  
  // 确保返回的是数组
  if (!Array.isArray(tools)) {
    console.warn('服务器工具数据不是数组:', server.name || server.server_name, tools)
    tools = []
  }
  
  // 调试信息
  if (tools.length > 0) {
    console.log(`服务器 ${server.name || server.server_name} 有 ${tools.length} 个工具:`, tools.slice(0, 3))
  }
  
  return tools
}

const getToolDisplayName = (tool) => {
  // 尝试多种可能的名称字段
  if (tool.name) {
    return tool.name
  } else if (tool.function_name) {
    return tool.function_name
  } else if (tool.id) {
    return tool.id
  } else if (tool.title) {
    return tool.title
  } else {
    console.warn('工具缺少名称字段:', tool)
    return '未知工具'
  }
}

const refreshAllData = async () => {
  try {
    loading.all = true
    await Promise.all([
      refreshServers(),
      validateConfig()
    ])
  } catch (error) {
    console.error('刷新数据失败:', error)
    message.error('刷新数据失败')
  } finally {
    loading.all = false
  }
}

const refreshServers = async () => {
  try {
    loading.functions = true
    const response = await mcpConfigApi.getServers()
    if (response.success) {
      // 确保数据结构正确
      servers.value = response.data.servers || response.data || {}
      console.log('获取到的服务器数据:', servers.value)
      console.log('服务器数量:', Object.keys(servers.value).length)
      
      // 打印每个服务器的基本信息
      Object.entries(servers.value).forEach(([key, server]) => {
        console.log(`服务器 ${key}:`, {
          name: server.name || server.server_name,
          type: server.type || server.server_type,
          enabled: server.enabled,
          toolsCount: getServerTools(server).length
        })
      })
    }
  } catch (error) {
    console.error('获取服务器列表失败:', error)
    message.error('获取服务器列表失败')
  } finally {
    loading.functions = false
  }
}

const reloadConfig = async () => {
  try {
    loading.reload = true
    const response = await mcpConfigApi.reloadConfig()
    if (response.success) {
      message.success('配置重新加载成功')
      await Promise.all([
        refreshServers(),
        validateConfig()
      ])
    }
  } catch (error) {
    console.error('重新加载配置失败:', error)
    message.error('重新加载配置失败')
  } finally {
    loading.reload = false
  }
}

const validateConfig = async () => {
  try {
    loading.validation = true
    const response = await mcpConfigApi.validateConfig()
    if (response.success) {
      configValid.value = response.data.valid
      validationErrors.value = response.data.errors || []

      if (configValid.value) {
        message.success('配置验证通过')
      } else {
        message.warning(`配置验证失败，发现 ${validationErrors.value.length} 个错误`)
      }
    }
  } catch (error) {
    console.error('验证配置失败:', error)
    message.error('验证配置失败')
  } finally {
    loading.validation = false
  }
}

const viewServerDetail = async (serverName) => {
  try {
    console.log('查看服务器详情:', serverName)
    const response = await mcpConfigApi.getServerDetail(serverName)
    if (response.success) {
      currentServer.value = response.data
      serverDetailVisible.value = true
    }
  } catch (error) {
    console.error('获取服务器详情失败:', error)
    message.error('获取服务器详情失败')
  }
}

const viewFunctions = (server) => {
  currentServerForFunctions.value = server
  functionsDetailVisible.value = true
}

const handleServerTypeChange = () => {
  // 服务器类型改变时会自动触发 filteredServers 计算属性
  console.log('服务器类型改变:', selectedServerType.value)
}

const handleSearch = () => {
  // 搜索处理会自动触发 filteredServers 计算属性
  console.log('搜索关键词:', searchKeyword.value)
}

// 初始化
onMounted(async () => {
  await refreshAllData()
})
</script>

<style lang="less" scoped>
.mcp-config-management {
  .description {
    color: var(--gray-600);
    margin-bottom: 24px;
  }

  .action-bar {
    margin-bottom: 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    
    .stats-info {
      color: var(--gray-600);
      font-size: 0.9em;
      font-weight: 500;
    }
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

    .mcp-server-card {
      height: 100%;
      border: none;
      border-radius: 16px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      background: #ffffff;
      overflow: hidden;

      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.12);
      }

      &.disabled {
        opacity: 0.6;
        cursor: not-allowed;
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        
        &:hover {
          transform: none;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        }
      }

      :deep(.ant-card-head) {
        border-bottom: 1px solid #f1f5f9;
        padding: 16px 20px 12px;
        min-height: auto;
        display: flex;
        align-items: center;
        
        .ant-card-head-title {
          font-size: 16px;
          font-weight: 600;
          color: #1e293b;
          line-height: 1.4;
          flex: 1;
          margin-right: 12px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        
        .ant-card-extra {
          flex-shrink: 0;
          margin-left: auto;
        }
      }

      :deep(.ant-card-body) {
        padding: 0 20px 20px;
      }

      .server-content {
        display: flex;
        flex-direction: column;
        height: 100%;
      }

      .server-description {
        flex-grow: 1;
        margin-bottom: 16px;
        font-size: 14px;
        color: #64748b;
        line-height: 1.5;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }

      .server-functions {
        margin-bottom: 16px;

        h5 {
          margin-bottom: 10px;
          font-size: 13px;
          font-weight: 600;
          color: #475569;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .functions-list {
          .functions-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
          }

          .no-functions {
            font-size: 13px;
            color: #94a3b8;
            font-style: italic;
          }
        }
      }

      .server-actions {
        text-align: right;
        margin-top: auto;
        
        :deep(.ant-btn) {
          border-radius: 8px;
          font-weight: 500;
          height: 32px;
          padding: 0 12px;
          
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
        }
      }
    }
  }
  }

  .tools-section {
    margin-top: 20px;

    h4 {
      margin-bottom: 16px;
      font-size: 16px;
      font-weight: 600;
      color: #1e293b;
    }
  }

  .functions-header {
    margin-bottom: 20px;

    h4 {
      margin-bottom: 8px;
      font-size: 18px;
      font-weight: 600;
      color: #1e293b;
    }

    .server-description {
      color: #64748b;
      margin: 0;
      font-size: 14px;
      line-height: 1.5;
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
  
  // 确保卡片头部标签不会重叠
  :deep(.ant-card-extra) {
    .ant-space {
      flex-wrap: nowrap;
      
      .ant-tag {
        flex-shrink: 0;
        min-width: 0;
      }
    }
  }
</style>