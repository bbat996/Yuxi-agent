<template>
  <div class="">
    <HeaderComponent title="设置" class="setting-header">
      <template #actions>
        <a-button :type="isNeedRestart ? 'primary' : 'default'" @click="sendRestart" :icon="h(ReloadOutlined)">
          {{ isNeedRestart ? '需要刷新' : '重新加载' }}
        </a-button>
      </template>
    </HeaderComponent>
    <div class="setting-container layout-container">
      <div class="sider">
        <a-button type="text" v-if="userStore.isSuperAdmin" :class="{ activesec: state.section === 'base' }"
          @click="state.section = 'base'" :icon="h(SettingOutlined)"> 基本设置 </a-button>
        <a-button type="text" v-if="userStore.isSuperAdmin" :class="{ activesec: state.section === 'model' }"
          @click="state.section = 'model'" :icon="h(CodeOutlined)"> 模型配置 </a-button>
        <a-button type="text" v-if="userStore.isSuperAdmin" :class="{ activesec: state.section === 'mcp-config' }"
          @click="state.section = 'mcp-config'" :icon="h(SettingOutlined)"> MCP配置 </a-button>
        <a-button type="text" :class="{ activesec: state.section === 'user' }" @click="state.section = 'user'"
          :icon="h(UserOutlined)" v-if="userStore.isAdmin"> 用户管理 </a-button>
      </div>
      <div class="setting" v-if="state.section === 'base' && userStore.isSuperAdmin">
        <h3>检索配置</h3>
        <div class="section">
          <div class="card card-select">
            <span class="label">对话模型</span>
            <ModelSelectorComponent @select-model="handleChatModelSelect" :model_name="configStore.config?.model_name"
              :model_provider="configStore.config?.model_provider" />
          </div>
          <div class="card card-select">
            <span class="label">{{ items?.embed_model.des }}</span>
            <a-select style="width: 300px" :value="configStore.config?.embed_model"
              @change="handleChange('embed_model', $event)">
              <a-select-option v-for="(name, idx) in items?.embed_model.choices" :key="idx" :value="name">{{ name }}
              </a-select-option>
            </a-select>
          </div>
          <div class="card card-select">
            <span class="label">{{ items?.reranker.des }}</span>
            <a-select style="width: 300px" :value="configStore.config?.reranker"
              @change="handleChange('reranker', $event)">
              <a-select-option v-for="(name, idx) in items?.reranker.choices" :key="idx" :value="name">{{ name }}
              </a-select-option>
            </a-select>
          </div>
        </div>

        <h3>功能配置</h3>
        <div class="section">
          <div class="card card-select">
            <span class="label">{{ items?.enable_reranker.des }}</span>
            <a-switch :checked="configStore.config?.enable_reranker"
              @change="handleChange('enable_reranker', $event)" />
          </div>
          <div class="card card-select">
            <span class="label">{{ items?.enable_web_search.des }}</span>
            <a-switch :checked="configStore.config?.enable_web_search"
              @change="handleChange('enable_web_search', $event)" />
          </div>
        </div>

        <h3>Web搜索配置</h3>
        <div class="section">
          <div class="card card-select">
            <span class="label">Tavily Base URL</span>
            <a-input style="width: 300px" :value="configStore.config?.tavily_base_url || 'https://api.tavily.com'"
              @change="handleChange('tavily_base_url', $event.target.value)" placeholder="Tavily API基础URL" />
          </div>
          <div class="card card-select">
            <span class="label">Tavily API Key</span>
            <a-input-password style="width: 300px" :value="configStore.config?.tavily_api_key || ''"
              @change="handleChange('tavily_api_key', $event.target.value)" placeholder="请输入Tavily API Key" />
          </div>

        </div>
      </div>
      <div class="setting" v-if="state.section === 'model' && userStore.isSuperAdmin">
        <ModelProvidersComponent :key="'model'" />
      </div>

      <!-- MCP配置管理 -->
      <div class="setting"
        v-if="state.section === 'mcp-config' && userStore.isSuperAdmin">
        <MCPConfigManagement :key="'mcp-config'" />
      </div>

      <!-- 用户管理 -->
      <div class="setting" v-if="state.section === 'user' && userStore.isAdmin">
        <UserManagementComponent :key="'user'" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref, h, onMounted } from 'vue'
import { useConfigStore } from '@/stores/config';
import { useUserStore } from '@/stores/user'
import {
  ReloadOutlined,
  SettingOutlined,
  CodeOutlined,
  UserOutlined
} from '@ant-design/icons-vue';
import HeaderComponent from '@/components/HeaderComponent.vue';
import ModelProvidersComponent from '@/components/model/ModelProvidersComponent.vue';
import UserManagementComponent from '@/components/user/UserManagementComponent.vue';
import MCPConfigManagement from '@/components/mcp_skill/MCPConfigManagement.vue';
import { systemConfigApi } from '@/apis/admin_api'
import ModelSelectorComponent from '@/components/model/ModelSelectorComponent.vue';

const configStore = useConfigStore()
const userStore = useUserStore()
const items = computed(() => configStore.config._config_items)
const isNeedRestart = ref(false)
const state = reactive({
  loading: false,
  section: 'base'
})

const handleModelLocalPathsUpdate = (config) => {
  handleChange('model_local_paths', config)
}

const preHandleChange = (key, e) => {
  if (key == 'enable_reranker'
    || key == 'embed_model'
    || key == 'reranker'
    || key == 'model_local_paths'
    || key == 'enable_web_search'
    || key == 'tavily_api_key'
    || key == 'tavily_base_url') {
    isNeedRestart.value = true
  }
  return true
}

const handleChange = (key, e) => {
  if (!preHandleChange(key, e)) {
    return
  }
  configStore.setConfigValue(key, e)
}

const handleChanges = (items) => {
  for (const key in items) {
    if (!preHandleChange(key, items[key])) {
      return
    }
  }
  configStore.setConfigValues(items)
}



const handleChatModelSelect = ({ provider, name }) => {
  configStore.setConfigValues({
    model_provider: provider,
    model_name: name,
  })
}

onMounted(() => {
  state.section = userStore.isSuperAdmin ? 'base' : (userStore.isAdmin ? 'user' : 'mcp-config')
})

const sendRestart = () => {
  console.log('Restarting...')

  systemConfigApi.restartServer()
    .then(() => {
      console.log('Restarted')
      setTimeout(() => {
        window.location.reload()
      }, 200)
    })
    .catch(error => {
      console.error('重启服务失败:', error)
    });
}
</script>

<style lang="less" scoped>
.setting-container {
  --setting-header-height: 65px;
}

.setting-header {
  height: var(--setting-header-height);
}

.setting-header p {
  margin: 8px 0 0;
}

.setting-container {
  padding: 0;
  box-sizing: border-box;
  display: flex;
  position: relative;
  min-height: calc(100vh - var(--setting-header-height));
}

.sider {
  width: 200px;
  height: 100%;
  padding: 0 20px;
  position: sticky;
  top: var(--setting-header-height);
  display: flex;
  flex-direction: column;
  align-items: center;
  border-right: 1px solid var(--main-light-3);
  gap: 8px;
  padding-top: 20px;

  &>* {
    width: 100%;
    height: auto;
    padding: 6px 16px;
    cursor: pointer;
    transition: all 0.1s;
    text-align: left;
    font-size: 15px;
    border-radius: 8px;
    color: var(--gray-700);

    &:hover {
      background: var(--gray-100);
    }

    &.activesec {
      background: var(--gray-200);
      color: var(--gray-900);
    }
  }
}

.setting {
  width: 100%;
  flex: 1;
  margin: 10px auto;
  height: 100%;
  padding: 0 20px;
  margin-bottom: 40px;

  h3 {
    margin-top: 20px;
  }

  .section {
    margin-top: 20px;
    background-color: var(--gray-10);
    padding: 20px;
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    border: 1px solid var(--gray-300);
  }

  .card {
    display: flex;
    align-items: center;
    justify-content: space-between;

    .label {
      margin-right: 20px;

      button {
        margin-left: 10px;
        height: 24px;
        padding: 0 8px;
        font-size: smaller;
      }
    }
  }
}

@media (max-width: 520px) {
  .setting-container {
    flex-direction: column;
  }

  .card.card-select {
    gap: 0.75rem;
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>