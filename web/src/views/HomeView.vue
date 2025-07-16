<template>
  <div class="home-container">
    <header class="glass-header">
      <div class="logo">
        <img src="/avatar.png" alt="Logo" class="logo-img" />
        <span>{{ configStore.siteName }}</span>
      </div>
    </header>

    <!-- 原理流程展示区（移到最上方） -->
    <section class="react-section">
      <div class="section-header">
        <h2>智能体原理</h2>
        <div class="divider"></div>
        <p class="react-desc">推理（Reasoning）与行动（Acting）结合，驱动智能体高效完成复杂任务</p>
      </div>
      <div class="react-flow">
        <div class="react-step">
          <div class="step-icon">📝</div>
          <div class="step-title">用户提问</div>
          <div class="step-desc">输入问题或需求</div>
        </div>
        <div class="react-arrow">→</div>
        <div class="react-step">
          <div class="step-icon">💡</div>
          <div class="step-title">推理</div>
          <div class="step-desc">智能体分析问题，生成思路</div>
        </div>
        <div class="react-arrow">→</div>
        <div class="react-step">
          <div class="step-icon">🛠️</div>
          <div class="step-title">行动</div>
          <div class="step-desc">调用工具/知识库/外部API</div>
        </div>
        <div class="react-arrow">→</div>
        <div class="react-step">
          <div class="step-icon">🔄</div>
          <div class="step-title">反馈</div>
          <div class="step-desc">获取结果，继续推理与行动</div>
        </div>
        <div class="react-arrow">→</div>
        <div class="react-step">
          <div class="step-icon">✅</div>
          <div class="step-title">输出答案</div>
          <div class="step-desc">最终输出高质量答案</div>
        </div>
      </div>
    </section>

    <!-- MCP工具调用原理流程展示区 -->
    <div class="mcp-flow-header">
      <span class="mcp-title">MCP工具调用原理</span>
      <div class="divider small"></div>
    </div>
    <div class="mcp-flow">
      <div class="mcp-step">
        <div class="mcp-icon">🤔</div>
        <div class="mcp-label">识别需求</div>
        <div class="mcp-desc">智能体判断需调用外部工具</div>
      </div>
      <div class="mcp-arrow">→</div>
      <div class="mcp-step">
        <div class="mcp-icon">🧩</div>
        <div class="mcp-label">选择MCP</div>
        <div class="mcp-desc">匹配合适的MCP工具</div>
      </div>
      <div class="mcp-arrow">→</div>
      <div class="mcp-step">
        <div class="mcp-icon">📤</div>
        <div class="mcp-label">发送请求</div>
        <div class="mcp-desc">带参数调用MCP</div>
      </div>
      <div class="mcp-arrow">→</div>
      <div class="mcp-step">
        <div class="mcp-icon">📥</div>
        <div class="mcp-label">获取结果</div>
        <div class="mcp-desc">MCP返回处理结果</div>
      </div>
      <div class="mcp-arrow">→</div>
      <div class="mcp-step">
        <div class="mcp-icon">🔁</div>
        <div class="mcp-label">继续推理</div>
        <div class="mcp-desc">智能体利用结果继续推理</div>
      </div>
    </div>

    <!-- 平台智能能力卡片区 -->
    <div class="ability-header">
      <span class="ability-title">平台智能能力</span>
      <div class="divider small"></div>
    </div>
    <div class="ability-grid">
      <div class="ability-card">
        <div class="ability-icon">📂</div>
        <div class="ability-title">读取文件</div>
        <div class="ability-desc">智能体可自动读取本地或云端文件，提取关键信息。</div>
      </div>
      <div class="ability-card">
        <div class="ability-icon">🔍</div>
        <div class="ability-title">RAG</div>
        <div class="ability-desc">检索增强生成，结合外部知识库，提升答案准确性。</div>
      </div>
      <div class="ability-card">
        <div class="ability-icon">💻</div>
        <div class="ability-title">编写执行代码</div>
        <div class="ability-desc">自动生成并运行代码，完成复杂任务。</div>
      </div>
      <div class="ability-card">
        <div class="ability-icon">🌐</div>
        <div class="ability-title">浏览器操作</div>
        <div class="ability-desc">自动打开网页，抓取和分析互联网信息。</div>
      </div>
    </div>

    <section class="hero-section">
      <div class="hero-content">
        <h1 class="title">{{ configStore.siteName }}</h1>
        <p class="subtitle">{{ configStore.siteDescription }}</p>
        
        <div class="cta-container">
          <button class="start-button" @click="goToChat">开始体验</button>
        </div>
      </div>
    </section>

    <footer>
      <p>© {{ configStore.siteName }} 2025 [WIP] v0.12.138</p>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useConfigStore } from '@/stores/config'
import { chatApi } from '@/apis/auth_api'

const router = useRouter()
const userStore = useUserStore()
const configStore = useConfigStore()

const goToChat = async () => {
  // 检查用户是否登录
  if (!userStore.isLoggedIn) {
    // 登录后跳转到智能体页面
    sessionStorage.setItem('redirect', '/');  // 设置为首页，登录后会通过路由守卫处理重定向
    router.push('/login');
    return;
  }

  // 根据用户角色进行跳转
  if (userStore.isAdmin) {
    // 管理员用户跳转到聊天页面
    router.push('/agent');
    return;
  }

  // 普通用户跳转到第一个可用智能体
  try {
    // 获取智能体列表选择第一个
    const agentData = await chatApi.getAgents();
    if (agentData.agents && agentData.agents.length > 0) {
      router.push(`/agent/${agentData.agents[0].name}`);
    } else {
      // 没有可用智能体，回退到chat页面
      router.push("/agent");
    }
  } catch (error) {
    console.error('跳转到智能体页面失败:', error);
    router.push("/agent");
  }
};
</script>

<style lang="less" scoped>
.home-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  color: #e0e0e0;
  background-color: #121212;
  background-image: 
    radial-gradient(circle at 25% 25%, rgba(40, 40, 40, 0.2) 0%, transparent 50%),
    radial-gradient(circle at 75% 75%, rgba(40, 40, 40, 0.2) 0%, transparent 50%);
  padding-top: 4.5rem;
}

/* 添加RGB变量，用于透明度调整 */
:root {
  --main-color-rgb: 24, 144, 255; /* #1890ff 对应的RGB值 */
}

.glass-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 1.2rem 2rem;
  background-color: rgba(18, 18, 18, 0.8);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
}

.logo {
  display: flex;
  align-items: center;
  font-size: 1.3rem;
  font-weight: bold;
  color: #ffffff;

  .logo-img {
    height: 2.8rem;
    margin-right: 1rem;
    border-radius: 0.5rem;
    box-shadow: 0 0 12px #1890ff55;
  }
}

.hero-section {
  min-height: 60vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  padding: 0 2rem;
  position: relative;
  overflow: hidden;
  
  &::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: radial-gradient(circle at center, rgba(24, 144, 255, 0.15) 0%, transparent 70%);
    z-index: -1;
  }
}

.hero-content {
  max-width: 800px;
}

.title {
  font-size: 4.5rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
  background: linear-gradient(45deg, #ffffff, #a0a0a0);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

.subtitle {
  font-size: 1.6rem;
  font-weight: 400;
  margin-bottom: 3rem;
  color: #b0b0b0;
  line-height: 1.5;
  max-width: 700px;
  margin-left: auto;
  margin-right: auto;
}

.cta-container {
  margin-top: 2rem;
}

.start-button {
  padding: 1.2rem 3.5rem;
  font-size: 1.2rem;
  font-weight: 600;
  color: #121212;
  background: linear-gradient(135deg, #1890ff, #40a9ff);
  border: none;
  border-radius: 3rem;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(24, 144, 255, 0.3);

  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 7px 20px rgba(24, 144, 255, 0.4);
    filter: brightness(1.1);
  }

  &:active {
    transform: translateY(-1px);
  }
}

.section-header {
  text-align: center;
  margin-bottom: 3rem;
  
  h2 {
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 1rem;
    background: linear-gradient(45deg, #ffffff, #a0a0a0);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
  }
  
  .divider {
    width: 80px;
    height: 4px;
    background: linear-gradient(90deg, transparent, #1890ff, transparent);
    margin: 0 auto;
  }
}

.features-section {
  padding: 6rem 2rem;
  background-color: #161616;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2.5rem;
  max-width: 1200px;
  margin: 0 auto;
}

.feature-card {
  background-color: rgba(30, 30, 30, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 1rem;
  padding: 2.5rem;
  transition: all 0.3s ease;
  text-align: center;
  
  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
    border-color: rgba(24, 144, 255, 0.3);
  }
  
  .feature-icon {
    font-size: 3rem;
    margin-bottom: 1.5rem;
  }
  
  h3 {
    font-size: 1.5rem;
    margin-bottom: 1rem;
    color: #ffffff;
  }
  
  p {
    color: #b0b0b0;
    line-height: 1.6;
  }
}

.preview-section {
  padding: 6rem 2rem;
  background-color: #121212;
}

.preview-container {
  position: relative;
  max-width: 1000px;
  margin: 0 auto;
  overflow: hidden;
  border-radius: 1rem;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);

    .preview-overlay {
      opacity: 1;
    }
    
    img {
      transform: scale(1.02);
    }
  }

  img {
    width: 100%;
    height: auto;
    display: block;
    transition: transform 0.5s ease;
  }

  .preview-overlay {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    background: linear-gradient(to top, rgba(0, 0, 0, 0.9), transparent);
    padding: 3rem 2rem;
    opacity: 0.8;
    transition: opacity 0.3s ease;

    .overlay-content {
      color: white;

      h3 {
        font-size: 1.8rem;
        margin-bottom: 0.8rem;
      }

      p {
        font-size: 1.1rem;
        opacity: 0.9;
        max-width: 600px;
      }
    }
  }
}

footer {
  margin-top: auto;
  text-align: center;
  padding: 2rem;
  color: #999;
  font-size: 0.9rem;
  background-color: #0a0a0a;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

/* ReAct 原理流程区样式 */
.react-section {
  padding: 2.5rem 2rem 3rem 2rem;
  background: linear-gradient(120deg, #10131a 80%, #181c2a 100%);
  box-shadow: 0 8px 32px 0 rgba(24, 144, 255, 0.08);
  position: relative;
  z-index: 1;
  margin-bottom: -2rem;
}

.react-desc {
  color: #7ecfff;
  font-size: 1.1rem;
  margin-top: 0.5rem;
  margin-bottom: 2.5rem;
  letter-spacing: 0.5px;
}

.react-flow {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1.5rem;
  flex-wrap: wrap;
  position: relative;
  z-index: 2;
}

.react-step {
  background: rgba(24, 144, 255, 0.10);
  border: 1.5px solid rgba(24, 144, 255, 0.25);
  border-radius: 1.2rem;
  box-shadow: 0 2px 16px 0 rgba(24, 144, 255, 0.10);
  padding: 2rem 1.5rem 1.5rem 1.5rem;
  min-width: 140px;
  max-width: 180px;
  text-align: center;
  transition: box-shadow 0.3s, transform 0.3s;
  position: relative;
  color: #e0f7ff;
  backdrop-filter: blur(2px);
  margin-bottom: 1rem;
  flex: 1 1 160px;
  
  &:hover {
    box-shadow: 0 6px 32px 0 rgba(24, 144, 255, 0.18);
    transform: translateY(-4px) scale(1.04);
    border-color: #40a9ff;
  }
  .step-icon {
    font-size: 2.2rem;
    margin-bottom: 0.7rem;
    filter: drop-shadow(0 0 8px #1890ff88);
  }
  .step-title {
    font-size: 1.15rem;
    font-weight: 600;
    margin-bottom: 0.3rem;
    color: #fff;
    letter-spacing: 0.5px;
  }
  .step-desc {
    font-size: 0.98rem;
    color: #b0e0ff;
    opacity: 0.92;
  }
}

.react-arrow {
  font-size: 2.2rem;
  color: #40a9ff;
  text-shadow: 0 0 8px #1890ff88;
  margin: 0 0.2rem;
  user-select: none;
}

/* MCP工具调用原理流程区样式 */
.mcp-flow-header {
  text-align: center;
  margin: 2.5rem 0 1.2rem 0;
}
.mcp-title {
  font-size: 1.35rem;
  font-weight: 600;
  color: #40a9ff;
  letter-spacing: 1px;
}
.divider.small {
  width: 48px;
  height: 3px;
  background: linear-gradient(90deg, transparent, #40a9ff, transparent);
  margin: 0.5rem auto 0 auto;
}
.mcp-flow {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1.1rem;
  flex-wrap: wrap;
  margin-bottom: 2.5rem;
}
.mcp-step {
  background: rgba(64, 169, 255, 0.13);
  border: 1.2px solid rgba(64, 169, 255, 0.22);
  border-radius: 1rem;
  box-shadow: 0 2px 12px 0 rgba(64, 169, 255, 0.10);
  padding: 1.2rem 1.1rem 1rem 1.1rem;
  min-width: 110px;
  max-width: 140px;
  text-align: center;
  color: #e0f7ff;
  transition: box-shadow 0.3s, transform 0.3s;
  flex: 1 1 120px;
  margin-bottom: 0.5rem;
  backdrop-filter: blur(1.5px);
  &:hover {
    box-shadow: 0 4px 18px 0 #40a9ff55;
    border-color: #1890ff;
    transform: translateY(-3px) scale(1.03);
  }
  .mcp-icon {
    font-size: 1.7rem;
    margin-bottom: 0.5rem;
    filter: drop-shadow(0 0 6px #40a9ff88);
  }
  .mcp-label {
    font-size: 1.05rem;
    font-weight: 600;
    color: #fff;
    margin-bottom: 0.2rem;
  }
  .mcp-desc {
    font-size: 0.92rem;
    color: #b0e0ff;
    opacity: 0.92;
  }
}
.mcp-arrow {
  font-size: 1.5rem;
  color: #40a9ff;
  text-shadow: 0 0 6px #40a9ff88;
  margin: 0 0.1rem;
  user-select: none;
}

/* 平台智能能力卡片区样式 */
.ability-header {
  text-align: center;
  margin: 2.5rem 0 1.2rem 0;
}
.ability-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #7ecfff;
  letter-spacing: 1px;
}
.ability-grid {
  display: flex;
  align-items: stretch;
  justify-content: center;
  gap: 1.5rem;
  flex-wrap: wrap;
  margin-bottom: 2.5rem;
}
.ability-card {
  background: rgba(24, 144, 255, 0.09);
  border: 1.2px solid rgba(24, 144, 255, 0.18);
  border-radius: 1rem;
  box-shadow: 0 2px 12px 0 rgba(24, 144, 255, 0.08);
  padding: 1.5rem 1.2rem 1.2rem 1.2rem;
  min-width: 140px;
  max-width: 200px;
  text-align: center;
  color: #e0f7ff;
  transition: box-shadow 0.3s, transform 0.3s;
  flex: 1 1 160px;
  margin-bottom: 0.5rem;
  backdrop-filter: blur(1.5px);
  &:hover {
    box-shadow: 0 4px 18px 0 #1890ff55;
    border-color: #40a9ff;
    transform: translateY(-3px) scale(1.03);
  }
  .ability-icon {
    font-size: 2rem;
    margin-bottom: 0.6rem;
    filter: drop-shadow(0 0 8px #1890ff88);
  }
  .ability-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #fff;
    margin-bottom: 0.2rem;
  }
  .ability-desc {
    font-size: 0.95rem;
    color: #b0e0ff;
    opacity: 0.92;
  }
}

@media (max-width: 900px) {
  .react-flow {
    flex-wrap: wrap;
    gap: 0.7rem;
  }
  .react-step {
    min-width: 120px;
    max-width: 150px;
    padding: 1.2rem 0.7rem 1rem 0.7rem;
  }
  .react-arrow {
    font-size: 1.5rem;
  }
}

@media (max-width: 768px) {
  .glass-header {
    padding: 1rem;
  }

  .logo {
    font-size: 1.1rem;
    
    .logo-img {
      height: 1.6rem;
    }
  }

  .title {
    font-size: 2.8rem;
  }

  .subtitle {
    font-size: 1.2rem;
  }

  .start-button {
    padding: 1rem 2.5rem;
    font-size: 1.1rem;
  }
  
  .section-header h2 {
    font-size: 2rem;
  }
  
  .features-grid {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
  
  .feature-card {
    padding: 2rem;
  }

  .preview-section, .features-section {
    padding: 4rem 1rem;
  }
}
</style>
