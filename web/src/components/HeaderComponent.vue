<template>
  <div class="header-container">
    <div class="header-content">
      <div class="header-actions" v-if="showBackButton || $slots.left">
        <a-button v-if="showBackButton" @click="onBack" type="text" shape="circle" title="返回">
          <template #icon>
            <ArrowLeftOutlined />
          </template>
        </a-button>
        <slot name="left"></slot>
      </div>
      <div class="header-title">
        <h1>{{ title }}</h1>
        <p v-if="description">{{ description }}</p>
      </div>
      <div class="header-actions" v-if="showSaveButton || $slots.actions">
        <a-button v-if="showSaveButton" type="primary" :loading="saving" @click="onSave">
          保存配置
        </a-button>
        <loading-outlined v-if="loading" />
        <slot name="actions"></slot>
      </div>
    </div>
  </div>
</template>

<script setup>
import { LoadingOutlined, ArrowLeftOutlined } from '@ant-design/icons-vue';

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  description: {
    type: String,
    default: ''
  },
  loading: {
    type: Boolean,
    default: false
  },
  showBackButton: {
    type: Boolean,
    default: false
  },
  showSaveButton: {
    type: Boolean,
    default: false
  },
  saving: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['back', 'save']);

const onBack = () => {
  emit('back');
};

const onSave = () => {
  emit('save');
};
</script>

<style scoped lang="less">
.header-container {
  background-color: white;
  backdrop-filter: blur(10px);
  padding: 16px 24px;
  border-bottom: 1px solid #f0f0f0;
  position: sticky;
  top: 0;
  z-index: 1000;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.header-title {
  flex: 1;
  width: 100%;
  font-size: 13px;
  color: rgba(0, 0, 0, 0.45);

  h1 {
    margin: 0;
    font-size: 20px;
    font-weight: 500;
    color: rgba(0, 0, 0, 0.85);
  }

  p {
    margin: 1px 0 0;
  }
}

.header-actions {
  display: flex;
  gap: 8px;
}
</style>
