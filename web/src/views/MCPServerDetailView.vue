<template>
  <div class="mcp-server-detail">
    <header-component
      :title="serverName"
      description="服务器详细信息与配置"
      :showBackButton="true"
      @back="goBack"
    >
      <template #actions>
        <a-space>
          <a-button type="primary" @click="saveServerConfig" :loading="saving">
            保存配置
          </a-button>
          <a-button @click="refreshServerData">
            <template #icon><ReloadOutlined /></template>
            刷新
          </a-button>
        </a-space>
      </template>
    </header-component>

    <div class="server-detail-container">
      <a-spin :spinning="loading">
        <a-tabs v-model:activeKey="activeTabKey">
          <!-- 基本信息标签页 -->
          <a-tab-pane key="basic" tab="基本信息">
            <a-form
              :model="serverConfig"
              :label-col="{ span: 4 }"
              :wrapper-col="{ span: 14 }"
              layout="horizontal"
            >
              <a-form-item label="服务器名称">
                <a-input v-model:value="serverConfig.name" disabled />
              </a-form-item>
              <a-form-item label="服务器URL">
                <a-input v-model:value="serverConfig.url" />
              </a-form-item>
              <a-form-item label="分类">
                <a-select
                  v-model:value="serverConfig.category"
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
              <a-form-item label="版本">
                <a-input v-model:value="serverConfig.version" />
              </a-form-item>
              <a-form-item label="API Key">
                <a-input-password v-model:value="serverConfig.api_key" />
              </a-form-item>
              <a-form-item label="状态">
                <a-switch v-model:checked="serverConfig.enabled" />
              </a-form-item>
              <a-form-item label="描述">
                <a-textarea v-model:value="serverConfig.description" rows="4" />
              </a-form-item>
            </a-form>
          </a-tab-pane>

          <!-- 工具列表标签页 -->
          <a-tab-pane key="tools" tab="工具列表">
            <div class="tools-container">
              <div class="tools-header">
                <a-input-search
                  v-model:value="toolSearchQuery"
                  placeholder="搜索工具..."
                  style="width: 200px"
                  @search="filterTools"
                />
                <a-select
                  v-model:value="toolCategoryFilter"
                  placeholder="所有分类"
                  style="width: 180px"
                  @change="filterTools"
                >
                  <a-select-option value="">所有分类</a-select-option>
                  <a-select-option v-for="category in toolCategories" :key="category" :value="category">
                    {{ category }}
                  </a-select-option>
                </a-select>
              </div>

              <a-table
                :dataSource="filteredTools"
                :columns="toolColumns"
                :pagination="{ pageSize: 10 }"
                :rowKey="record => record.id"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.dataIndex === 'enabled'">
                    <a-switch
                      :checked="record.enabled"
                      @change="(checked) => toggleToolStatus(record.id, checked)"
                    />
                  </template>
                  <template v-if="column.dataIndex === 'action'">
                    <a-button type="link" @click="viewToolDetail(record)">查看</a-button>
                  </template>
                </template>
              </a-table>
            </div>
          </a-tab-pane>

          <!-- YAML配置标签页 -->
          <a-tab-pane key="yaml" tab="YAML配置">
            <div class="yaml-editor">
              <a-alert
                type="warning"
                message="警告：直接编辑YAML配置可能导致配置错误。请确保你了解YAML格式及配置结构。"
                show-icon
                banner
                style="margin-bottom: 20px"
              />
              <a-textarea
                v-model:value="yamlConfig"
                :rows="20"
                :spellcheck="false"
                class="yaml-textarea"
              />
              <div class="yaml-actions">
                <a-space>
                  <a-button type="primary" @click="validateAndSaveYaml" :loading="yamlSaving">
                    验证并保存
                  </a-button>
                  <a-button @click="resetYaml">
                    重置
                  </a-button>
                </a-space>
              </div>
            </div>
          </a-tab-pane>

          <!-- 测试连接标签页 -->
          <a-tab-pane key="test" tab="测试连接">
            <div class="test-connection">
              <a-card title="服务器连接测试" :bordered="false">
                <a-button
                  type="primary"
                  @click="testServerConnection"
                  :loading="testingConnection"
                >
                  测试连接
                </a-button>
                
                <a-divider />
                
                <a-timeline v-if="connectionResults.length > 0">
                  <a-timeline-item
                    v-for="(result, index) in connectionResults"
                    :key="index"
                    :color="result.success ? 'green' : 'red'"
                  >
                    <p><strong>{{ result.timestamp }}</strong></p>
                    <p>状态: {{ result.success ? '成功' : '失败' }}</p>
                    <p>响应时间: {{ result.responseTime }}ms</p>
                    <p v-if="result.message">{{ result.message }}</p>
                  </a-timeline-item>
                </a-timeline>
                
                <a-empty v-else description="暂无测试记录" />
              </a-card>
            </div>
          </a-tab-pane>

          <!-- 工具函数测试标签页 -->
          <a-tab-pane key="tool-test" tab="工具函数测试">
            <mcp-tool-tester 
              :serverName="serverName"
              :tools="tools"
            />
          </a-tab-pane>
        </a-tabs>
      </a-spin>
    </div>

    <!-- 工具详情抽屉 -->
    <a-drawer
      :title="selectedTool?.name || '工具详情'"
      :visible="toolDrawerVisible"
      @close="toolDrawerVisible = false"
      width="600"
    >
      <template v-if="selectedTool">
        <a-descriptions bordered>
          <a-descriptions-item label="ID" :span="3">{{ selectedTool.id }}</a-descriptions-item>
          <a-descriptions-item label="名称" :span="3">{{ selectedTool.name }}</a-descriptions-item>
          <a-descriptions-item label="分类" :span="3">{{ selectedTool.category }}</a-descriptions-item>
          <a-descriptions-item label="状态" :span="3">
            <a-tag :color="selectedTool.enabled ? 'green' : 'red'">
              {{ selectedTool.enabled ? '启用' : '禁用' }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="描述" :span="3">{{ selectedTool.description }}</a-descriptions-item>
        </a-descriptions>

        <a-divider />

        <h3>参数列表</h3>
        <a-table
          v-if="selectedTool.parameters && selectedTool.parameters.length > 0"
          :dataSource="selectedTool.parameters"
          :columns="paramColumns"
          :pagination="false"
          :rowKey="record => record.name"
        ></a-table>
        <a-empty v-else description="无参数" />
      </template>
    </a-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import MCPToolTester from '@/components/mcp/MCPToolTester.vue';
import { useRoute, useRouter } from 'vue-router';
import HeaderComponent from '@/components/HeaderComponent.vue';
import { ReloadOutlined } from '@ant-design/icons-vue';
import { message } from 'ant-design-vue';
import * as yaml from 'js-yaml';

const route = useRoute();
const router = useRouter();
const serverName = ref(route.params.server_name);
const loading = ref(true);
const saving = ref(false);
const yamlSaving = ref(false);
const testingConnection = ref(false);
const activeTabKey = ref('basic');

// 服务器配置
const serverConfig = reactive({
  name: serverName.value,
  url: '',
  category: '',
  version: '',
  api_key: '',
  enabled: true,
  description: ''
});

// YAML配置
const yamlConfig = ref('');
const originalYamlConfig = ref('');

// 分类列表
const categories = ref([]);

// 工具相关
const tools = ref([]);
const toolCategories = ref([]);
const toolSearchQuery = ref('');
const toolCategoryFilter = ref('');
const toolDrawerVisible = ref(false);
const selectedTool = ref(null);

// 测试连接结果
const connectionResults = ref([]);

// 工具表格列定义
const toolColumns = [
  {
    title: '名称',
    dataIndex: 'name',
    key: 'name',
  },
  {
    title: '分类',
    dataIndex: 'category',
    key: 'category',
  },
  {
    title: '描述',
    dataIndex: 'description',
    key: 'description',
    ellipsis: true,
  },
  {
    title: '启用状态',
    dataIndex: 'enabled',
    key: 'enabled',
    width: 100,
  },
  {
    title: '操作',
    dataIndex: 'action',
    key: 'action',
    width: 100,
  },
];

// 参数表格列定义
const paramColumns = [
  {
    title: '参数名',
    dataIndex: 'name',
    key: 'name',
  },
  {
    title: '类型',
    dataIndex: 'type',
    key: 'type',
  },
  {
    title: '必填',
    dataIndex: 'required',
    key: 'required',
    render: (text) => (text ? '是' : '否'),
  },
  {
    title: '描述',
    dataIndex: 'description',
    key: 'description',
    ellipsis: true,
  },
];

// 过滤后的工具列表
const filteredTools = computed(() => {
  let result = tools.value;
  
  if (toolCategoryFilter.value) {
    result = result.filter(tool => tool.category === toolCategoryFilter.value);
  }
  
  if (toolSearchQuery.value) {
    const query = toolSearchQuery.value.toLowerCase();
    result = result.filter(tool => 
      tool.name.toLowerCase().includes(query) || 
      tool.description.toLowerCase().includes(query)
    );
  }
  
  return result;
});

// 返回上一页
const goBack = () => {
  router.push('/mcp');
};

// 刷新服务器数据
const refreshServerData = async () => {
  fetchServerConfig();
  fetchServerTools();
};

// 获取服务器配置
const fetchServerConfig = async () => {
  loading.value = true;
  try {
    const response = await fetch(`/api/mcp/servers/${serverName.value}`);
    const data = await response.json();
    
    if (data.success) {
      const config = data.data;
      Object.assign(serverConfig, config);
      
      // 同时更新YAML配置
      updateYamlFromConfig(config);
    } else {
      message.error(`获取服务器配置失败: ${data.message || '未知错误'}`);
    }
  } catch (error) {
    console.error('获取服务器配置出错:', error);
    message.error('获取服务器配置出错');
  } finally {
    loading.value = false;
  }
};

// 获取服务器工具列表
const fetchServerTools = async () => {
  try {
    const response = await fetch(`/api/mcp/servers/${serverName.value}/tools`);
    const data = await response.json();
    
    if (data.success) {
      tools.value = data.data.tools || [];
      
      // 提取工具分类
      const categories = new Set();
      tools.value.forEach(tool => {
        if (tool.category) {
          categories.add(tool.category);
        }
      });
      toolCategories.value = Array.from(categories);
    } else {
      message.error(`获取工具列表失败: ${data.message || '未知错误'}`);
    }
  } catch (error) {
    console.error('获取工具列表出错:', error);
    message.error('获取工具列表出错');
  }
};

// 获取所有MCP分类
const fetchCategories = async () => {
  try {
    const response = await fetch('/api/mcp/categories');
    const data = await response.json();
    
    if (data.success) {
      categories.value = data.data || [];
    }
  } catch (error) {
    console.error('获取分类列表出错:', error);
  }
};

// 保存服务器配置
const saveServerConfig = async () => {
  saving.value = true;
  try {
    const response = await fetch(`/api/mcp/servers/${serverName.value}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(serverConfig)
    });
    
    const data = await response.json();
    
    if (data.success) {
      message.success('服务器配置已保存');
      // 更新YAML配置
      updateYamlFromConfig(serverConfig);
    } else {
      message.error(`保存失败: ${data.message || '未知错误'}`);
    }
  } catch (error) {
    console.error('保存服务器配置出错:', error);
    message.error('保存服务器配置出错');
  } finally {
    saving.value = false;
  }
};

// 切换工具状态
const toggleToolStatus = async (toolId, enabled) => {
  try {
    const response = await fetch(`/api/mcp/servers/${serverName.value}/tools/${toolId}/status`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ enabled })
    });
    
    const data = await response.json();
    
    if (data.success) {
      message.success(`工具已${enabled ? '启用' : '禁用'}`);
      
      // 更新本地工具状态
      const toolIndex = tools.value.findIndex(t => t.id === toolId);
      if (toolIndex !== -1) {
        tools.value[toolIndex].enabled = enabled;
      }
      
      // 如果当前选中的工具就是被修改的工具，也更新它
      if (selectedTool.value && selectedTool.value.id === toolId) {
        selectedTool.value.enabled = enabled;
      }
    } else {
      message.error(`切换工具状态失败: ${data.message || '未知错误'}`);
    }
  } catch (error) {
    console.error('切换工具状态出错:', error);
    message.error('切换工具状态出错');
  }
};

// 查看工具详情
const viewToolDetail = (tool) => {
  selectedTool.value = { ...tool };
  toolDrawerVisible.value = true;
};

// 过滤工具
const filterTools = () => {
  // 通过计算属性自动过滤
};

// 从配置更新YAML
const updateYamlFromConfig = (config) => {
  try {
    const yamlString = yaml.dump(config, {
      indent: 2,
      lineWidth: 100,
      noRefs: true,
      sortKeys: true
    });
    yamlConfig.value = yamlString;
    originalYamlConfig.value = yamlString;
  } catch (error) {
    console.error('转换YAML出错:', error);
    message.error('转换YAML配置出错');
  }
};

// 验证并保存YAML配置
const validateAndSaveYaml = async () => {
  yamlSaving.value = true;
  try {
    // 尝试解析YAML
    const config = yaml.load(yamlConfig.value);
    
    // 更新服务器配置
    Object.assign(serverConfig, config);
    
    // 保存配置
    const response = await fetch(`/api/mcp/servers/${serverName.value}/config`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ config: yamlConfig.value })
    });
    
    const data = await response.json();
    
    if (data.success) {
      message.success('YAML配置已保存');
      // 重新获取服务器配置和工具列表
      refreshServerData();
    } else {
      message.error(`保存YAML配置失败: ${data.message || '未知错误'}`);
    }
  } catch (error) {
    console.error('验证或保存YAML配置出错:', error);
    message.error(`YAML格式错误: ${error.message}`);
  } finally {
    yamlSaving.value = false;
  }
};

// 重置YAML配置
const resetYaml = () => {
  yamlConfig.value = originalYamlConfig.value;
  message.info('YAML配置已重置');
};

// 测试服务器连接
const testServerConnection = async () => {
  testingConnection.value = true;
  try {
    const startTime = Date.now();
    const response = await fetch(`/api/mcp/servers/${serverName.value}/test`, {
      method: 'POST'
    });
    const responseTime = Date.now() - startTime;
    
    const data = await response.json();
    
    const result = {
      timestamp: new Date().toLocaleTimeString(),
      success: data.success,
      responseTime,
      message: data.message || (data.success ? '连接成功' : '连接失败')
    };
    
    // 添加到测试结果列表
    connectionResults.value = [result, ...connectionResults.value];
    
    if (data.success) {
      message.success('服务器连接测试成功');
    } else {
      message.error(`服务器连接测试失败: ${data.message || '未知错误'}`);
    }
  } catch (error) {
    console.error('测试服务器连接出错:', error);
    
    const result = {
      timestamp: new Date().toLocaleTimeString(),
      success: false,
      responseTime: 0,
      message: `测试出错: ${error.message}`
    };
    
    connectionResults.value = [result, ...connectionResults.value];
    message.error('测试服务器连接出错');
  } finally {
    testingConnection.value = false;
  }
};

// 初始化
onMounted(() => {
  fetchServerConfig();
  fetchServerTools();
  fetchCategories();
});
</script>

<style scoped lang="less">
.mcp-server-detail {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.server-detail-container {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  background-color: #f5f5f5;
}

.tools-container {
  .tools-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 16px;
  }
}

.yaml-editor {
  .yaml-textarea {
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'source-code-pro', monospace;
    font-size: 14px;
  }
  
  .yaml-actions {
    margin-top: 16px;
    display: flex;
    justify-content: flex-end;
  }
}

.test-connection {
  max-width: 800px;
}
</style>
