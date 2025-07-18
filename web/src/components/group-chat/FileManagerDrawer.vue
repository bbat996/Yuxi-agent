<template>
  <a-drawer
    v-model:open="visible"
    title="文件管理"
    :width="500"
    placement="right"
    @close="handleClose"
  >
    <template #extra>
      <a-space>
        <a-button @click="refreshFiles" :loading="loading">
          <template #icon>
            <ReloadOutlined />
          </template>
        </a-button>
        <a-upload
          :before-upload="beforeUpload"
          :show-upload-list="false"
          :multiple="true"
          accept="*/*"
        >
          <a-button type="primary" :loading="uploading">
            <template #icon>
              <UploadOutlined />
            </template>
            上传文件
          </a-button>
        </a-upload>
      </a-space>
    </template>

    <!-- 文件统计 -->
    <div class="file-stats">
      <a-row :gutter="16">
        <a-col :span="8">
          <a-statistic
            title="总文件数"
            :value="fileStats.total_files"
            :value-style="{ color: '#1890ff' }"
          >
            <template #prefix>
              <FileOutlined />
            </template>
          </a-statistic>
        </a-col>
        <a-col :span="8">
          <a-statistic
            title="总大小"
            :value="formatFileSize(fileStats.total_size)"
            :value-style="{ color: '#52c41a' }"
          >
            <template #prefix>
              <CloudOutlined />
            </template>
          </a-statistic>
        </a-col>
        <a-col :span="8">
          <a-statistic
            title="下载次数"
            :value="fileStats.total_downloads"
            :value-style="{ color: '#fa8c16' }"
          >
            <template #prefix>
              <DownloadOutlined />
            </template>
          </a-statistic>
        </a-col>
      </a-row>
    </div>

    <!-- 文件筛选和搜索 -->
    <div class="file-controls">
      <a-row :gutter="8" align="middle">
        <a-col :span="8">
          <a-select
            v-model:value="fileFilter.type"
            placeholder="文件类型"
            allowClear
            style="width: 100%"
            @change="loadFiles"
          >
            <a-select-option value="image">图片</a-select-option>
            <a-select-option value="document">文档</a-select-option>
            <a-select-option value="video">视频</a-select-option>
            <a-select-option value="audio">音频</a-select-option>
            <a-select-option value="archive">压缩包</a-select-option>
            <a-select-option value="other">其他</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="8">
          <a-select
            v-model:value="fileFilter.uploader"
            placeholder="上传者"
            allowClear
            style="width: 100%"
            @change="loadFiles"
          >
            <a-select-option
              v-for="member in members"
              :key="member.id"
              :value="member.id"
            >
              {{ member.display_name || member.name }}
            </a-select-option>
          </a-select>
        </a-col>
        <a-col :span="8">
          <a-input
            v-model:value="fileFilter.search"
            placeholder="搜索文件名"
            allowClear
            @change="handleSearch"
          >
            <template #prefix>
              <SearchOutlined />
            </template>
          </a-input>
        </a-col>
      </a-row>
    </div>

    <!-- 文件列表 -->
    <div class="file-list">
      <a-spin :spinning="loading">
        <div v-if="files.length === 0" class="empty-state">
          <a-empty description="暂无文件" />
        </div>
        
        <div v-else class="file-items">
          <div
            v-for="file in paginatedFiles"
            :key="file.id"
            class="file-item"
            @click="selectFile(file)"
            :class="{ selected: selectedFiles.includes(file.id) }"
          >
            <!-- 文件图标和预览 -->
            <div class="file-preview">
              <div v-if="isImageFile(file)" class="image-preview">
                <img :src="getFilePreviewUrl(file)" :alt="file.filename" />
              </div>
              <div v-else class="file-icon">
                <component :is="getFileIcon(file)" :style="{ fontSize: '24px', color: getFileIconColor(file) }" />
              </div>
            </div>

            <!-- 文件信息 -->
            <div class="file-info">
              <div class="file-name" :title="file.filename">
                {{ file.filename }}
              </div>
              <div class="file-meta">
                <span class="file-size">{{ formatFileSize(file.file_size) }}</span>
                <a-divider type="vertical" />
                <span class="uploader">{{ getUploaderName(file.uploader_id) }}</span>
                <a-divider type="vertical" />
                <span class="upload-time">{{ formatTime(file.created_at) }}</span>
              </div>
              <div class="file-stats-small">
                <span><DownloadOutlined /> {{ file.download_count || 0 }}</span>
              </div>
            </div>

            <!-- 文件操作 -->
            <div class="file-actions" @click.stop>
              <a-dropdown placement="bottomRight">
                <a-button type="text" size="small">
                  <template #icon>
                    <MoreOutlined />
                  </template>
                </a-button>
                <template #overlay>
                  <a-menu>
                    <a-menu-item key="download" @click="downloadFile(file)">
                      <DownloadOutlined />
                      下载
                    </a-menu-item>
                    <a-menu-item key="copy-link" @click="copyFileLink(file)">
                      <LinkOutlined />
                      复制链接
                    </a-menu-item>
                    <a-menu-item key="preview" @click="previewFile(file)" v-if="canPreview(file)">
                      <EyeOutlined />
                      预览
                    </a-menu-item>
                    <a-menu-divider />
                    <a-menu-item key="delete" danger @click="deleteFile(file)" v-if="canDeleteFile(file)">
                      <DeleteOutlined />
                      删除
                    </a-menu-item>
                  </a-menu>
                </template>
              </a-dropdown>
            </div>
          </div>
        </div>
      </a-spin>
    </div>

    <!-- 分页 -->
    <div class="file-pagination" v-if="files.length > pageSize">
      <a-pagination
        v-model:current="currentPage"
        :total="files.length"
        :page-size="pageSize"
        :show-size-changer="false"
        :show-quick-jumper="false"
        size="small"
        simple
      />
    </div>

    <!-- 批量操作栏 -->
    <div v-if="selectedFiles.length > 0" class="batch-actions">
      <div class="selected-info">
        已选择 {{ selectedFiles.length }} 个文件
      </div>
      <a-space>
        <a-button @click="clearSelection">取消选择</a-button>
        <a-button @click="batchDownload">批量下载</a-button>
        <a-button danger @click="batchDelete" v-if="canBatchDelete">
          批量删除
        </a-button>
      </a-space>
    </div>

    <!-- 文件预览模态框 -->
    <a-modal
      v-model:open="previewModal.visible"
      :title="previewModal.file?.filename"
      :width="800"
      :footer="null"
      centered
    >
      <div class="file-preview-content">
        <!-- 图片预览 -->
        <div v-if="previewModal.file && isImageFile(previewModal.file)" class="image-preview-modal">
          <img
            :src="getFilePreviewUrl(previewModal.file)"
            :alt="previewModal.file.filename"
            style="max-width: 100%; max-height: 500px; object-fit: contain;"
          />
        </div>
        
        <!-- 文本文件预览 -->
        <div v-else-if="previewModal.file && isTextFile(previewModal.file)" class="text-preview-modal">
          <a-spin :spinning="previewLoading">
            <pre class="text-content">{{ previewContent }}</pre>
          </a-spin>
        </div>
        
        <!-- 其他文件类型 -->
        <div v-else class="unsupported-preview">
          <a-result
            status="info"
            title="无法预览此文件类型"
            sub-title="请下载文件后使用相应软件打开"
          >
            <template #extra>
              <a-button type="primary" @click="downloadFile(previewModal.file)">
                <template #icon>
                  <DownloadOutlined />
                </template>
                下载文件
              </a-button>
            </template>
          </a-result>
        </div>
      </div>
    </a-modal>
  </a-drawer>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  FileOutlined,
  UploadOutlined,
  DownloadOutlined,
  DeleteOutlined,
  MoreOutlined,
  SearchOutlined,
  ReloadOutlined,
  CloudOutlined,
  LinkOutlined,
  EyeOutlined,
  FileImageOutlined,
  FileTextOutlined,
  FileWordOutlined,
  FileExcelOutlined,
  FilePdfOutlined,
  FileZipOutlined,
  VideoCameraOutlined,
  AudioOutlined
} from '@ant-design/icons-vue'
import { groupChatApi } from '@/apis/group_chat_api'

// Props 和 Emits
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  groupId: {
    type: String,
    required: true
  },
  members: {
    type: Array,
    default: () => []
  },
  currentUserId: {
    type: String,
    required: true
  },
  canManageFiles: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:visible', 'file-uploaded'])

// 响应式数据
const loading = ref(false)
const uploading = ref(false)
const files = ref([])
const selectedFiles = ref([])
const currentPage = ref(1)
const pageSize = ref(20)

// 文件统计
const fileStats = reactive({
  total_files: 0,
  total_size: 0,
  total_downloads: 0
})

// 文件筛选
const fileFilter = reactive({
  type: undefined,
  uploader: undefined,
  search: ''
})

// 文件预览
const previewModal = reactive({
  visible: false,
  file: null
})
const previewLoading = ref(false)
const previewContent = ref('')

// 计算属性
const paginatedFiles = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return files.value.slice(start, end)
})

const canBatchDelete = computed(() => {
  return props.canManageFiles || selectedFiles.value.every(fileId => {
    const file = files.value.find(f => f.id === fileId)
    return file && file.uploader_id === props.currentUserId
  })
})

// 方法
const handleClose = () => {
  emit('update:visible', false)
  clearSelection()
}

const loadFiles = async () => {
  try {
    loading.value = true
    const params = {
      ...fileFilter,
      page: 1,
      limit: 1000 // 加载所有文件用于前端分页
    }
    
    const result = await groupChatApi.getFiles(props.groupId, params)
    files.value = result.data.files || []
    
    // 更新统计信息
    Object.assign(fileStats, result.data.stats || {})
  } catch (error) {
    message.error('加载文件列表失败：' + error.message)
  } finally {
    loading.value = false
  }
}

const refreshFiles = () => {
  loadFiles()
}

const handleSearch = (e) => {
  // 延迟搜索
  setTimeout(() => {
    loadFiles()
  }, 300)
}

const beforeUpload = async (file) => {
  try {
    uploading.value = true
    await groupChatApi.uploadFile(props.groupId, file)
    message.success('文件上传成功')
    emit('file-uploaded', file)
    await loadFiles()
  } catch (error) {
    message.error('文件上传失败：' + error.message)
  } finally {
    uploading.value = false
  }
  return false
}

const selectFile = (file) => {
  const index = selectedFiles.value.indexOf(file.id)
  if (index > -1) {
    selectedFiles.value.splice(index, 1)
  } else {
    selectedFiles.value.push(file.id)
  }
}

const clearSelection = () => {
  selectedFiles.value = []
}

const downloadFile = async (file) => {
  try {
    const result = await groupChatApi.downloadFile(props.groupId, file.id)
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([result]))
    const link = document.createElement('a')
    link.href = url
    link.download = file.filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    message.success('文件下载成功')
  } catch (error) {
    message.error('文件下载失败：' + error.message)
  }
}

const copyFileLink = async (file) => {
  try {
    const url = `${window.location.origin}/api/group-chat/${props.groupId}/files/${file.id}/download`
    await navigator.clipboard.writeText(url)
    message.success('文件链接已复制到剪贴板')
  } catch (error) {
    message.error('复制链接失败')
  }
}

const deleteFile = async (file) => {
  try {
    await groupChatApi.deleteFile(props.groupId, file.id)
    message.success('文件删除成功')
    await loadFiles()
  } catch (error) {
    message.error('文件删除失败：' + error.message)
  }
}

const batchDownload = () => {
  selectedFiles.value.forEach(fileId => {
    const file = files.value.find(f => f.id === fileId)
    if (file) {
      downloadFile(file)
    }
  })
  clearSelection()
}

const batchDelete = async () => {
  try {
    const promises = selectedFiles.value.map(fileId => 
      groupChatApi.deleteFile(props.groupId, fileId)
    )
    await Promise.all(promises)
    message.success(`成功删除 ${selectedFiles.value.length} 个文件`)
    clearSelection()
    await loadFiles()
  } catch (error) {
    message.error('批量删除失败：' + error.message)
  }
}

const previewFile = async (file) => {
  previewModal.file = file
  previewModal.visible = true
  
  if (isTextFile(file)) {
    try {
      previewLoading.value = true
      // 这里应该调用预览接口获取文件内容
      // const result = await groupChatApi.previewFile(props.groupId, file.id)
      // previewContent.value = result.data.content
      previewContent.value = '文件预览功能待实现...'
    } catch (error) {
      message.error('预览失败：' + error.message)
    } finally {
      previewLoading.value = false
    }
  }
}

const canPreview = (file) => {
  return isImageFile(file) || isTextFile(file)
}

const canDeleteFile = (file) => {
  return props.canManageFiles || file.uploader_id === props.currentUserId
}

// 文件类型判断
const isImageFile = (file) => {
  const imageTypes = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg']
  const ext = file.filename.split('.').pop()?.toLowerCase()
  return imageTypes.includes(ext)
}

const isTextFile = (file) => {
  const textTypes = ['txt', 'md', 'json', 'xml', 'csv', 'log']
  const ext = file.filename.split('.').pop()?.toLowerCase()
  return textTypes.includes(ext)
}

const getFileIcon = (file) => {
  const ext = file.filename.split('.').pop()?.toLowerCase()
  
  if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'].includes(ext)) {
    return FileImageOutlined
  } else if (['txt', 'md', 'log'].includes(ext)) {
    return FileTextOutlined
  } else if (['doc', 'docx'].includes(ext)) {
    return FileWordOutlined
  } else if (['xls', 'xlsx'].includes(ext)) {
    return FileExcelOutlined
  } else if (['pdf'].includes(ext)) {
    return FilePdfOutlined
  } else if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) {
    return FileZipOutlined
  } else if (['mp4', 'avi', 'mov', 'wmv', 'flv'].includes(ext)) {
    return VideoCameraOutlined
  } else if (['mp3', 'wav', 'flac', 'aac'].includes(ext)) {
    return AudioOutlined
  }
  
  return FileOutlined
}

const getFileIconColor = (file) => {
  const ext = file.filename.split('.').pop()?.toLowerCase()
  
  if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'].includes(ext)) {
    return '#52c41a'
  } else if (['doc', 'docx'].includes(ext)) {
    return '#1890ff'
  } else if (['xls', 'xlsx'].includes(ext)) {
    return '#52c41a'
  } else if (['pdf'].includes(ext)) {
    return '#ff4d4f'
  } else if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) {
    return '#fa8c16'
  } else if (['mp4', 'avi', 'mov', 'wmv', 'flv'].includes(ext)) {
    return '#722ed1'
  } else if (['mp3', 'wav', 'flac', 'aac'].includes(ext)) {
    return '#eb2f96'
  }
  
  return '#666'
}

const getFilePreviewUrl = (file) => {
  return `/api/group-chat/${props.groupId}/files/${file.id}/preview`
}

const getUploaderName = (uploaderId) => {
  const member = props.members.find(m => m.id === uploaderId)
  return member ? (member.display_name || member.name) : '未知'
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) { // 1分钟内
    return '刚刚'
  } else if (diff < 3600000) { // 1小时内
    return Math.floor(diff / 60000) + '分钟前'
  } else if (diff < 86400000) { // 1天内
    return Math.floor(diff / 3600000) + '小时前'
  } else {
    return date.toLocaleDateString()
  }
}

// 监听器
watch(() => props.visible, (visible) => {
  if (visible) {
    loadFiles()
  }
})

watch(() => props.groupId, (groupId) => {
  if (groupId && props.visible) {
    loadFiles()
  }
})
</script>

<style scoped>
.file-stats {
  margin-bottom: 16px;
  padding: 16px;
  background: #f9f9f9;
  border-radius: 6px;
}

.file-controls {
  margin-bottom: 16px;
}

.file-list {
  min-height: 400px;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.file-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.file-item:hover {
  border-color: #d9d9d9;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.file-item.selected {
  border-color: #1890ff;
  background-color: #e6f7ff;
}

.file-preview {
  width: 48px;
  height: 48px;
  margin-right: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  overflow: hidden;
}

.image-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.file-icon {
  display: flex;
  align-items: center;
  justify-content: center;
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-meta {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.file-stats-small {
  font-size: 11px;
  color: #999;
}

.file-actions {
  margin-left: 8px;
}

.file-pagination {
  margin-top: 16px;
  text-align: center;
}

.batch-actions {
  position: sticky;
  bottom: 0;
  background: white;
  border-top: 1px solid #f0f0f0;
  padding: 12px 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
}

.selected-info {
  font-size: 14px;
  color: #1890ff;
  font-weight: 500;
}

.file-preview-content {
  max-height: 500px;
  overflow: auto;
}

.text-content {
  white-space: pre-wrap;
  word-break: break-word;
  font-family: 'Monaco', 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
  padding: 12px;
  background: #f5f5f5;
  border-radius: 4px;
}
</style> 