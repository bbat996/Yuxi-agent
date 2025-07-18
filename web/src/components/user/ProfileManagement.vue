<template>
  <div class="profile-management">
    <!-- 头部区域 -->
    <div class="header-section">
      <div class="header-content">
        <h3 class="title">个人信息</h3>
        <p class="description">管理您的个人信息、头像和账户设置</p>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="content-section">
      <a-row :gutter="24">
        <!-- 左侧：个人信息编辑 -->
        <a-col :xs="24" :md="14">
          <a-card title="基本信息" class="profile-card">
            <a-spin :spinning="loading.profile">
              <a-form
                ref="profileFormRef"
                :model="profileForm"
                :rules="profileRules"
                layout="vertical"
                class="profile-form"
              >
                <!-- 头像区域 -->
                <a-form-item label="头像">
                  <div class="avatar-section">
                    <div class="avatar-display">
                      <a-avatar :size="80" :src="avatarPreview || profileForm.avatar">
                        <template v-if="!avatarPreview && !profileForm.avatar">
                          <UserOutlined />
                        </template>
                      </a-avatar>
                    </div>
                    <div class="avatar-actions">
                      <a-upload
                        :show-upload-list="false"
                        :before-upload="beforeAvatarUpload"
                        accept="image/*"
                      >
                        <a-button type="dashed" size="small">
                          <UploadOutlined />
                          更换头像
                        </a-button>
                      </a-upload>
                      <p class="avatar-hint">支持 JPG、PNG 格式，建议 200x200 像素</p>
                    </div>
                  </div>
                </a-form-item>

                <!-- 用户名 -->
                <a-form-item label="用户名">
                  <a-input :value="profileForm.username" disabled />
                  <div class="form-hint">用户名不可修改</div>
                </a-form-item>

                <!-- 显示名称 -->
                <a-form-item label="显示名称" name="display_name">
                  <a-input
                    v-model:value="profileForm.display_name"
                    placeholder="请输入显示名称"
                    :maxlength="50"
                  />
                  <div class="form-hint">其他用户看到的名称</div>
                </a-form-item>

                <!-- 邮箱 -->
                <a-form-item label="邮箱" name="email">
                  <a-input
                    v-model:value="profileForm.email"
                    placeholder="请输入邮箱地址"
                    type="email"
                  />
                </a-form-item>

                <!-- 操作按钮 -->
                <a-form-item>
                  <a-space>
                    <a-button
                      type="primary"
                      @click="updateProfile"
                      :loading="loading.update"
                    >
                      保存修改
                    </a-button>
                    <a-button @click="resetProfileForm">重置</a-button>
                  </a-space>
                </a-form-item>
              </a-form>
            </a-spin>
          </a-card>

          <!-- 密码修改 -->
          <a-card title="修改密码" class="profile-card">
            <a-form
              ref="passwordFormRef"
              :model="passwordForm"
              :rules="passwordRules"
              layout="vertical"
              class="password-form"
            >
              <a-form-item label="当前密码" name="current_password">
                <a-input-password
                  v-model:value="passwordForm.current_password"
                  placeholder="请输入当前密码"
                />
              </a-form-item>

              <a-form-item label="新密码" name="new_password">
                <a-input-password
                  v-model:value="passwordForm.new_password"
                  placeholder="请输入新密码"
                />
              </a-form-item>

              <a-form-item label="确认新密码" name="confirm_password">
                <a-input-password
                  v-model:value="passwordForm.confirm_password"
                  placeholder="请再次输入新密码"
                />
              </a-form-item>

              <a-form-item>
                <a-space>
                  <a-button
                    type="primary"
                    @click="changePassword"
                    :loading="loading.password"
                  >
                    修改密码
                  </a-button>
                  <a-button @click="resetPasswordForm">重置</a-button>
                </a-space>
              </a-form-item>
            </a-form>
          </a-card>
        </a-col>

        <!-- 右侧：统计信息 -->
        <a-col :xs="24" :md="10">
          <!-- 使用统计 -->
          <a-card title="使用统计" class="stats-card">
            <a-spin :spinning="loading.stats">
              <div class="stats-grid">
                <div class="stat-item">
                  <div class="stat-icon">
                    <MessageOutlined />
                  </div>
                  <div class="stat-content">
                    <div class="stat-value">{{ stats.total_messages || 0 }}</div>
                    <div class="stat-label">总消息数</div>
                  </div>
                </div>

                <div class="stat-item">
                  <div class="stat-icon">
                    <ApiOutlined />
                  </div>
                  <div class="stat-content">
                    <div class="stat-value">{{ formatNumber(stats.total_tokens) || 0 }}</div>
                    <div class="stat-label">Token 使用量</div>
                  </div>
                </div>

                <div class="stat-item">
                  <div class="stat-icon">
                    <CommentOutlined />
                  </div>
                  <div class="stat-content">
                    <div class="stat-value">{{ stats.total_chats || 0 }}</div>
                    <div class="stat-label">对话次数</div>
                  </div>
                </div>

                <div class="stat-item">
                  <div class="stat-icon">
                    <CalendarOutlined />
                  </div>
                  <div class="stat-content">
                    <div class="stat-value">{{ stats.account_age_days || 0 }}</div>
                    <div class="stat-label">账户天数</div>
                  </div>
                </div>
              </div>
            </a-spin>
          </a-card>

          <!-- 存储空间 -->
          <a-card title="存储空间" class="storage-card">
            <a-spin :spinning="loading.storage">
              <div class="storage-info">
                <div class="storage-usage">
                  <a-progress
                    type="circle"
                    :percent="storageInfo.usage_percentage || 0"
                    :size="100"
                    :stroke-color="getStorageColor(storageInfo.usage_percentage)"
                  />
                </div>
                <div class="storage-details">
                  <div class="storage-item">
                    <span class="label">已使用:</span>
                    <span class="value">{{ storageInfo.used_mb || 0 }} MB</span>
                  </div>
                  <div class="storage-item">
                    <span class="label">总空间:</span>
                    <span class="value">{{ storageInfo.limit_mb || 1024 }} MB</span>
                  </div>
                  <div class="storage-item">
                    <span class="label">存储路径:</span>
                    <span class="value path">{{ formatPath(storageInfo.storage_path) }}</span>
                  </div>
                </div>
              </div>
            </a-spin>
          </a-card>

          <!-- 账户信息 -->
          <a-card title="账户信息" class="account-card">
            <div class="account-info">
              <div class="info-item">
                <span class="label">用户ID:</span>
                <span class="value">{{ profileForm.id }}</span>
              </div>
              <div class="info-item">
                <span class="label">角色:</span>
                <a-tag :color="getRoleColor(profileForm.role)">
                  {{ getRoleLabel(profileForm.role) }}
                </a-tag>
              </div>
              <div class="info-item">
                <span class="label">注册时间:</span>
                <span class="value">{{ formatTime(profileForm.created_at) }}</span>
              </div>
              <div class="info-item">
                <span class="label">最后登录:</span>
                <span class="value">{{ formatTime(profileForm.last_login) }}</span>
              </div>
            </div>
          </a-card>
        </a-col>
      </a-row>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  UserOutlined,
  UploadOutlined,
  MessageOutlined,
  ApiOutlined,
  CommentOutlined,
  CalendarOutlined
} from '@ant-design/icons-vue'
import { profileApi } from '@/apis/auth_api'

// 状态管理
const loading = reactive({
  profile: false,
  update: false,
  password: false,
  stats: false,
  storage: false
})

// 表单引用
const profileFormRef = ref()
const passwordFormRef = ref()

// 头像预览
const avatarPreview = ref('')

// 个人信息表单
const profileForm = reactive({
  id: '',
  username: '',
  display_name: '',
  email: '',
  avatar: '',
  role: '',
  created_at: '',
  last_login: '',
  updated_at: ''
})

// 密码修改表单
const passwordForm = reactive({
  current_password: '',
  new_password: '',
  confirm_password: ''
})

// 统计信息
const stats = reactive({
  total_messages: 0,
  total_tokens: 0,
  total_chats: 0,
  account_age_days: 0
})

// 存储信息
const storageInfo = reactive({
  used_mb: 0,
  limit_mb: 1024,
  usage_percentage: 0,
  storage_path: ''
})

// 表单验证规则
const profileRules = {
  display_name: [
    { max: 50, message: '显示名称不能超过50个字符' }
  ],
  email: [
    { type: 'email', message: '请输入有效的邮箱地址' }
  ]
}

const passwordRules = {
  current_password: [
    { required: true, message: '请输入当前密码' }
  ],
  new_password: [
    { required: true, message: '请输入新密码' },
    { min: 6, message: '密码长度至少6位' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码' },
    {
      validator: (rule, value) => {
        if (value !== passwordForm.new_password) {
          return Promise.reject('两次输入的密码不一致')
        }
        return Promise.resolve()
      }
    }
  ]
}

// 方法
const loadProfile = async () => {
  try {
    loading.profile = true
    const response = await profileApi.getProfile()
    if (response.success) {
      Object.assign(profileForm, response.data)
    } else {
      message.error(response.message || '获取个人信息失败')
    }
  } catch (error) {
    console.error('获取个人信息失败:', error)
    message.error('获取个人信息失败')
  } finally {
    loading.profile = false
  }
}

const loadStats = async () => {
  try {
    loading.stats = true
    const response = await profileApi.getStats()
    if (response.success) {
      Object.assign(stats, response.data)
    } else {
      message.error(response.message || '获取统计信息失败')
    }
  } catch (error) {
    console.error('获取统计信息失败:', error)
    message.error('获取统计信息失败')
  } finally {
    loading.stats = false
  }
}

const loadStorageInfo = async () => {
  try {
    loading.storage = true
    const response = await profileApi.getFileStorage()
    if (response.success) {
      Object.assign(storageInfo, response.data)
    } else {
      message.error(response.message || '获取存储信息失败')
    }
  } catch (error) {
    console.error('获取存储信息失败:', error)
    message.error('获取存储信息失败')
  } finally {
    loading.storage = false
  }
}

const updateProfile = async () => {
  try {
    await profileFormRef.value.validate()
    loading.update = true

    const profileData = {
      display_name: profileForm.display_name || null,
      email: profileForm.email || null,
      avatar: avatarPreview.value || profileForm.avatar || null
    }

    const response = await profileApi.updateProfile(profileData)
    if (response.success) {
      message.success('个人信息更新成功')
      Object.assign(profileForm, response.data)
      avatarPreview.value = ''
    } else {
      message.error(response.message || '更新个人信息失败')
    }
  } catch (error) {
    console.error('更新个人信息失败:', error)
    message.error('更新个人信息失败')
  } finally {
    loading.update = false
  }
}

const changePassword = async () => {
  try {
    await passwordFormRef.value.validate()
    loading.password = true

    const passwordData = {
      current_password: passwordForm.current_password,
      new_password: passwordForm.new_password
    }

    const response = await profileApi.changePassword(passwordData)
    if (response.success) {
      message.success('密码修改成功')
      resetPasswordForm()
    } else {
      message.error(response.message || '修改密码失败')
    }
  } catch (error) {
    console.error('修改密码失败:', error)
    message.error('修改密码失败')
  } finally {
    loading.password = false
  }
}

const beforeAvatarUpload = (file) => {
  const isJpgOrPng = file.type === 'image/jpeg' || file.type === 'image/png'
  if (!isJpgOrPng) {
    message.error('只能上传 JPG/PNG 格式的图片!')
    return false
  }
  const isLt2M = file.size / 1024 / 1024 < 2
  if (!isLt2M) {
    message.error('图片大小不能超过 2MB!')
    return false
  }

  // 转换为base64
  const reader = new FileReader()
  reader.onload = (e) => {
    avatarPreview.value = e.target.result
  }
  reader.readAsDataURL(file)

  return false // 阻止自动上传
}

const resetProfileForm = () => {
  loadProfile()
  avatarPreview.value = ''
}

const resetPasswordForm = () => {
  passwordForm.current_password = ''
  passwordForm.new_password = ''
  passwordForm.confirm_password = ''
}

// 工具方法
const formatNumber = (num) => {
  if (!num) return '0'
  return num.toLocaleString()
}

const formatTime = (timeStr) => {
  if (!timeStr) return '未知'
  return new Date(timeStr).toLocaleString('zh-CN')
}

const formatPath = (path) => {
  if (!path) return '未知'
  return path.length > 30 ? '...' + path.slice(-30) : path
}

const getRoleColor = (role) => {
  const colors = {
    superadmin: 'red',
    admin: 'orange',
    user: 'blue'
  }
  return colors[role] || 'default'
}

const getRoleLabel = (role) => {
  const labels = {
    superadmin: '超级管理员',
    admin: '管理员',
    user: '普通用户'
  }
  return labels[role] || '未知'
}

const getStorageColor = (percentage) => {
  if (percentage >= 90) return '#ff4d4f'
  if (percentage >= 70) return '#faad14'
  return '#52c41a'
}

// 初始化
onMounted(async () => {
  await Promise.all([
    loadProfile(),
    loadStats(),
    loadStorageInfo()
  ])
})
</script>

<style lang="less" scoped>
.profile-management {
  .header-section {
    margin-bottom: 24px;

    .header-content {
      .title {
        margin: 0 0 8px 0;
        font-size: 20px;
        font-weight: 600;
        color: #1e293b;
      }

      .description {
        margin: 0;
        color: #64748b;
        font-size: 14px;
      }
    }
  }

  .content-section {
    .profile-card,
    .stats-card,
    .storage-card,
    .account-card {
      margin-bottom: 16px;
      border-radius: 12px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);

      :deep(.ant-card-head) {
        border-bottom: 1px solid #f0f0f0;
        
        .ant-card-head-title {
          font-weight: 600;
          color: #1e293b;
        }
      }
    }

    .avatar-section {
      display: flex;
      align-items: center;
      gap: 16px;

      .avatar-actions {
        .avatar-hint {
          margin: 8px 0 0 0;
          font-size: 12px;
          color: #8b949e;
        }
      }
    }

    .form-hint {
      margin-top: 4px;
      font-size: 12px;
      color: #8b949e;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;

      .stat-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 16px;
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border-radius: 8px;

        .stat-icon {
          width: 40px;
          height: 40px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #3b82f6;
          color: white;
          border-radius: 8px;
          font-size: 16px;
        }

        .stat-content {
          .stat-value {
            font-size: 20px;
            font-weight: 600;
            color: #1e293b;
            line-height: 1;
          }

          .stat-label {
            font-size: 12px;
            color: #64748b;
            margin-top: 4px;
          }
        }
      }
    }

    .storage-info {
      display: flex;
      align-items: center;
      gap: 24px;

      .storage-usage {
        flex-shrink: 0;
      }

      .storage-details {
        flex: 1;

        .storage-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;

          &:last-child {
            margin-bottom: 0;
          }

          .label {
            font-size: 14px;
            color: #64748b;
          }

          .value {
            font-size: 14px;
            color: #1e293b;
            font-weight: 500;

            &.path {
              font-family: monospace;
              font-size: 12px;
            }
          }
        }
      }
    }

    .account-info {
      .info-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        padding-bottom: 12px;
        border-bottom: 1px solid #f0f0f0;

        &:last-child {
          margin-bottom: 0;
          padding-bottom: 0;
          border-bottom: none;
        }

        .label {
          font-size: 14px;
          color: #64748b;
        }

        .value {
          font-size: 14px;
          color: #1e293b;
          font-weight: 500;
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .profile-management {
    .content-section {
      .stats-grid {
        grid-template-columns: 1fr;
      }

      .storage-info {
        flex-direction: column;
        text-align: center;
        gap: 16px;
      }
    }
  }
}
</style> 