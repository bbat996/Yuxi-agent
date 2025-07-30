<template>
  <div class="log-viewer">
    <div class="log-viewer-header">
      <div class="log-filter">
        <a-select
          v-model:value="logType"
          style="width: 120px"
          placeholder="日志类型"
          @change="handleLogTypeChange"
        >
          <a-select-option value="">全部类型</a-select-option>
          <a-select-option v-for="type in logTypes" :key="type.value" :value="type.value">
            {{ type.label }}
          </a-select-option>
        </a-select>
        
        <a-range-picker
          v-model:value="timeRange"
          :show-time="{ format: 'HH:mm:ss' }"
          format="YYYY-MM-DD HH:mm:ss"
          style="width: 380px; margin-left: 8px"
          @change="handleTimeRangeChange"
        />
        
        <a-input-search
          v-model:value="searchKeyword"
          placeholder="搜索日志内容"
          style="width: 200px; margin-left: 8px"
          @search="handleSearch"
        />
      </div>
      
      <div class="log-actions">
        <a-button type="primary" @click="refreshLogs">
          <template #icon><sync-outlined /></template>
          刷新
        </a-button>
        <a-button danger @click="showClearConfirm">
          <template #icon><delete-outlined /></template>
          清除日志
        </a-button>
      </div>
    </div>
    
    <div class="log-viewer-body">
      <a-spin :spinning="loading">
        <a-empty v-if="logs.length === 0" description="暂无日志数据" />
        
        <a-timeline v-else>
          <a-timeline-item
            v-for="log in logs"
            :key="log.id"
            :color="getLogColor(log.level)"
          >
            <template #dot>
              <a-tag :color="getLogColor(log.level)">
                {{ getLogLevelText(log.level) }}
              </a-tag>
            </template>
            
            <div class="log-item">
              <div class="log-time">{{ log.timestamp }}</div>
              <div class="log-content">
                <div class="log-message">{{ log.message }}</div>
                <div v-if="log.details" class="log-details">
                  {{ log.details }}
                </div>
              </div>
            </div>
          </a-timeline-item>
        </a-timeline>
        
        <div class="log-pagination">
          <a-pagination
            v-model:current="currentPage"
            :total="totalLogs"
            :pageSize="pageSize"
            show-size-changer
            @change="handlePageChange"
            @showSizeChange="handleSizeChange"
          />
        </div>
      </a-spin>
    </div>
  </div>
</template>

<script>
import { defineComponent, ref, onMounted, watch } from 'vue';
import { message, Modal } from 'ant-design-vue';
import { SyncOutlined, DeleteOutlined } from '@ant-design/icons-vue';
import axios from 'axios';
import { formatDate } from '../../utils/date';

export default defineComponent({
  name: 'MCPLogViewer',
  components: {
    SyncOutlined,
    DeleteOutlined
  },
  props: {
    serverName: {
      type: String,
      required: true
    },
    autoRefresh: {
      type: Boolean,
      default: false
    },
    refreshInterval: {
      type: Number,
      default: 30000 // 默认30秒自动刷新一次
    }
  },
  setup(props) {
    const logs = ref([]);
    const loading = ref(false);
    const totalLogs = ref(0);
    const currentPage = ref(1);
    const pageSize = ref(10);
    const logType = ref('');
    const searchKeyword = ref('');
    const timeRange = ref([]);
    const refreshTimer = ref(null);
    
    const logTypes = [
      { value: 'info', label: '信息', color: 'blue' },
      { value: 'warning', label: '警告', color: 'orange' },
      { value: 'error', label: '错误', color: 'red' },
      { value: 'debug', label: '调试', color: 'green' }
    ];
    
    // 监听自动刷新属性变化
    watch(() => props.autoRefresh, (newVal) => {
      if (newVal) {
        startAutoRefresh();
      } else {
        stopAutoRefresh();
      }
    });
    
    // 初始化
    onMounted(() => {
      fetchLogs();
      if (props.autoRefresh) {
        startAutoRefresh();
      }
    });
    
    // 获取日志
    const fetchLogs = async () => {
      loading.value = true;
      try {
        const skip = (currentPage.value - 1) * pageSize.value;
        const limit = pageSize.value;
        
        let params = {
          skip: skip,
          limit: limit
        };
        
        if (logType.value) {
          params.log_type = logType.value;
        }
        
        if (timeRange.value && timeRange.value.length === 2) {
          params.start_time = formatDate(timeRange.value[0], 'YYYY-MM-DD HH:mm:ss');
          params.end_time = formatDate(timeRange.value[1], 'YYYY-MM-DD HH:mm:ss');
        }
        
        const response = await axios.get(`/api/mcp/servers/${props.serverName}/logs`, { params });
        
        if (response.data.success) {
          logs.value = response.data.data.logs;
          totalLogs.value = response.data.data.total;
          
          // 如果搜索关键词存在，在客户端进行过滤
          if (searchKeyword.value) {
            logs.value = logs.value.filter(log => 
              log.message.toLowerCase().includes(searchKeyword.value.toLowerCase()) || 
              (log.details && log.details.toLowerCase().includes(searchKeyword.value.toLowerCase()))
            );
            totalLogs.value = logs.value.length;
          }
        } else {
          message.error('获取日志失败');
        }
      } catch (error) {
        console.error('获取日志出错:', error);
        message.error('获取日志时发生错误');
      } finally {
        loading.value = false;
      }
    };
    
    // 刷新日志
    const refreshLogs = () => {
      fetchLogs();
    };
    
    // 清除日志确认
    const showClearConfirm = () => {
      Modal.confirm({
        title: '确认清除日志',
        content: logType.value 
          ? `确定要清除服务器 "${props.serverName}" 的所有 "${getLogLevelText(logType.value)}" 类型日志吗？`
          : `确定要清除服务器 "${props.serverName}" 的所有日志吗？`,
        okText: '确认清除',
        okType: 'danger',
        cancelText: '取消',
        onOk: clearLogs
      });
    };
    
    // 清除日志
    const clearLogs = async () => {
      loading.value = true;
      try {
        let params = {};
        if (logType.value) {
          params.log_type = logType.value;
        }
        
        const response = await axios.delete(`/api/mcp/servers/${props.serverName}/logs`, { params });
        
        if (response.data.success) {
          message.success(`成功清除 ${response.data.data.cleared_count} 条日志`);
          fetchLogs(); // 重新获取日志
        } else {
          message.error('清除日志失败');
        }
      } catch (error) {
        console.error('清除日志出错:', error);
        message.error('清除日志时发生错误');
      } finally {
        loading.value = false;
      }
    };
    
    // 日志类型变化
    const handleLogTypeChange = () => {
      currentPage.value = 1;
      fetchLogs();
    };
    
    // 时间范围变化
    const handleTimeRangeChange = () => {
      currentPage.value = 1;
      fetchLogs();
    };
    
    // 搜索
    const handleSearch = () => {
      currentPage.value = 1;
      fetchLogs();
    };
    
    // 页码变化
    const handlePageChange = (page) => {
      currentPage.value = page;
      fetchLogs();
    };
    
    // 每页条数变化
    const handleSizeChange = (current, size) => {
      pageSize.value = size;
      currentPage.value = 1;
      fetchLogs();
    };
    
    // 获取日志级别对应的颜色
    const getLogColor = (level) => {
      const type = logTypes.find(t => t.value === level);
      return type ? type.color : 'blue';
    };
    
    // 获取日志级别对应的文本
    const getLogLevelText = (level) => {
      const type = logTypes.find(t => t.value === level);
      return type ? type.label : level;
    };
    
    // 开始自动刷新
    const startAutoRefresh = () => {
      if (refreshTimer.value) {
        clearInterval(refreshTimer.value);
      }
      refreshTimer.value = setInterval(() => {
        refreshLogs();
      }, props.refreshInterval);
    };
    
    // 停止自动刷新
    const stopAutoRefresh = () => {
      if (refreshTimer.value) {
        clearInterval(refreshTimer.value);
        refreshTimer.value = null;
      }
    };
    
    return {
      logs,
      loading,
      totalLogs,
      currentPage,
      pageSize,
      logType,
      logTypes,
      searchKeyword,
      timeRange,
      fetchLogs,
      refreshLogs,
      showClearConfirm,
      clearLogs,
      handleLogTypeChange,
      handleTimeRangeChange,
      handleSearch,
      handlePageChange,
      handleSizeChange,
      getLogColor,
      getLogLevelText
    };
  }
});
</script>

<style scoped>
.log-viewer {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.log-viewer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid #f0f0f0;
}

.log-filter {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.log-actions {
  display: flex;
  gap: 8px;
}

.log-viewer-body {
  flex: 1;
  padding: 16px 0;
  overflow-y: auto;
}

.log-item {
  margin-bottom: 8px;
}

.log-time {
  font-size: 12px;
  color: #888;
  margin-bottom: 4px;
}

.log-content {
  background: #f9f9f9;
  padding: 8px 12px;
  border-radius: 4px;
  border-left: 3px solid;
}

.log-content.info {
  border-left-color: #1890ff;
}

.log-content.warning {
  border-left-color: #faad14;
}

.log-content.error {
  border-left-color: #f5222d;
}

.log-content.debug {
  border-left-color: #52c41a;
}

.log-message {
  font-weight: 500;
}

.log-details {
  margin-top: 4px;
  font-size: 12px;
  color: #666;
  white-space: pre-wrap;
}

.log-pagination {
  margin-top: 16px;
  text-align: right;
}
</style>
