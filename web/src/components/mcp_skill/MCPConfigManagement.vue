<template>
  <div class="mcp-config-management">
    <h3>MCP配置管理</h3>
    <p class="description">管理MCP工具和服务器配置</p>

    <div class="config-overview">
      <div class="section-header">
        <h4>MCP服务器配置</h4>
        <a-space>
          <a-button @click="refreshServers" :loading="loading.servers" :icon="h(ReloadOutlined)">
            刷新配置
          </a-button>
          <a-button @click="reloadConfig" :loading="loading.reload" :icon="h(SyncOutlined)">
            重新加载
          </a-button>
          <a-button @click="validateConfig" :loading="loading.validation" :icon="h(SafetyOutlined)">
            验证配置
          </a-button>
        </a-space>
      </div>

      <!-- 配置状态 -->
      <a-alert
        :message="configValid ? '配置验证通过' : '配置验证失败'"
        :type="configValid ? 'success' : 'error'"
        :description="configValid ? '所有MCP配置项都正常' : `发现 ${validationErrors.length} 个错误`"
        show-icon
        style="margin-bottom: 24px;"
      />

      <!-- MCP服务器卡片 -->
      <a-spin :spinning="loading.servers">
        <a-row :gutter="[16, 16]">
          <a-col v-for="(server, name) in servers" :key="name" :xs="24" :sm="12" :md="8" :lg="6">
            <a-card 
              :title="name" 
              class="mcp-server-card"
              :class="{ 'disabled': !server.enabled }"
            >
              <template #extra>
                <a-tag :color="server.enabled ? 'green' : 'red'">
                  {{ server.enabled ? '启用' : '禁用' }}
                </a-tag>
              </template>
              
              <div class="server-content">
                <div class="server-description">
                  <p>{{ server.description || '无描述' }}</p>
                </div>
                
                <div class="server-methods">
                  <h5>实现方法:</h5>
                  <div class="methods-list">
                    <a-tag v-if="server.type" color="blue">{{ server.type }}</a-tag>
                    <span v-if="server.tools?.length" class="tool-count">
                      {{ server.tools.length }} 个工具
                    </span>
                  </div>
                </div>

                <div class="server-actions">
                  <a-space>
                    <a-button 
                      size="small" 
                      type="primary" 
                      @click="viewServerDetail(name)" 
                      :icon="h(EyeOutlined)"
                    >
                      详情
                    </a-button>

                  </a-space>
                </div>
              </div>
            </a-card>
          </a-col>
        </a-row>
      </a-spin>

      <!-- 统计信息 -->
      <a-card title="配置统计" class="stats-card" style="margin-top: 24px;">
        <a-row :gutter="16">
          <a-col :span="6">
            <a-statistic title="服务器总数" :value="Object.keys(servers).length" />
          </a-col>
          <a-col :span="6">
            <a-statistic title="启用服务器" :value="enabledServersCount" />
          </a-col>
          <a-col :span="6">
            <a-statistic title="总工具数" :value="totalToolsCount" />
          </a-col>
          <a-col :span="6">
            <a-statistic 
              title="配置状态" 
              :value="configValid ? '正常' : '异常'" 
              :value-style="{ color: configValid ? '#52c41a' : '#ff4d4f' }" 
            />
          </a-col>
        </a-row>
      </a-card>
    </div>

    <!-- 服务器详情模态框 -->
    <a-modal
      v-model:open="serverDetailVisible"
      title="服务器详情"
      width="800px"
      :footer="null"
    >
      <div v-if="currentServer">
        <a-descriptions :column="2" bordered>
          <a-descriptions-item label="服务器名称">{{ currentServer.name }}</a-descriptions-item>
          <a-descriptions-item label="类型">{{ currentServer.type }}</a-descriptions-item>
          <a-descriptions-item label="描述">{{ currentServer.description }}</a-descriptions-item>
          <a-descriptions-item label="状态">
            <a-tag :color="currentServer.enabled ? 'green' : 'red'">
              {{ currentServer.enabled ? '启用' : '禁用' }}
            </a-tag>
          </a-descriptions-item>
        </a-descriptions>

        <div v-if="currentServer.tools_by_category" class="tools-section">
          <h4>工具分类:</h4>
          <a-collapse>
            <a-collapse-panel
              v-for="(tools, category) in currentServer.tools_by_category"
              :key="category"
              :header="`${category} (${tools.length})`"
            >
              <a-list
                :data-source="tools"
                size="small"
              >
                <template #renderItem="{ item }">
                  <a-list-item>
                    <a-list-item-meta>
                      <template #title>{{ item.name }}</template>
                      <template #description>{{ item.description }}</template>
                    </a-list-item-meta>
                  </a-list-item>
                </template>
              </a-list>
            </a-collapse-panel>
          </a-collapse>
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
  EyeOutlined
} from '@ant-design/icons-vue'
import { mcpConfigApi } from '@/apis/mcp_api'

// 状态管理
const loading = reactive({
  servers: false,
  validation: false,
  reload: false
})

// 数据状态
const servers = ref({})
const configValid = ref(true)
const validationErrors = ref([])

// 模态框状态
const serverDetailVisible = ref(false)
const currentServer = ref(null)

// 计算属性
const totalToolsCount = computed(() => {
  return Object.values(servers.value).reduce((sum, server) => sum + (server.tools?.length || 0), 0)
})

const enabledServersCount = computed(() => {
  return Object.values(servers.value).filter(server => server.enabled).length
})

// 方法

const refreshServers = async () => {
  try {
    loading.servers = true
    const response = await mcpConfigApi.getServers()
    if (response.success) {
      servers.value = response.data.servers || {}
    }
  } catch (error) {
    console.error('获取服务器列表失败:', error)
    message.error('获取服务器列表失败')
  } finally {
    loading.servers = false
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



// 初始化
onMounted(async () => {
  await Promise.all([
    refreshServers(),
    validateConfig()
  ])
})
</script>

<style lang="less" scoped>
.mcp-config-management {
  .description {
    color: var(--gray-600);
    margin-bottom: 24px;
  }

  .config-overview {
    .section-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      
      h4 {
        margin: 0;
      }
    }

    .stats-card {
      margin-top: 24px;
    }

    .mcp-server-card {
      margin-bottom: 16px;
      border: 1px solid var(--border-color);
      border-radius: 8px;
      overflow: hidden;
      transition: all 0.3s ease;

      &:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
      }

      &.disabled {
        opacity: 0.7;
        cursor: not-allowed;
        background-color: var(--gray-100);
      }

      .server-content {
        display: flex;
        flex-direction: column;
        height: 100%;
      }

      .server-description {
        flex-grow: 1;
        margin-bottom: 12px;
        font-size: 0.9em;
        color: var(--gray-700);
      }

      .server-methods {
        margin-bottom: 12px;
        h5 {
          margin-bottom: 8px;
          font-size: 0.9em;
          color: var(--gray-800);
        }
        .methods-list {
          display: flex;
          align-items: center;
          gap: 8px;
          flex-wrap: wrap;
        }
        .tool-count {
          font-size: 0.9em;
          color: var(--gray-600);
        }
      }

      .server-actions {
        text-align: right;
      }
    }
  }

  .parameters-section {
    margin-top: 16px;
    
    h4 {
      margin-bottom: 12px;
    }
  }

  .tools-section {
    margin-top: 16px;
    
    h4 {
      margin-bottom: 12px;
    }
  }
}
</style> 