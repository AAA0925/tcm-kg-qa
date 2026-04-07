/**
 * 用户工具函数
 */

export function getUser() {
  const userStr = localStorage.getItem('user')
  return userStr ? JSON.parse(userStr) : null
}

export function getToken() {
  return localStorage.getItem('token')
}

export function isAdmin() {
  const user = getUser()
  return user && user.role === 'admin'
}

export function isLoggedIn() {
  return !!getToken()
}

export function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
}
