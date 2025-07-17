<template>
  <a-modal :open="props.modelValue" title="选择提示词模板" width="1000px" :footer="null" @cancel="handleCancel">
    <div v-if="categories.length > 0">
      <a-tabs v-model:activeKey="selectedCategory">
        <a-tab-pane v-for="cat in categories" :key="cat" :tab="cat" />
      </a-tabs>

      <div v-if="filteredTemplates.length > 0" class="card-list-container">
        <a-row :gutter="[16, 16]">
          <a-col :xs="24" :sm="12" :md="8" v-for="item in paginatedTemplates" :key="item.id">
            <a-popover trigger="hover" placement="top" :mouseEnterDelay="0.5">
              <template #content>
                <div class="prompt-popover-content">
                  <pre>{{ item.prompt }}</pre>
                </div>
              </template>
              <a-card hoverable class="prompt-card" @click="handleSelect(item)">
                <a-card-meta :title="item.name" :description="item.description" />
              </a-card>
            </a-popover>
          </a-col>
        </a-row>
        <a-pagination
          v-if="filteredTemplates.length > pageSize"
          v-model:current="currentPage"
          :total="filteredTemplates.length"
          :page-size="pageSize"
          show-less-items
          class="pagination"
        />
      </div>
      <a-empty v-else description="该分类下暂无模板" />
    </div>
    <a-empty v-else description="暂无模板数据" />
  </a-modal>
</template>

<script setup>
import { ref, onMounted, defineEmits, defineProps, watch, computed } from 'vue';
import { promptApi } from '@/apis/prompt_api';

const props = defineProps({
  modelValue: Boolean
});
const emit = defineEmits(['update:modelValue', 'select']);

const categorizedTemplates = ref({});
const categories = ref([]);
const selectedCategory = ref('');
const currentPage = ref(1);
const pageSize = ref(6); // 每页显示6个卡片

const handleCancel = () => {
  emit('update:modelValue', false);
};

const handleSelect = (item) => {
  emit('select', item.prompt);
  emit('update:modelValue', false);
};

const filteredTemplates = computed(() => {
  return categorizedTemplates.value[selectedCategory.value] || [];
});

const paginatedTemplates = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  const end = start + pageSize.value;
  return filteredTemplates.value.slice(start, end);
});

watch(selectedCategory, () => {
  currentPage.value = 1;
});

onMounted(async () => {
  try {
    const res = await promptApi.getAllTemplates();
    if (Array.isArray(res)) {
      const grouped = res.reduce((acc, item) => {
        const { category, key, template } = item;
        if (!acc[category]) {
          acc[category] = [];
        }
        acc[category].push({ id: key, ...template });
        return acc;
      }, {});

      categorizedTemplates.value = grouped;
      categories.value = Object.keys(grouped);
      if (categories.value.length > 0) {
        selectedCategory.value = categories.value[0];
      }
    } else {
      console.error('获取提示词模板失败，返回数据格式不正确或为空', res);
      categorizedTemplates.value = {};
      categories.value = [];
    }
  } catch (error) {
    console.error('获取提示词模板时发生错误:', error);
    categorizedTemplates.value = {};
    categories.value = [];
  }
});
</script>

<style scoped>
.card-list-container {
  height: 450px; /* 固定容器高度 */
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.prompt-card {
  height: 120px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
}

.prompt-card :deep(.ant-card-body) {
  flex-grow: 1;
  overflow: hidden;
}

.prompt-card :deep(.ant-card-meta-description) {
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3; /* 显示3行 */
  line-clamp: 3;
  -webkit-box-orient: vertical;
}

.prompt-popover-content {
  max-width: 400px;
  max-height: 300px;
  overflow-y: auto;
}

.prompt-popover-content pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'source-code-pro', monospace;
}

.pagination {
  text-align: right;
  margin-top: 16px;
}
</style>
