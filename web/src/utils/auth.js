import { useUserStore } from '@/stores/user'

/**
 * 权限检查工具函数
 */

// 检查当前用户是否有管理员权限
export const checkAdminPermission = () => {
  const userStore = useUserStore()
  if (!userStore.isAdmin) {
    throw new Error('需要管理员权限')
  }
  return true
}

// 检查当前用户是否有超级管理员权限
export const checkSuperAdminPermission = () => {
  const userStore = useUserStore()
  if (!userStore.isSuperAdmin) {
    throw new Error('需要超级管理员权限')
  }
  return true
}

// 检查当前用户是否有用户权限（已登录）
export const checkUserPermission = () => {
  const userStore = useUserStore()
  if (!userStore.isLoggedIn) {
    throw new Error('需要用户权限')
  }
  return true
} 