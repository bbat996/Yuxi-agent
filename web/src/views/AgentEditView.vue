<template>
  <div class="agent-edit-view layout-container">
    <!-- 页面头部 -->
    <HeaderComponent 
      title="编辑智能体" 
      description="配置智能体的指令、知识和技能"
      :loading="loading"
    />

    <div class="edit-container">
      <!-- 左侧配置区域 -->
      <div class="left-panel">
        <div class="config-header">
          <div class="header-left">
            <a-button @click="goBack" type="text" shape="circle" title="返回">
              <template #icon>
                <ArrowLeftOutlined />
              </template>
            </a-button>
            <h3>智能体配置</h3>
          </div>
          <div class="header-right">
            <a-button type="primary" :loading="saving" @click="onSave">保存配置</a-button>
          </div>
        </div>
        
        <div class="config-content">
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
        </div>
      </div>

      <!-- 右侧对话区域 -->
      <div class="right-panel">
        <div class="chat-header">
          <h3>对话测试</h3>
          <p>在这里测试智能体的对话能力</p>
        </div>
        <div class="chat-content">
          <SimpleAgentChat 
            :agent-id="agentId" 
            :config="{}"
            :state="{}"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { ArrowLeftOutlined } from '@ant-design/icons-vue'
import SimpleAgentChat from '@/components/agent/SimpleAgentChat.vue'
import HeaderComponent from '@/components/HeaderComponent.vue'

const route = useRoute()
const router = useRouter()

// 从路由参数获取agentId
const agentId = ref(route.params.agent_id)
const loading = ref(false)

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

const knowledgeList = ref([
  { id: 'kb1', name: '产品知识库' },
  { id: 'kb2', name: '技术文档库' },
  { id: 'kb3', name: '常见问题库' }
])
const mcpList = ref([
  { id: 'mcp1', name: 'Amap Maps' },
  { id: 'mcp2', name: 'Weather Service' },
  { id: 'mcp3', name: 'Calculator' }
])
const skillList = ref([
  { id: 'skill1', name: '数据分析' },
  { id: 'skill2', name: '文档生成' },
  { id: 'skill3', name: '代码审查' }
])
const saving = ref(false)

// 返回上一页
const goBack = () => {
  router.back()
}

// 加载智能体数据
const loadAgentData = async () => {
  if (!agentId.value) return
  
  try {
    loading.value = true
    // TODO: 拉取agent详情，填充form
    // const response = await getAgentDetail(agentId.value)
    // if (response.success) {
    //   form.value = { ...form.value, ...response.data }
    // }
    
    // 模拟数据填充
    form.value = {
      name: '智能助手',
      description: '一个多功能的AI助手',
      variable: '$(documents)',
      prompt: '你是一个智能助手，可以帮助用户解决各种问题。请根据用户的问题提供准确、有用的回答。',
      knowledge: ['kb1', 'kb2'],
      knowledgeEnabled: true,
      dynamicFile: false,
      webSearch: true,
      exampleLib: false,
      mcp: ['mcp1'],
      skills: ['skill1'],
      visual: false
    }
  } catch (error) {
    console.error('加载智能体数据失败:', error)
    message.error('加载智能体数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadAgentData()
  // TODO: 拉取知识库、MCP服务、技能列表
  // try {
  //   const [knowledgeResponse, mcpResponse, skillResponse] = await Promise.all([
  //     getKnowledgeList(),
  //     getMCPList(),
  //     getSkillList()
  //   ])
  //   
  //   if (knowledgeResponse.success) {
  //     knowledgeList.value = knowledgeResponse.data
  //   }
  //   if (mcpResponse.success) {
  //     mcpList.value = mcpResponse.data
  //   }
  //   if (skillResponse.success) {
  //     skillList.value = skillResponse.data
  //   }
  // } catch (error) {
  //   console.error('加载配置数据失败:', error)
  // }
})

const onSave = async () => {
  saving.value = true
  try {
    // TODO: 保存API
    // const response = await saveAgent(agentId.value, form.value)
    // if (response.success) {
    //   message.success('保存成功')
    // } else {
    //   message.error(response.message || '保存失败')
    // }
    message.success('保存成功')
  } catch (e) {
    console.error('保存失败:', e)
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<style lang="less" scoped>
.agent-edit-view {
  padding: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.edit-container {
  display: flex;
  flex: 1;
  min-height: 0;
}

.left-panel {
  width: 50%;
  border-right: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
  background: #fafbfc;
}

.config-header {
  padding: 16px 24px;
  border-bottom: 1px solid #f0f0f0;
  background: white;
  display: flex;
  align-items: center;
  justify-content: space-between;

  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;

    h3 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      color: #262626;
    }
  }

  .header-right {
    display: flex;
    align-items: center;
  }
}

.config-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.right-panel {
  width: 50%;
  display: flex;
  flex-direction: column;
  background: white;
}

.chat-header {
  padding: 16px 24px;
  border-bottom: 1px solid #f0f0f0;
  background: white;

  h3 {
    margin: 0 0 4px 0;
    font-size: 16px;
    font-weight: 600;
    color: #262626;
  }

  p {
    margin: 0;
    font-size: 14px;
    color: #8c8c8c;
  }
}

.chat-content {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  
  :deep(.chat-container) {
    height: 100%;
  }
  
  :deep(.chat) {
    height: 100%;
    overflow: hidden;
  }
  
  :deep(.chat-box) {
    flex: 1;
    overflow-y: auto;
  }
  
  :deep(.bottom) {
    position: sticky;
    bottom: 0;
    background: white;
    border-top: 1px solid #f0f0f0;
  }
}

.edit-steps {
  margin-bottom: 24px;
}

.section {
  margin-bottom: 16px;
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



/* 响应式设计 */
@media (max-width: 1200px) {
  .left-panel,
  .right-panel {
    width: 50%;
  }
}

@media (max-width: 768px) {
  .edit-container {
    flex-direction: column;
  }
  
  .left-panel,
  .right-panel {
    width: 100%;
  }
  
  .left-panel {
    height: 50vh;
  }
  
  .right-panel {
    height: 50vh;
  }
}
</style> 