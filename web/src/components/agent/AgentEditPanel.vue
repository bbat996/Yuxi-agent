<template>
  <div class="agent-edit-view">
    <div class="left-panel">
      <a-button @click="$emit('back')" style="margin-bottom: 16px;" type="text" shape="circle" title="返回">
        <template #icon>
          <template v-if="$antIcons && $antIcons.ArrowLeftOutlined">
            <ArrowLeftOutlined />
          </template>
          <template v-else>
            <!-- fallback: Unicode arrow if icon not loaded -->
            ←
          </template>
        </template>
      </a-button>
      <a-steps direction="vertical" :current="0" class="edit-steps" progressDot>
        <a-step title="指令">
          <template #description>
            <div class="section">
              <a-form layout="vertical" :model="form" @submit.prevent="onSave">
                <a-form-item label="可引入1项变量（可通过点击添加）：">
                  <a-input v-model:value="form.variable" placeholder="如：$(documents)" suffix="+" />
                </a-form-item>
                <a-form-item label="提示词">
                  <a-textarea v-model:value="form.prompt" :maxlength="30720" :auto-size="{ minRows: 4, maxRows: 8 }" />
                  <div class="prompt-info">{{ form.prompt.length }} / 30720</div>
                </a-form-item>
              </a-form>
            </div>
          </template>
        </a-step>
        <a-step title="知识">
          <template #description>
            <div class="section">
              <div class="section-row">
                <span>知识库</span>
                <a-switch v-model:checked="form.knowledgeEnabled" size="small" style="margin-left: 8px; margin-right: 8px;" />
                <span class="section-action">1/5</span>
                <a-button type="link" size="small">权限</a-button>
                <a-button type="link" size="small">+ 知识库</a-button>
                <a-button type="link" size="small">配置</a-button>
              </div>
              <a-form-item>
                <a-select v-model:value="form.knowledge" mode="multiple" placeholder="选择知识库">
                  <a-select-option v-for="item in knowledgeList" :key="item.id" :value="item.id">{{ item.name }}</a-select-option>
                </a-select>
              </a-form-item>
              <div class="section-row">
                <span>动态文件解析</span>
                <a-switch v-model:checked="form.dynamicFile" size="small" style="margin-left: 8px;" />
              </div>
              <div class="section-row">
                <span>联网搜索</span>
                <a-switch v-model:checked="form.webSearch" size="small" style="margin-left: 8px; margin-right: 8px;" />
                <a-button type="link" size="small">?</a-button>
              </div>
              <div class="section-row">
                <span>样例库</span>
                <a-switch v-model:checked="form.exampleLib" size="small" style="margin-left: 8px;" />
              </div>
            </div>
          </template>
        </a-step>
        <a-step title="技能">
          <template #description>
            <div class="section">
              <div class="section-row">
                <span>MCP服务</span>
                <span class="section-action">1/5</span>
                <a-button type="link" size="small">+ MCP</a-button>
              </div>
              <a-form-item>
                <a-select v-model:value="form.mcp" mode="multiple" placeholder="选择MCP服务">
                  <a-select-option v-for="item in mcpList" :key="item.id" :value="item.id">{{ item.name }}</a-select-option>
                </a-select>
              </a-form-item>
              <div class="section-row">
                <span style="margin-left: 24px;">Amap Maps</span>
                <span class="section-action">工具12</span>
                <a-button type="link" size="small" style="margin-left: 8px;">🗑</a-button>
              </div>
            </div>
          </template>
        </a-step>
      </a-steps>
      <a-form-item style="margin-top: 24px;">
        <a-button type="primary" html-type="submit" :loading="saving">保存</a-button>
      </a-form-item>
    </div>
    <div class="right-panel">
      <SimpleAgentChat :agentId="agentId" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { message } from 'ant-design-vue'
import AgentChatComponent from '@/components/agent/AgentChatComponent.vue'
import SimpleAgentChat from './SimpleAgentChat.vue'
const props = defineProps({ agentId: String })
const form = ref({
  name: '',
  description: '',
  variable: '',
  prompt: '',
  knowledge: [],
  knowledgeEnabled: true,
  dynamicFile: false,
  webSearch: true,
  exampleLib: false,
  mcp: [],
  skills: [],
  visual: false
})
const knowledgeList = ref([])
const mcpList = ref([])
const skillList = ref([])
const saving = ref(false)

watch(() => props.agentId, async (newId) => {
  if (newId) {
    // TODO: 拉取agent详情，填充form
  }
}, { immediate: true })

onMounted(async () => {
  // TODO: 拉取知识库、MCP服务、技能列表
})

const onSave = async () => {
  saving.value = true
  try {
    // TODO: 保存API
    message.success('保存成功')
  } catch (e) {
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.agent-edit-view {
  display: flex;
  height: 100%;
}
.left-panel {
  width: 400px;
  padding-right: 24px;
  padding-top: 12px;
  border-right: 1px solid #eee;
  background: #fafbfc;
  overflow-y: auto;
}
.right-panel {
  flex: 1;
  min-width: 0;
  background: #fff;
}
.edit-steps {
  margin-bottom: 16px;
}
.section {
  margin-bottom: 0;
}
.section-title {
  display: none;
}
.section-row {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
}
.section-action {
  color: #8c8c8c;
  margin-left: 8px;
  font-size: 13px;
}
.prompt-info {
  text-align: right;
  color: #bfbfbf;
  font-size: 12px;
  margin-top: 2px;
}
</style> 