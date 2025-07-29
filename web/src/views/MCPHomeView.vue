<template>
  <div class="mcp-home">
    <header-component
      title="MCP平台"
      description="多组件平台管理，提供各类工具和技能"
    >
      <template #actions>
        <a-button type="primary" @click="refreshServers">
          <template #icon><ReloadOutlined /></template>
          刷新
        </a-button>
      </template>
    </header-component>

    <div class="mcp-container">
      <div class="mcp-sidebar">
        <a-menu
          v-model:selectedKeys="selectedMenu"
          mode="inline"
          :style="{ height: '100%', borderRight: 0 }"
        >
          <a-menu-item key="servers" @click="activeTab = 'servers'">
            <template #icon><ServerOutlined /></template>
            <span>已连接MCP服务</span>
          </a-menu-item>
          <a-menu-item key="built-in" @click="activeTab = 'built-in'">
            <template #icon><AppstoreOutlined /></template>
            <span>内置服务器</span>
          </a-menu-item>
          <a-menu-item key="more" @click="activeTab = 'more'">
            <template #icon><MoreOutlined /></template>
            <span>更多MCP资源</span>
          </a-menu-item>
        </a-menu>
      </div>

      <div class="mcp-content">
        <!-- 服务器列表组件 -->
        <div v-if="activeTab === 'servers'" class="server-section">
          <div class="toolbar">
            <a-input-search
              v-model:value="searchQuery"
              placeholder="搜索服务器..."
              style="width: 200px"
            />
            <a-select
              v-model:value="categoryFilter"
              placeholder="所有分类"
              style="width: 150px"
              @change="filterServers"
            >
              <a-select-option value="">所有分类</a-select-option>
              <a-select-option v-for="category in categories" :key="category" :value="category">
                {{ category }}
              </a-select-option>
            </a-select>
            <a-switch
              v-model:checked="enabledOnly"
              checked-children="已启用"
              un-checked-children="全部"
              @change="filterServers"
            />
          </div>

          <a-spin :spinning="loading">
            <div class="server-grid">
              <mcp-server-card
                v-for="server in filteredServers"
                :key="server.name"
                :server="server"
                @toggle-status="toggleServerStatus"
                @view-detail="viewServerDetail"
              />

              <!-- 添加服务器卡片 -->
              <a-card class="server-card add-card" @click="showAddServerModal">
                <div class="add-server-content">
                  <PlusOutlined />
                  <p>添加服务器</p>
                </div>
              </a-card>
            </div>
          </a-spin>

          <!-- 空状态 -->
          <a-empty v-if="filteredServers.length === 0 && !loading" description="暂无数据" />
        </div>

        <!-- 内置服务器组件 -->
        <div v-if="activeTab === 'built-in'" class="server-section">
          <a-empty description="内置服务器功能待开发" />
        </div>

        <!-- 更多MCP资源组件 -->
        <div v-if="activeTab === 'more'" class="server-section">
          <a-empty description="更多MCP资源功能待开发" />
        </div>
      </div>
    </div>

    <!-- 添加服务器弹窗 -->
    <a-modal
      v-model:visible="addServerModalVisible"
      title="添加MCP服务器"
      @ok="handleAddServer"
      :okText="'添加'"
      :cancelText="'取消'"
      :confirmLoading="addServerLoading"
    >
      <a-form :model="newServer" :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }">
        <a-form-item label="服务器名称" name="name">
          <a-input v-model:value="newServer.name" placeholder="请输入服务器名称" />
        </a-form-item>
        <a-form-item label="URL" name="url">
          <a-input v-model:value="newServer.url" placeholder="请输入服务器URL" />
        </a-form-item>
        <a-form-item label="分类" name="category">
          <a-select
            v-model:value="newServer.category"
            placeholder="请选择分类"
            style="width: 100%"
            show-search
            allow-clear
          >
            <a-select-option v-for="category in categories" :key="category" :value="category">
              {{ category }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="API Key" name="api_key">
          <a-input v-model:value="newServer.api_key" placeholder="请输入API Key（可选）" />
        </a-form-item>
        <a-form-item label="状态" name="enabled">
          <a-switch v-model:checked="newServer.enabled" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import HeaderComponent from '@/components/HeaderComponent.vue'
import MCPServerCard from '@/components/mcp/MCPServerCard.vue'
import {
  ServerOutlined,
  AppstoreOutlined,
  MoreOutlined,
  ReloadOutlined,
  PlusOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'

const router = useRouter()
const loading = ref(false)
const servers = ref([])
const categories = ref([])
const searchQuery = ref('')
const categoryFilter = ref('')
const enabledOnly = ref(false)
const activeTab = ref('servers')
const selectedMenu = ref(['servers'])

// 添加服务器相关状态
const addServerModalVisible = ref(false)
const addServerLoading = ref(false)
const newServer = reactive({
  name: '',
  url: '',
  category: '',
  api_key: '',
  enabled: true
})

// 计算过滤后的服务器列表
const filteredServers = computed(() => {
  let result = servers.value

  // 过滤是否启用
  if (enabledOnly.value) {
    result = result.filter(server => server.enabled)
  }

  // 过滤分类
  if (categoryFilter.value) {
    result = result.filter(server => server.category === categoryFilter.value)
  }

  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(server => 
      server.name.toLowerCase().includes(query) || 
      (server.description && server.description.toLowerCase().includes(query))
    )
  }

  return result
})

// 获取服务器列表
const fetchServers = async () => {
  loading.value = true
  try {
    const response = await fetch('/api/mcp/servers')
    const data = await response.json()
    
    if (data.success) {
      // 转换服务器对象为数组格式以便使用
      const serversData = data.data.servers || {}
      servers.value = Object.entries(serversData).map(([name, config]) => ({
        name,
        ...config
      }))
    } else {
      message.error('获取服务器列表失败')
    }
  } catch (error) {
    console.error('获取服务器列表出错:', error)
    message.error('获取服务器列表出错')
  } finally {
    loading.value = false
  }
}

// 获取所有MCP分类
const fetchCategories = async () => {
  try {
    const response = await fetch('/api/mcp/categories')
    const data = await response.json()
    
    if (data.success) {
      categories.value = data.data || []
    }
  } catch (error) {
    console.error('获取分类列表出错:', error)
  }
}

// 刷新服务器列表
const refreshServers = () => {
  fetchServers()
}

// 切换服务器状态
const toggleServerStatus = async (serverName, enabled) => {
  try {
    const response = await fetch(`/api/mcp/servers/${serverName}/status`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ enabled })
    })
    
    const data = await response.json()
    
    if (data.success) {
      message.success(`服务器已${enabled ? '启用' : '禁用'}`)
      // 更新本地状态
      const serverIndex = servers.value.findIndex(s => s.name === serverName)
      if (serverIndex !== -1) {
        servers.value[serverIndex].enabled = enabled
      }
    } else {
      message.error(`切换服务器状态失败: ${data.message || '未知错误'}`)
    }
  } catch (error) {
    console.error('切换服务器状态出错:', error)
    message.error('切换服务器状态出错')
  }
}

// 查看服务器详情
const viewServerDetail = (serverName) => {
  router.push(`/mcp/servers/${serverName}`)
}

// 显示添加服务器弹窗
const showAddServerModal = () => {
  // 重置表单
  Object.assign(newServer, {
    name: '',
    url: '',
    category: '',
    api_key: '',
    enabled: true
  })
  addServerModalVisible.value = true
}

// 添加服务器
const handleAddServer = async () => {
  // 表单验证
  if (!newServer.name || !newServer.url) {
    message.error('服务器名称和URL不能为空')
    return
  }

  addServerLoading.value = true
  try {
    const response = await fetch('/api/mcp/servers', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(newServer)
    })
    
    const data = await response.json()
    
    if (data.success) {
      message.success('添加服务器成功')
      addServerModalVisible.value = false
      // 重新获取服务器列表
      fetchServers()
    } else {
      message.error(`添加服务器失败: ${data.message || '未知错误'}`)
    }
  } catch (error) {
    console.error('添加服务器出错:', error)
    message.error('添加服务器出错')
  } finally {
    addServerLoading.value = false
  }
}

// 过滤服务器
const filterServers = () => {
  // 通过计算属性自动过滤
}

// 初始化
onMounted(() => {
  fetchServers()
  fetchCategories()
})
</script>

<style scoped lang="less">
.mcp-home {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.mcp-container {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.mcp-sidebar {
  width: 250px;
  border-right: 1px solid #f0f0f0;
  background-color: #fff;
  height: 100%;
  overflow-y: auto;
}

.mcp-content {
  flex: 1;
  padding: 20px;
  background-color: #f5f5f5;
  overflow-y: auto;
}

.server-section {
  .toolbar {
    margin-bottom: 20px;
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
  }

  .server-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 20px;
  }

  .server-card {
    height: 280px;
    display: flex;
    flex-direction: column;

    &.enabled {
      border-color: #52c41a;
    }

    &.disabled {
      opacity: 0.7;
    }

    &.add-card {
      border: 1px dashed #d9d9d9;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      height: 280px;

      &:hover {
        border-color: #1890ff;
        color: #1890ff;
      }

      .add-server-content {
        text-align: center;
        font-size: 24px;
        color: #999;

        p {
          margin-top: 8px;
          font-size: 14px;
        }
      }
    }

    .server-icon {
      height: 100px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 48px;
      background-color: #f5f5f5;
    }

    .card-actions {
      margin-top: auto;
      display: flex;
      justify-content: flex-end;
      padding-top: 12px;
    }
  }
}
</style>
