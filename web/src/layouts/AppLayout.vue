<template>
  <div class="app-layout" :class="{ 'use-top-bar': layoutSettings.useTopBar }">
    <div class="debug-panel">
      <!-- <a-float-button
        @click="layoutSettings.showDebug = !layoutSettings.showDebug"
        tooltip="调试面板"
        :style="{
          right: '12px'
        }"
      >
        <template #icon>
          <BugOutlined />
        </template>
      </a-float-button> -->
      <a-drawer
        v-model:open="layoutSettings.showDebug"
        title="调试面板"
        width="800"
        :contentWrapperStyle="{ maxWidth: '100%' }"
        placement="right"
      >
        <DebugComponent />
      </a-drawer>
    </div>
    <div class="header" :class="{ 'top-bar': layoutSettings.useTopBar }">
      <div class="logo circle">
        <router-link to="/">
          <img src="/avatar.png" />
          <span class="logo-text">{{ configStore.siteName }}</span>
        </router-link>
      </div>
      <div class="nav">
        <!-- 使用mainList渲染导航项 -->
        <RouterLink
          v-for="(item, index) in mainList"
          :key="index"
          :to="item.path"
          v-show="!item.hidden"
          class="nav-item"
          active-class="active"
        >
          <component
            class="icon"
            :is="route.path.startsWith(item.path) ? item.activeIcon : item.icon"
            size="22"
          />
          <span class="text">{{ item.name }}</span>
        </RouterLink>

   
      </div>
      <div class="fill" style="flex-grow: 1"></div>

      <!-- <div class="nav-item api-docs">
        <a-tooltip placement="right">
          <template #title>接口文档 {{ apiDocsUrl }}</template>
          <a :href="apiDocsUrl" target="_blank" class="github-link">
            <ApiOutlined class="icon" style="color: #222;"/>
          </a>
        </a-tooltip>
      </div> -->


      <!-- 用户信息组件 -->
      <div class="nav-item user-info">
        <a-tooltip placement="right">
          <template #title>用户信息</template>
          <UserInfoComponent />
        </a-tooltip>
      </div>
      <a-tooltip placement="right">
          <template #title
            >后端疑似没有正常启动或者正在繁忙中，请刷新一下或者检查 docker logs api-dev</template
          >
          <div class="nav-item warning" v-if="!configStore.config._config_items">
            <component class="icon" :is="ExclamationCircleOutlined" />
            <span class="text">警告</span>
          </div>
        </a-tooltip>
    </div>
    <div class="header-mobile">
      <RouterLink to="/chat" class="nav-item" active-class="active">对话</RouterLink>
      <RouterLink to="/database" class="nav-item" active-class="active">知识</RouterLink>
      <RouterLink to="/setting" class="nav-item" active-class="active">设置</RouterLink>
    </div>
    <router-view v-slot="{ Component, route }" id="app-router-view">
      <keep-alive v-if="route.meta.keepAlive !== false">
        <component :is="Component" />
      </keep-alive>
      <component :is="Component" v-else />
    </router-view>
  </div>
</template>


<script setup>
import { ref, reactive, KeepAlive, onMounted, computed } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import {
  BugOutlined,
  ExclamationCircleOutlined,
  UserOutlined,
  LogoutOutlined
} from '@ant-design/icons-vue'
import {
  Bot,
  Waypoints,
  LibraryBig,
  MessageSquareMore,
  Settings,
  User2,
  Mic2
} from 'lucide-vue-next'
import { Dropdown } from 'ant-design-vue'

import { useConfigStore } from '@/stores/config'
import { useDatabaseStore } from '@/stores/database'
import DebugComponent from '@/components/DebugComponent.vue'
import UserInfoComponent from '@/components/UserInfoComponent.vue'

const configStore = useConfigStore()
const databaseStore = useDatabaseStore()

const layoutSettings = reactive({
  showDebug: false,
  useTopBar: false // 是否使用顶栏
})

const getRemoteConfig = () => {
  configStore.refreshConfig()
}

const getRemoteDatabase = () => {
  if (!configStore.config.enable_knowledge_base) {
    return
  }
  databaseStore.refreshDatabase()
}

onMounted(() => {
  getRemoteConfig()
  getRemoteDatabase()
})

// 打印当前页面的路由信息，使用 vue3 的 setup composition API
const route = useRoute()
console.log(route)

// 下面是导航菜单部分，添加智能体项
const mainList = [
  {
    name: '智能体',
    path: '/agent',
    icon: Bot,
    activeIcon: Bot
  },
  {
    name: '智能体管理',
    path: '/agent/management',
    icon: Settings,
    activeIcon: Settings,
    hidden: !configStore.config.enable_agent_management
  },
  {
    name: '知识库',
    path: '/database',
    icon: LibraryBig,
    activeIcon: LibraryBig
    // hidden: !configStore.config.enable_knowledge_base,
  },
  // {
  //   name: '数字人',
  //   path: '/digital-human',
  //   icon: User2,
  //   activeIcon: User2
  // },
  // {
  //   name: '音色',
  //   path: '/voice',
  //   icon: Mic2,
  //   activeIcon: Mic2
  // },
  {
    name: '设置',
    path: '/setting',
    icon: Settings,
    activeIcon: Settings
  },
  // {
  //   name: '图谱',
  //   path: '/graph',
  //   icon: Waypoints,
  //   activeIcon: Waypoints
  //   // hidden: !configStore.config.enable_knowledge_graph,
  // },

]
</script>

<style lang="less" scoped>
@import '@/assets/css/main.css';

:root {
  --header-width: 100px;
}

.app-layout {
  display: flex;
  flex-direction: row;
  width: 100%;
  height: 100vh;
  min-width: var(--min-width);

  .header-mobile {
    display: none;
  }

  .debug-panel {
    position: absolute;
    z-index: 100;
    right: 0;
    bottom: 50px;
    border-radius: 20px 0 0 20px;
    cursor: pointer;
  }
}

div.header,
#app-router-view {
  height: 100%;
  max-width: 100%;
  user-select: none;
}

#app-router-view {
  flex: 1 1 auto;
  overflow-y: auto;
}

.header {
  display: flex;
  flex-direction: column;
  flex: 0 0 80px;
  justify-content: flex-start;
  align-items: center;
  background-color: #121212;
  height: 100%;
  width: 80px;
  border-right: 1px solid #2a2a2a;

  .logo {
    width: 50px;
    height: 50px;
    margin: 14px 0 14px 0;

    img {
      width: 100%;
      height: 100%;
      border-radius: 4px;
    }

    .logo-text {
      display: none;
    }

    & > a {
      text-decoration: none;
      font-size: 24px;
      font-weight: bold;
      color: #ffffff;
    }
  }

  .nav-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 52px;
    padding: 4px;
    padding-top: 10px;
    border: 1px solid transparent;
    border-radius: 8px;
    background-color: transparent;
    color: #f0f0f0;
    font-size: 20px;
    transition: all 0.1s ease-in-out;
    margin: 0;
    text-decoration: none;
    cursor: pointer;
    width: 56px;
    padding: 6px;

    &.api-docs {
      padding: 10px 12px;
    }

    &.active {
      font-weight: bold;
      color: white;
      background-color: rgba(255, 255, 255, 0.15);
      border: 1px solid #4299e1;
      box-shadow: 0 0 8px rgba(66, 153, 225, 0.5);

      &:hover {
        transform: none;
        backdrop-filter: none;
      }
    }

    &.warning {
      color: #ff4d4f;
    }

    &:hover {
      backdrop-filter: blur(10px);
      background-color: rgba(255, 255, 255, 0.15);
      transform: translateY(-2px);
    }

    .text {
      font-size: 12px;
      margin-top: 4px;
      text-align: center;
    }
  }

  .setting {
    width: auto;
    font-size: 20px;
    color: #ffffff;
    margin-bottom: 8px;
    padding: 16px 12px;

    &:hover {
      cursor: pointer;
    }
  }
}

.header .nav {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: center;
  position: relative;
  height: 45px;
  gap: 16px;
}

@media (max-width: 520px) {
  .app-layout {
    flex-direction: column-reverse;

    div.header {
      display: none;
    }

    .debug-panel {
      bottom: 10rem;
    }
  }
  .app-layout div.header-mobile {
    display: flex;
    flex-direction: row;
    width: 100%;
    padding: 0 20px;
    justify-content: space-around;
    align-items: center;
    flex: 0 0 60px;
    border-right: none;
    height: 50px;

    .nav-item {
      text-decoration: none;
      width: 50px;
      color: var(--gray-00);
      font-size: 1rem;
      font-weight: bold;
      transition: color 0.1s ease-in-out, font-size 0.1s ease-in-out;

      &.active {
        color: #1890ff;
        font-size: 1.1rem;
      }
    }
  }
  .app-layout .chat-box::webkit-scrollbar {
    width: 0;
  }
}

.app-layout.use-top-bar {
  flex-direction: column;
}

.header.top-bar {
  flex-direction: row;
  flex: 0 0 50px;
  width: 100%;
  height: 50px;
  border-right: none;
  border-bottom: 1px solid #2a2a2a;
  background-color: #121212;
  padding: 0 20px;
  gap: 24px;

  .logo {
    width: fit-content;
    height: 28px;
    margin-right: 16px;
    display: flex;
    align-items: center;

    a {
      display: flex;
      align-items: center;
      text-decoration: none;
      color: inherit;
    }

    img {
      width: 28px;
      height: 28px;
      margin-right: 8px;
    }

    .logo-text {
      display: block;
      font-size: 16px;
      font-weight: 600;
      letter-spacing: 0.5px;
      color: #ffffff;
      white-space: nowrap;
    }
  }

  .nav {
    flex-direction: row;
    height: auto;
    gap: 20px;
  }

  .nav-item {
    flex-direction: row;
    width: auto;
    padding: 4px 16px;
    margin: 0;

    .icon {
      margin-right: 8px;
      font-size: 15px;
      border: none;
      outline: none;

      &:focus,
      &:active {
        border: none;
        outline: none;
      }
    }

    .text {
      margin-top: 0;
      font-size: 15px;
    }

    &.setting {
      padding: 8px 12px;

      .icon {
        margin-right: 0;
        font-size: 18px;
      }

      &.active {
        color: white;
        background-color: #2b6cb0;
        border: 1px solid #4299e1;
        padding: 6px 18px;
        box-shadow: 0 0 8px rgba(66, 153, 225, 0.5);
      }
    }
  }
}
</style>