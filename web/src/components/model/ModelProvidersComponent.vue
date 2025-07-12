<template>
  <div class="model-providers-container">
    <!-- 左侧：厂商列表 -->
    <div class="providers-sidebar">
      <!-- 自定义模型区域 -->
      <div class="provider-item custom-models-section" :class="{ active: selectedProvider === 'custom' }">
        <div class="provider-header" @click="selectProvider('custom')">
          <div class="provider-info">
            <div class="provider-icon custom-icon">
              <span>自</span>
            </div>
            <div class="provider-details">
              <h3>自定义模型</h3>
              <span class="provider-status"
                >{{ (configStore.config.custom_models || []).length }} 个模型</span
              >
            </div>
          </div>
          <div class="provider-actions">
            <a-button type="text" size="small" @click.stop="prepareToAddCustomModel">
              <template #icon><EditOutlined /></template>
            </a-button>
          </div>
        </div>
      </div>

      <!-- 已配置的模型提供商 -->
      <div
        v-for="item in modelKeys"
        :key="item"
        class="provider-item configured-provider"
        :class="{ active: selectedProvider === item }"
        @click="selectProvider(item)"
      >
        <div class="provider-header">
          <div class="provider-info">
            <div class="provider-icon available">
              <img :src="modelIcons[item] || modelIcons.default" alt="模型图标" />
            </div>
            <div class="provider-details">
              <h3>{{ modelNames[item].name }}</h3>
              <span class="provider-status"
                >{{ (modelNames[item].models || []).length }} 个模型</span
              >
            </div>
          </div>
          <div class="provider-actions">
            <a-button type="text" size="small" @click.stop="openProviderConfig(item)">
              <template #icon><SettingOutlined /></template>
            </a-button>
          </div>
        </div>
      </div>

      <!-- 未配置的模型提供商 -->
      <div
        v-for="item in notModelKeys"
        :key="item"
        class="provider-item unconfigured-provider"
        :class="{ active: selectedProvider === item }"
        @click="selectProvider(item)"
      >
        <div class="provider-header">
          <div class="provider-info">
            <div class="provider-icon">
              <img :src="modelIcons[item] || modelIcons.default" alt="模型图标" />
            </div>
            <div class="provider-details">
              <h3>{{ modelNames[item].name }}</h3>
              <div class="missing-keys">
                需配置
                <span v-for="(envKey, idx) in modelNames[item].env" :key="idx">{{ envKey }}</span>
              </div>
            </div>
          </div>
          <div class="provider-actions">
            <a-button type="text" size="small" @click.stop="openProviderConfig(item)">
              <template #icon><SettingOutlined /></template>
            </a-button>
            <a :href="modelNames[item].url" target="_blank" class="info-link">
              <InfoCircleOutlined />
            </a>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧：模型详情 -->
    <div class="models-content">
      <div v-if="!selectedProvider" class="empty-state">
        <div class="empty-icon">🤖</div>
        <h3>选择模型提供商</h3>
        <p>从左侧列表中选择一个模型提供商来查看其模型列表和配置</p>
      </div>

      <!-- 自定义模型详情 -->
      <div v-else-if="selectedProvider === 'custom'" class="custom-models-content">
        <div class="content-header">
          <h2>自定义模型</h2>
          <a-button type="primary" @click="prepareToAddCustomModel">
            <template #icon><EditOutlined /></template>
            添加模型
          </a-button>
        </div>
        <div class="models-grid">
          <div
            v-for="item in configStore.config.custom_models"
            :key="item.custom_id"
            class="model-card custom-model-card"
          >
            <div class="model-header">
              <div class="model-name" :title="item.name">{{ item.name }}</div>
              <div class="model-actions">
                <a-button type="text" size="small" @click="prepareToEditCustomModel(item)">
                  <template #icon><EditOutlined /></template>
                </a-button>
                <a-popconfirm
                  title="确认删除该模型?"
                  @confirm="handleDeleteCustomModel(item.custom_id)"
                  okText="确认删除"
                  cancelText="取消"
                  ok-type="danger"
                >
                  <a-button type="text" size="small" danger>
                    <template #icon><DeleteOutlined /></template>
                  </a-button>
                </a-popconfirm>
              </div>
            </div>
            <div class="model-info">
              <div class="info-item">
                <span class="label">API Base:</span>
                <span class="value">{{ item.api_base }}</span>
              </div>
              <div class="info-item" v-if="item.api_key">
                <span class="label">API Key:</span>
                <span class="value">••••••••</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 厂商模型详情 -->
      <div v-else class="provider-models-content">
        <div class="content-header">
          <div class="header-info">
            <div class="provider-icon">
              <img :src="modelIcons[selectedProvider] || modelIcons.default" alt="模型图标" />
            </div>
            <div>
              <h2>{{ modelNames[selectedProvider]?.name }}</h2>
              <p class="provider-description">
                {{ modelStatus[selectedProvider] ? '已配置' : '未配置' }} ·
                {{ (modelNames[selectedProvider]?.models || []).length }} 个模型
              </p>
            </div>
          </div>
          <div class="header-actions">
            <a-button type="primary" @click="openProviderConfig(selectedProvider)">
              <template #icon><SettingOutlined /></template>
              配置模型
            </a-button>
          </div>
        </div>

        <div v-if="modelStatus[selectedProvider]" class="models-grid">
          <div
            v-for="(model, idx) in modelNames[selectedProvider]?.models"
            :key="idx"
            class="model-card provider-model-card"
          >
            <div class="model-name">{{ model }}</div>
            <div class="model-status">可用</div>
          </div>
        </div>

        <div v-else class="unconfigured-state">
          <div class="warning-icon">⚠️</div>
          <h3>模型提供商未配置</h3>
          <p>请配置以下环境变量后重启服务：</p>
          <div class="env-keys">
            <code v-for="(envKey, idx) in modelNames[selectedProvider]?.env" :key="idx">{{
              envKey
            }}</code>
          </div>
          <a-button type="primary" @click="openProviderConfig(selectedProvider)">
            立即配置
          </a-button>
        </div>
      </div>
    </div>

    <!-- 添加和编辑自定义模型的弹窗 -->
    <a-modal
      class="custom-model-modal"
      :open="customModel.visible"
      :title="customModel.modelTitle"
      @ok="handleAddOrEditCustomModel"
      @cancel="handleCancelCustomModel"
      @update:open="(val) => customModel.visible = val"
      :okText="'确认'"
      :cancelText="'取消'"
      :okButtonProps="{ disabled: !customModel.name || !customModel.api_base }"
      :ok-type="'primary'"
    >
      <p>添加的模型是兼容 OpenAI 的模型，比如 vllm，Ollama。</p>
      <a-form :model="customModel" layout="vertical">
        <a-form-item label="模型ID" v-if="customModel.edit_type == 'edit'" name="custom_id">
          <p class="form-item-description">调用的模型的ID</p>
          <a-input :value="customModel.custom_id" @update:value="(val) => customModel.custom_id = val" disabled />
        </a-form-item>
        <a-form-item
          label="模型名称"
          name="name"
          :rules="[{ required: true, message: '请输入模型名称' }]"
        >
          <p class="form-item-description">调用的模型的名称</p>
          <a-input :value="customModel.name" @update:value="(val) => customModel.name = val" :disabled="customModel.edit_type == 'edit'" />
        </a-form-item>
        <a-form-item
          label="API Base"
          name="api_base"
          :rules="[{ required: true, message: '请输入API Base' }]"
        >
          <p class="form-item-description">比如 <code>http://localhost:11434/v1</code></p>
          <a-input :value="customModel.api_base" @update:value="(val) => customModel.api_base = val" />
        </a-form-item>
        <a-form-item label="API KEY" name="api_key">
          <a-input-password
            :value="customModel.api_key"
            @update:value="(val) => customModel.api_key = val"
            :visibilityToggle="true"
            autocomplete="new-password"
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 模型提供商配置弹窗 -->
    <a-modal
      class="provider-config-modal"
      :open="providerConfig.visible"
      :title="`配置${providerConfig.providerName}模型`"
      @ok="saveProviderConfig"
      @cancel="cancelProviderConfig"
      @update:open="(val) => providerConfig.visible = val"
      :okText="'保存配置'"
      :cancelText="'取消'"
      :ok-type="'primary'"
      :width="800"
    >
      <div v-if="providerConfig.loading" class="modal-loading-container">
        <a-spin
          :indicator="
            h(LoadingOutlined, { style: { fontSize: '32px', color: 'var(--main-color)' } })
          "
        />
        <div class="loading-text">正在获取模型列表...</div>
      </div>
      <div v-else class="modal-config-content">
        <div class="modal-config-header">
          <h3>选择 {{ providerConfig.providerName }} 的模型</h3>
          <p class="description">
            勾选您希望在系统中启用的模型，请注意，列表中可能包含非对话模型，请仔细甄别。
          </p>
        </div>

        <div class="modal-models-section">
          <div class="model-search">
            <a-input :value="providerConfig.searchQuery" @update:value="(val) => providerConfig.searchQuery = val" placeholder="搜索模型..." allow-clear>
              <template #prefix>
                <SearchOutlined />
              </template>
            </a-input>
          </div>

          <!-- 显示选中统计信息 -->
          <div class="selection-summary">
            <span>已选择 {{ providerConfig.selectedModels.length }} 个模型</span>
            <span v-if="providerConfig.searchQuery" class="filter-info">
              （当前筛选显示 {{ filteredModels.length }} 个）
            </span>
          </div>

          <div class="modal-checkbox-list">
            <div v-for="(model, index) in filteredModels" :key="index" class="modal-checkbox-item">
              <a-checkbox
                :checked="providerConfig.selectedModels.includes(model.id)"
                @change="(e) => handleModelSelect(model.id, e.target.checked)"
              >
                {{ model.id }}
              </a-checkbox>
            </div>
          </div>
          <div v-if="providerConfig.allModels.length === 0" class="modal-no-models">
            <a-alert
              v-if="!modelStatus[providerConfig.provider]"
              type="warning"
              message="请在 src/.env 中配置对应的 APIKEY，并重新启动服务"
            />
            <div v-else>
              <a-alert
                type="warning"
                message="该提供商暂未适配获取模型列表的方法，如果需要添加模型，请在 config/models.private.yml 中添加。"
              />
              <img
                src="../../assets/pics/guides/how-to-add-models.png"
                alt="添加模型指引"
                style="width: 100%; height: 100%"
              />
            </div>
          </div>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { computed, reactive, watch, h, ref } from 'vue'
import { message } from 'ant-design-vue'
import {
  DeleteOutlined,
  EditOutlined,
  InfoCircleOutlined,
  SettingOutlined,
  DownCircleOutlined,
  LoadingOutlined,
  SearchOutlined
} from '@ant-design/icons-vue'
import { useConfigStore } from '@/stores/config'
import { modelIcons } from '@/utils/modelIcon'
import { chatApi } from '@/apis/auth_api'

const configStore = useConfigStore()

// 选中的提供商
const selectedProvider = ref(null)

// 计算属性
const modelNames = computed(() => configStore.config?.model_names)
const modelStatus = computed(() => configStore.config?.model_provider_status)

// 自定义模型相关状态
const customModel = reactive({
  modelTitle: '添加自定义模型',
  visible: false,
  custom_id: '',
  name: '',
  api_key: '',
  api_base: '',
  edit_type: 'add'
})

// 提供商配置相关状态
const providerConfig = reactive({
  visible: false,
  provider: '',
  providerName: '',
  models: [],
  allModels: [], // 所有可用的模型
  selectedModels: [], // 用户选择的模型
  loading: false,
  searchQuery: ''
})

// 筛选 modelStatus 中为真的key
const modelKeys = computed(() => {
  return Object.keys(modelStatus.value || {}).filter((key) => modelStatus.value[key])
})

// 筛选 modelStatus 中为假的key
const notModelKeys = computed(() => {
  return Object.keys(modelStatus.value || {}).filter((key) => !modelStatus.value[key])
})

// 模型展开状态管理
const expandedModels = reactive({})

// 监听 modelKeys 变化，确保新添加的模型也是默认展开状态
watch(
  modelKeys,
  (newKeys) => {
    newKeys.forEach((key) => {
      if (expandedModels[key] === undefined) {
        expandedModels[key] = true
      }
    })
    
    // 如果没有选中的提供商，自动选择第一个可用的
    if (!selectedProvider.value) {
      if (configStore.config.custom_models && configStore.config.custom_models.length > 0) {
        selectedProvider.value = 'custom'
      } else if (newKeys.length > 0) {
        selectedProvider.value = newKeys[0]
      } else if (notModelKeys.value.length > 0) {
        selectedProvider.value = notModelKeys.value[0]
      }
    }
  },
  { immediate: true }
)

// 选择提供商
const selectProvider = (provider) => {
  selectedProvider.value = provider
}

// 生成随机哈希值
const generateRandomHash = (length) => {
  let chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
  let hash = ''
  for (let i = 0; i < length; i++) {
    hash += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return hash
}

// 处理自定义模型删除
const handleDeleteCustomModel = (customId) => {
  const updatedModels = configStore.config.custom_models.filter(
    (item) => item.custom_id !== customId
  )
  configStore.setConfigValue('custom_models', updatedModels)
}

// 准备编辑自定义模型
const prepareToEditCustomModel = (item) => {
  customModel.modelTitle = '编辑自定义模型'
  customModel.custom_id = item.custom_id
  customModel.visible = true
  customModel.edit_type = 'edit'
  customModel.name = item.name
  customModel.api_key = item.api_key
  customModel.api_base = item.api_base
}

// 准备添加自定义模型
const prepareToAddCustomModel = () => {
  customModel.modelTitle = '添加自定义模型'
  customModel.edit_type = 'add'
  customModel.visible = true
  clearCustomModel()
}

// 清除自定义模型表单
const clearCustomModel = () => {
  customModel.custom_id = ''
  customModel.name = ''
  customModel.api_key = ''
  customModel.api_base = ''
}

// 取消自定义模型添加/编辑
const handleCancelCustomModel = () => {
  clearCustomModel()
  customModel.visible = false
}

// 添加或编辑自定义模型
const handleAddOrEditCustomModel = async () => {
  if (!customModel.name || !customModel.api_base) {
    message.error('请填写完整的模型名称和API Base信息。')
    return
  }

  let custom_models = configStore.config.custom_models || []

  const model_info = {
    custom_id: customModel.custom_id || `${customModel.name}-${generateRandomHash(4)}`,
    name: customModel.name,
    api_key: customModel.api_key,
    api_base: customModel.api_base
  }

  if (customModel.edit_type === 'add') {
    if (custom_models.find((item) => item.custom_id === customModel.custom_id)) {
      message.error('模型ID已存在')
      return
    }
    custom_models.push(model_info)
  } else {
    // 如果 custom_id 相同，则更新
    custom_models = custom_models.map((item) =>
      item.custom_id === customModel.custom_id ? model_info : item
    )
  }

  customModel.visible = false
  await configStore.setConfigValue('custom_models', custom_models)
  message.success(customModel.edit_type === 'add' ? '模型添加成功' : '模型修改成功')
}

// 切换展开状态
const toggleExpand = (item) => {
  expandedModels[item] = !expandedModels[item]
}

// 处理模型选择
const handleModelSelect = (modelId, checked) => {
  const selectedModels = providerConfig.selectedModels
  const index = selectedModels.indexOf(modelId)

  if (checked && index === -1) {
    selectedModels.push(modelId)
  } else if (!checked && index > -1) {
    selectedModels.splice(index, 1)
  }
}

// 打开提供商配置
const openProviderConfig = (provider) => {
  providerConfig.provider = provider
  providerConfig.providerName = modelNames.value[provider].name
  providerConfig.allModels = []
  providerConfig.visible = true
  providerConfig.loading = true
  providerConfig.searchQuery = '' // 重置搜索关键词

  // 获取当前选择的模型作为初始选中值
  const currentModels = modelNames.value[provider]?.models || []
  providerConfig.selectedModels = [...currentModels]

  // 获取所有可用模型
  fetchProviderModels(provider)
}

// 获取模型提供商的模型列表
const fetchProviderModels = (provider) => {
  providerConfig.loading = true
  chatApi
    .getProviderModels(provider)
    .then((data) => {
      console.log(`${provider} 模型列表:`, data)

      // 处理各种可能的API返回格式
      let modelsList = []

      // 情况1: { data: [...] }
      if (data.data && Array.isArray(data.data)) {
        modelsList = data.data
      }
      // 情况2: { models: [...] } (字符串数组)
      else if (data.models && Array.isArray(data.models)) {
        modelsList = data.models.map((model) => (typeof model === 'string' ? { id: model } : model))
      }
      // 情况3: { models: { data: [...] } }
      else if (data.models && data.models.data && Array.isArray(data.models.data)) {
        modelsList = data.models.data
      }

      console.log('处理后的模型列表:', modelsList)
      providerConfig.allModels = modelsList
      providerConfig.loading = false
    })
    .catch((error) => {
      console.error(`获取${provider}模型列表失败:`, error)
      message.error({ content: `获取${modelNames.value[provider].name}模型列表失败`, duration: 2 })
      providerConfig.loading = false
    })
}

// 保存提供商配置
const saveProviderConfig = async () => {
  if (!modelStatus.value[providerConfig.provider]) {
    message.error('请在 src/.env 中配置对应的 APIKEY，并重新启动服务')
    return
  }

  message.loading({ content: '保存配置中...', key: 'save-config', duration: 0 })

  try {
    // 发送选择的模型列表到后端
    const data = await chatApi.updateProviderModels(
      providerConfig.provider,
      providerConfig.selectedModels
    )
    console.log('更新后的模型列表:', data.models)

    message.success({ content: '模型配置已保存!', key: 'save-config', duration: 2 })

    // 关闭弹窗
    providerConfig.visible = false

    // 刷新配置
    configStore.refreshConfig()
  } catch (error) {
    console.error('保存配置失败:', error)
    message.error({ content: '保存配置失败: ' + error.message, key: 'save-config', duration: 2 })
  }
}

// 取消提供商配置
const cancelProviderConfig = () => {
  providerConfig.visible = false
}

// 计算筛选后的模型列表
const filteredModels = computed(() => {
  const allModels = providerConfig.allModels || []
  const searchQuery = providerConfig.searchQuery.toLowerCase()
  return allModels.filter((model) => model.id.toLowerCase().includes(searchQuery))
})
</script>

<style lang="less" scoped>
.model-providers-container {
  display: flex;
  height: 100%;
  gap: 24px;
  background: #f8f9fa;
  border-radius: 8px;
  overflow: hidden;
}

// 左侧厂商列表
.providers-sidebar {
  width: 280px;
  flex-shrink: 0;
  background: white;
  border-right: 1px solid var(--gray-200);
  padding: 16px;
  overflow-y: auto;

  .provider-item {
    border: 1px solid var(--gray-200);
    border-radius: 8px;
    margin-bottom: 8px;
    cursor: pointer;
    transition: all 0.2s ease;
    overflow: hidden;

    &:hover {
      border-color: var(--gray-300);
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }

    &.active {
      border-color: var(--main-color);
      box-shadow: 0 0 0 1px var(--main-color);
    }

    &.custom-models-section {
      .provider-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;

        .provider-details h3 {
          color: white;
        }

        .provider-status {
          color: rgba(255, 255, 255, 0.8);
        }

        .custom-icon {
          background: rgba(255, 255, 255, 0.2);
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: bold;
        }
      }
    }

    &.configured-provider {
      .provider-icon.available {
        filter: none;
      }
    }

    &.unconfigured-provider {
      .provider-header {
        background: #f8f9fa;
      }

      .provider-icon {
        filter: grayscale(100%);
        opacity: 0.6;
      }

      .provider-details h3 {
        color: var(--gray-600);
      }
    }

    .provider-header {
      padding: 12px;
      display: flex;
      align-items: center;
      gap: 12px;
      background: white;

      .provider-info {
        flex: 1;
        display: flex;
        align-items: center;
        gap: 12px;
        min-width: 0;

        .provider-icon {
          width: 36px;
          height: 36px;
          border-radius: 8px;
          overflow: hidden;
          border: 1px solid var(--gray-200);
          filter: grayscale(100%);
          transition: filter 0.2s ease;

          img {
            width: 100%;
            height: 100%;
            object-fit: cover;
          }

          &.available {
            filter: none;
          }
        }

        .provider-details {
          flex: 1;
          min-width: 0;

          h3 {
            margin: 0;
            font-size: 14px;
            font-weight: 600;
            color: var(--gray-900);
            line-height: 1.2;
          }

          .provider-status {
            font-size: 12px;
            color: var(--gray-500);
            line-height: 1.2;
          }

          .missing-keys {
            font-size: 11px;
            color: var(--gray-600);
            margin-top: 2px;

            span {
              background: #fff7ed;
              color: #d97706;
              padding: 1px 4px;
              border-radius: 3px;
              margin-left: 4px;
              font-family: monospace;
            }
          }
        }
      }

      .provider-actions {
        display: flex;
        align-items: center;
        gap: 4px;

        .info-link {
          color: var(--gray-500);
          font-size: 14px;
          padding: 4px;
          border-radius: 4px;
          transition: all 0.2s ease;

          &:hover {
            color: var(--main-color);
            background: var(--gray-100);
          }
        }
      }
    }
  }
}

// 右侧内容区域
.models-content {
  flex: 1;
  background: white;
  border-radius: 8px;
  padding: 24px;
  overflow-y: auto;

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    text-align: center;
    color: var(--gray-500);

    .empty-icon {
      font-size: 48px;
      margin-bottom: 16px;
    }

    h3 {
      margin: 0 0 8px 0;
      color: var(--gray-700);
    }

    p {
      margin: 0;
      font-size: 14px;
    }
  }

  .content-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--gray-200);

    .header-info {
      display: flex;
      align-items: center;
      gap: 16px;

      .provider-icon {
        width: 48px;
        height: 48px;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid var(--gray-200);

        img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
      }

      h2 {
        margin: 0;
        font-size: 24px;
        font-weight: 600;
        color: var(--gray-900);
      }

      .provider-description {
        margin: 4px 0 0 0;
        font-size: 14px;
        color: var(--gray-600);
      }
    }
  }

  .models-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px;

    .model-card {
      border: 1px solid var(--gray-200);
      border-radius: 8px;
      padding: 16px;
      background: white;
      transition: all 0.2s ease;

      &:hover {
        border-color: var(--gray-300);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
      }

      &.custom-model-card {
        .model-header {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          margin-bottom: 12px;

          .model-name {
            font-size: 16px;
            font-weight: 600;
            color: var(--gray-900);
            flex: 1;
            margin-right: 8px;
          }

          .model-actions {
            display: flex;
            gap: 4px;
            opacity: 0;
            transition: opacity 0.2s ease;
          }
        }

        &:hover .model-actions {
          opacity: 1;
        }

        .model-info {
          .info-item {
            display: flex;
            margin-bottom: 8px;
            font-size: 13px;

            .label {
              color: var(--gray-600);
              margin-right: 8px;
              min-width: 70px;
            }

            .value {
              color: var(--gray-900);
              word-break: break-all;
              flex: 1;
            }
          }
        }
      }

      &.provider-model-card {
        display: flex;
        align-items: center;
        justify-content: space-between;

        .model-name {
          font-size: 14px;
          font-weight: 500;
          color: var(--gray-900);
        }

        .model-status {
          font-size: 12px;
          color: #059669;
          background: #d1fae5;
          padding: 2px 8px;
          border-radius: 12px;
        }
      }
    }
  }

  .unconfigured-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 48px 24px;
    color: var(--gray-600);

    .warning-icon {
      font-size: 48px;
      margin-bottom: 16px;
    }

    h3 {
      margin: 0 0 8px 0;
      color: var(--gray-700);
    }

    p {
      margin: 0 0 16px 0;
      font-size: 14px;
    }

    .env-keys {
      display: flex;
      gap: 8px;
      margin-bottom: 24px;
      flex-wrap: wrap;
      justify-content: center;

      code {
        background: #f3f4f6;
        padding: 4px 8px;
        border-radius: 4px;
        font-family: monospace;
        font-size: 12px;
        color: var(--gray-700);
        border: 1px solid var(--gray-300);
      }
    }
  }
}

// 弹窗样式保持不变
.custom-model-modal {
  .ant-form-item {
    margin-bottom: 10px;
    .form-item-description {
      font-size: 12px;
      color: var(--gray-600);
      margin-bottom: 10px;
    }
  }
}

.provider-config-modal {
  .ant-modal-body {
    padding: 16px 0 !important;
    .modal-loading-container {
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      height: 200px;

      .loading-text {
        margin-top: 20px;
        color: var(--gray-700);
        font-size: 14px;
      }
    }

    .modal-config-content {
      max-height: 70vh;
      overflow-y: auto;

      .modal-config-header {
        margin-bottom: 20px;

        .description {
          font-size: 14px;
          color: var(--gray-600);
          margin: 0;
        }
      }

      .modal-models-section {
        .model-search {
          margin-bottom: 10px;
          padding: 0 6px;

          .ant-input-affix-wrapper {
            border-radius: 6px;
            &:hover,
            &:focus {
              border-color: var(--main-color);
            }
            .anticon {
              color: var(--gray-500);
            }
          }
        }
        .selection-summary {
          margin: 0 6px 10px;
          font-size: 14px;
          color: var(--gray-600);

          .filter-info {
            color: var(--gray-500);
          }
        }
        .modal-checkbox-list {
          max-height: 50vh;
          overflow-y: auto;
          .modal-checkbox-item {
            display: inline-block;
            margin-bottom: 4px;
            padding: 4px 6px;
            border-radius: 6px;
            background-color: white;
            border: 1px solid var(--gray-200);

            &:hover {
              background-color: var(--gray-50);
            }
          }
        }
      }
    }
  }
}

// 响应式调整
@media (max-width: 1024px) {
  .model-providers-container {
    flex-direction: column;
    height: auto;

    .providers-sidebar {
      width: 100%;
      max-height: 300px;
    }

    .models-content {
      padding: 16px;

      .models-grid {
        grid-template-columns: 1fr;
      }
    }
  }
}

@media (max-width: 768px) {
  .providers-sidebar {
    padding: 12px;

    .provider-item .provider-header {
      padding: 8px;
      gap: 8px;

      .provider-info .provider-icon {
        width: 32px;
        height: 32px;
      }

      .provider-details h3 {
        font-size: 13px;
      }
    }
  }

  .models-content {
    padding: 12px;

    .content-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 16px;

      .header-info .provider-icon {
        width: 40px;
        height: 40px;
      }

      h2 {
        font-size: 20px;
      }
    }
  }
}
</style>