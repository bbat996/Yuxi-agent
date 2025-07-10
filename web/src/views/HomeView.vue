<template>
  <div class="home-container">
    <header class="glass-header">
      <div class="logo">
        <img :src="configStore.siteLogo" :alt="configStore.siteName" class="logo-img" />
        <span>{{ configStore.siteName }}</span>
      </div>
    </header>

    <section class="hero-section">
      <div class="hero-content">
        <h1 class="title">{{ configStore.siteName }}</h1>
        <p class="subtitle">{{ configStore.siteDescription }}</p>
        
        <div class="cta-container">
          <button class="start-button" @click="goToChat">开始体验</button>
        </div>
      </div>
    </section>

    <section class="features-section">
      <div class="section-header">
        <h2>核心功能</h2>
        <div class="divider"></div>
      </div>
      
      <div class="features-grid">
        <div class="feature-card">
          <div class="feature-icon">📚</div>
          <h3>灵活知识库</h3>
          <p>轻松导入和管理各类知识资源，支持多种格式文档，实现智能检索与更新</p>
        </div>
        
        <div class="feature-card">
          <div class="feature-icon">🕸️</div>
          <h3>知识图谱集成</h3>
          <p>构建结构化知识网络，捕捉概念间关系，提供更深入的上下文理解与推理能力</p>
        </div>
        
        <div class="feature-card">
          <div class="feature-icon">🤖</div>
          <h3>多模型支持</h3>
          <p>兼容多种大语言模型，灵活切换不同AI能力，满足多样化场景需求</p>
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
    // 登录后应该跳转到默认智能体而不是/agent
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

  // 普通用户跳转到默认智能体
  try {
    // 获取默认智能体
    const data = await chatApi.getDefaultAgent();
    if (data.default_agent_id) {
      // 使用后端设置的默认智能体
      router.push(`/agent/${data.default_agent_id}`);
    } else {
      // 如果没有设置默认智能体，则获取智能体列表选择第一个
      const agentData = await chatApi.getAgents();
      if (agentData.agents && agentData.agents.length > 0) {
        router.push(`/agent/${agentData.agents[0].name}`);
      } else {
        // 没有可用智能体，回退到chat页面
        router.push("/agent");
      }
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
    height: 2rem;
    margin-right: 0.6rem;
  }
}

.hero-section {
  height: 100vh;
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
