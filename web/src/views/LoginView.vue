<template>
  <!-- TODO 登录页面样式优化；（1）风格和整个系统统一； -->
  <div class="login-view" :class="{ 'has-alert': serverStatus === 'error' }">
    <!-- 服务状态提示 -->
    <div v-if="serverStatus === 'error'" class="server-status-alert">
      <div class="alert-content">
        <exclamation-circle-outlined class="alert-icon" />
        <div class="alert-text">
          <div class="alert-title">服务端连接失败</div>
          <div class="alert-message">{{ serverError }}</div>
        </div>
        <a-button type="link" size="small" @click="checkServerHealth" :loading="healthChecking">
          重试
        </a-button>
      </div>
    </div>

    <!-- 左侧艺术图片区域 -->
    <div class="login-art-section" :style="{ backgroundImage: `url(${loginBg})` }">
      <div class="art-overlay"></div>
    </div>

    <!-- 右侧登录表单区域 -->
    <div class="login-form-section">
      <div class="login-container">
        <div class="login-logo">
          <img src="/public/avatar.png" :alt="configStore.siteName" class="logo-img" />
          <h1>{{ configStore.siteName }}</h1>
        </div>

        <!-- 初始化管理员表单 -->
        <div v-if="isFirstRun" class="login-form">
          <h2>系统初始化</h2>
          <p class="init-desc">系统首次运行，请创建超级管理员账户：</p>

          <a-form
            :model="adminForm"
            @finish="handleInitialize"
            layout="vertical"
          >
            <a-form-item
              label="用户名"
              name="username"
              :rules="[{ required: true, message: '请输入用户名' }]"
            >
              <a-input v-model:value="adminForm.username" prefix-icon="user" />
            </a-form-item>

            <a-form-item
              label="密码"
              name="password"
              :rules="[{ required: true, message: '请输入密码' }]"
            >
              <a-input-password v-model:value="adminForm.password" prefix-icon="lock" />
            </a-form-item>

            <a-form-item
              label="确认密码"
              name="confirmPassword"
              :rules="[
                { required: true, message: '请确认密码' },
                { validator: validateConfirmPassword }
              ]"
            >
              <a-input-password v-model:value="adminForm.confirmPassword" prefix-icon="lock" />
            </a-form-item>

            <a-form-item>
              <a-button type="primary" html-type="submit" :loading="loading" block>创建管理员账户</a-button>
            </a-form-item>
          </a-form>
        </div>

        <!-- 登录表单 -->
        <div v-else class="login-form">
          <h2>用户登录</h2>

          <a-form
            :model="loginForm"
            @finish="handleLogin"
            layout="vertical"
          >
            <a-form-item
              label="用户名"
              name="username"
              :rules="[{ required: true, message: '请输入用户名' }]"
            >
              <a-input v-model:value="loginForm.username">
                <template #prefix>
                  <user-outlined />
                </template>
              </a-input>
            </a-form-item>

            <a-form-item
              label="密码"
              name="password"
              :rules="[{ required: true, message: '请输入密码' }]"
            >
              <a-input-password v-model:value="loginForm.password">
                <template #prefix>
                  <lock-outlined />
                </template>
              </a-input-password>
            </a-form-item>

            <a-form-item>
              <div class="login-options">
                <a-checkbox v-model:checked="rememberMe" @click="showDevMessage">记住我</a-checkbox>
                <a class="forgot-password" @click="showDevMessage">忘记密码?</a>
              </div>
            </a-form-item>

            <a-form-item>
              <a-button type="primary" html-type="submit" :loading="loading" block>登录</a-button>
            </a-form-item>

            <!-- 第三方登录选项 -->
            <div class="third-party-login">
              <div class="divider">
                <span>其他登录方式</span>
              </div>
              <div class="login-icons">
                <a-tooltip title="微信登录">
                  <a-button shape="circle" class="login-icon" @click="showDevMessage">
                    <template #icon><wechat-outlined /></template>
                  </a-button>
                </a-tooltip>
                <a-tooltip title="企业微信登录">
                  <a-button shape="circle" class="login-icon" @click="showDevMessage">
                    <template #icon><qrcode-outlined /></template>
                  </a-button>
                </a-tooltip>
                <a-tooltip title="飞书登录">
                  <a-button shape="circle" class="login-icon" @click="showDevMessage">
                    <template #icon><thunderbolt-outlined /></template>
                  </a-button>
                </a-tooltip>
              </div>
            </div>
          </a-form>
        </div>

        <!-- 错误提示 -->
        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>

        <!-- 页脚 -->
        <div class="login-footer">
          <a @click="showDevMessage">联系我们</a>
          <a @click="showDevMessage">使用帮助</a>
          <a @click="showDevMessage">隐私政策</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/stores/user';
import { useConfigStore } from '@/stores/config';
import { message } from 'ant-design-vue';
import { chatApi } from '@/apis/auth_api';
import { authApi, healthApi } from '@/apis/public_api';
import { UserOutlined, LockOutlined, WechatOutlined, QrcodeOutlined, ThunderboltOutlined, ExclamationCircleOutlined } from '@ant-design/icons-vue';
import loginBg from '@/assets/pics/login_bg.png';

const router = useRouter();
const userStore = useUserStore();
const configStore = useConfigStore();

// 状态
const isFirstRun = ref(false);
const loading = ref(false);
const errorMessage = ref('');
const rememberMe = ref(false);
const serverStatus = ref('loading');
const serverError = ref('');
const healthChecking = ref(false);

// 登录表单
const loginForm = reactive({
  username: '',
  password: ''
});

// 管理员初始化表单
const adminForm = reactive({
  username: '',
  password: '',
  confirmPassword: ''
});

// 开发中功能提示
const showDevMessage = () => {
  message.info('该功能正在开发中，敬请期待！');
};

// 密码确认验证
const validateConfirmPassword = (rule, value) => {
  if (value === '') {
    return Promise.reject('请确认密码');
  }
  if (value !== adminForm.password) {
    return Promise.reject('两次输入的密码不一致');
  }
  return Promise.resolve();
};

// 处理登录
const handleLogin = async () => {
  try {
    loading.value = true;
    errorMessage.value = '';

    await userStore.login({
      username: loginForm.username,
      password: loginForm.password
    });

    message.success('登录成功');

    // 获取重定向路径
    const redirectPath = sessionStorage.getItem('redirect') || '/';
    sessionStorage.removeItem('redirect'); // 清除重定向信息

    // 根据用户角色决定重定向目标
    if (redirectPath === '/') {
      // 如果是管理员，直接跳转到/chat页面
      if (userStore.isAdmin) {
        router.push('/agent');
        return;
      }

      // 普通用户跳转到第一个可用智能体
      try {
        // 获取第一个可用智能体
        const agentData = await chatApi.getAgents();
        if (agentData.agents && agentData.agents.length > 0) {
          router.push(`/agent/${agentData.agents[0].name}`);
          return;
        }

        // 没有可用智能体，回退到首页
        router.push('/');
      } catch (error) {
        console.error('获取智能体信息失败:', error);
        router.push('/');
      }
    } else {
      // 跳转到其他预设的路径
      router.push(redirectPath);
    }
  } catch (error) {
    console.error('登录失败:', error);
    errorMessage.value = error.message || '登录失败，请检查用户名和密码';
  } finally {
    loading.value = false;
  }
};

// 处理初始化管理员
const handleInitialize = async () => {
  try {
    loading.value = true;
    errorMessage.value = '';

    if (adminForm.password !== adminForm.confirmPassword) {
      errorMessage.value = '两次输入的密码不一致';
      return;
    }

    await userStore.initialize({
      username: adminForm.username,
      password: adminForm.password
    });

    message.success('管理员账户创建成功');
    router.push('/');
  } catch (error) {
    console.error('初始化失败:', error);
    errorMessage.value = error.message || '初始化失败，请重试';
  } finally {
    loading.value = false;
  }
};

// 检查是否是首次运行
const checkFirstRunStatus = async () => {
  try {
    loading.value = true;
    const isFirst = await userStore.checkFirstRun();
    isFirstRun.value = isFirst;
  } catch (error) {
    console.error('检查首次运行状态失败:', error);
    errorMessage.value = '系统出错，请稍后重试';
  } finally {
    loading.value = false;
  }
};

// 检查服务器健康状态
const checkServerHealth = async () => {
  try {
    healthChecking.value = true;
    const response = await healthApi.check();
    if (response.status === 'ok') {
      serverStatus.value = 'ok';
    } else {
      serverStatus.value = 'error';
      serverError.value = response.message || '服务端状态异常';
    }
  } catch (error) {
    console.error('检查服务器健康状态失败:', error);
    serverStatus.value = 'error';
    serverError.value = error.message || '无法连接到服务端，请检查网络连接';
  } finally {
    healthChecking.value = false;
  }
};

// 组件挂载时
onMounted(async () => {
  // 如果已登录，跳转到首页
  if (userStore.isLoggedIn) {
    router.push('/');
    return;
  }

  // 首先检查服务器健康状态
  await checkServerHealth();

  // 检查是否是首次运行
  await checkFirstRunStatus();
});
</script>

<style lang="less" scoped>
.login-view {
  height: 100vh;
  width: 100%;
  display: flex;
  position: relative;

  &.has-alert {
    padding-top: 60px;
  }
}

.login-art-section {
  flex: 1;
  background-size: cover;
  background-position: center;
  position: relative;
  overflow: hidden;

  .art-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(to right, rgba(0, 0, 0, 0.1), rgba(0, 0, 0, 0.3));
  }
}

.login-form-section {
  width: 500px;
  background-color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  box-shadow: -4px 0 24px rgba(0, 0, 0, 0.1);
}

.login-container {
  width: 100%;
  max-width: 420px;
}

.login-logo {
  text-align: center;
  margin-bottom: 40px;

  .logo-img {
    height: 70px;
    width: 70px;
    object-fit: cover;
    border-radius: 8px;
    margin-bottom: 16px;
  }

  h1 {
    font-size: 28px;
    font-weight: 600;
    color: var(--ant-primary-color);
    margin: 0;
  }
}

.login-form {
  h2 {
    text-align: center;
    margin-bottom: 30px;
    font-size: 22px;
    font-weight: 500;
    color: #333;
  }

  :deep(.ant-form-item) {
    margin-bottom: 20px;
  }

  :deep(.ant-input-affix-wrapper) {
    padding: 10px 11px;
    height: auto;
  }

  :deep(.ant-btn) {
    font-size: 16px;
  }
}

.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;

  .forgot-password {
    color: #1890ff;
    font-size: 14px;

    &:hover {
      color: #40a9ff;
    }
  }
}

.init-desc {
  margin-bottom: 24px;
  color: #666;
  text-align: center;
}

.error-message {
  margin-top: 16px;
  padding: 10px 12px;
  background-color: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 4px;
  color: #ff4d4f;
  font-size: 14px;
}

.third-party-login {
  margin-top: 20px;

  .divider {
    position: relative;
    text-align: center;
    margin: 16px 0;

    &::before, &::after {
      content: '';
      position: absolute;
      top: 50%;
      width: calc(50% - 60px);
      height: 1px;
      background-color: #e8e8e8;
    }

    &::before {
      left: 0;
    }

    &::after {
      right: 0;
    }

    span {
      display: inline-block;
      padding: 0 12px;
      background-color: #fff;
      position: relative;
      color: #999;
      font-size: 14px;
    }
  }

  .login-icons {
    display: flex;
    justify-content: center;
    margin-top: 16px;

    .login-icon {
      margin: 0 12px;
      width: 42px;
      height: 42px;
      color: #666;
      border: 1px solid var(--gray-300);
      transition: all 0.3s;

      &:hover {
        color: var(--main-color);
        border-color: var(--main-color);
      }
    }
  }
}

.login-footer {
  margin-top: 24px;
  text-align: center;
  font-size: 13px;

  a {
    color: #666;
    margin: 0 8px;
    cursor: pointer;

    &:hover {
      color: var(--main-color);
    }
  }
}

.server-status-alert {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  padding: 12px 20px;
  background: linear-gradient(135deg, #ff4d4f, #ff7875);
  color: white;
  z-index: 1000;
  box-shadow: 0 2px 8px rgba(255, 77, 79, 0.3);

  .alert-content {
    display: flex;
    align-items: center;
    max-width: 1200px;
    margin: 0 auto;

    .alert-icon {
      font-size: 20px;
      margin-right: 12px;
      color: white;
    }

    .alert-text {
      flex: 1;

      .alert-title {
        font-weight: 600;
        font-size: 16px;
        margin-bottom: 2px;
      }

      .alert-message {
        font-size: 14px;
        opacity: 0.9;
      }
    }

    :deep(.ant-btn-link) {
      color: white;
      border-color: white;

      &:hover {
        color: white;
        background-color: rgba(255, 255, 255, 0.1);
      }
    }
  }
}

@media (max-width: 768px) {
  .login-view {
    flex-direction: column;
  }

  .login-art-section {
    height: 200px;
  }

  .login-form-section {
    width: 100%;
    padding: 20px;
  }
}
</style>