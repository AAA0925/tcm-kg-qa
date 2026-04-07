import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'Login', component: () => import('@/views/Login.vue') },
  { path: '/', name: 'Home', component: () => import('@/views/Home.vue') },
  { path: '/qa', name: 'QA', component: () => import('@/views/QA.vue') },
  { path: '/kg-visual', name: 'KGVisual', component: () => import('@/views/KGVisual.vue') },
  { path: '/profile', name: 'Profile', component: () => import('@/views/Profile.vue'), meta: { requiresAuth: true } },
  { path: '/crawler-config', name: 'CrawlerConfig', component: () => import('@/views/CrawlerConfig.vue'), meta: { requiresAuth: true, role: 'admin' } },
  { path: '/data-management', name: 'DataManagement', component: () => import('@/views/DataManagement.vue'), meta: { requiresAuth: true, role: 'admin' } },
  { path: '/algorithm-config', name: 'AlgorithmConfig', component: () => import('@/views/AlgorithmConfig.vue'), meta: { requiresAuth: true, role: 'admin' } }
]

const router = createRouter({ history: createWebHistory(), routes })

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  
  // 如果访问登录页，直接放行
  if (to.path === '/login') {
    if (token) {
      // 已登录则跳转到首页
      next('/')
    } else {
      next()
    }
    return
  }
  
  // 检查是否需要认证
  if (to.meta.requiresAuth && !token) {
    next('/login')
    return
  }
  
  // 检查角色权限
  if (to.meta.role && to.meta.role !== user.role) {
    // 没有权限访问该页面，重定向到首页
    next('/')
    return
  }
  
  next()
})

export default router
