<template>
  <div id="app">
    <el-container v-if="$route.path !== '/login'">
      <el-aside width="200px" style="background-color: #304156; min-height: 100vh;">
        <div style="padding: 20px; color: white; font-size: 18px; font-weight: bold;">TCM-KG-QA</div>
        <el-menu
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
          :default-active="$route.path"
          router
        >
          <el-menu-item index="/">
            <span>🏠 首页</span>
          </el-menu-item>
          <el-menu-item index="/qa">
            <span>💬 智能问答</span>
          </el-menu-item>
          <el-menu-item index="/kg-visual">
            <span>🕸️ 知识可视化</span>
          </el-menu-item>
          <!-- 管理员专属菜单 -->
          <template v-if="userRole === 'admin'">
            <el-menu-item index="/crawler-config">
              <span>🕷️ 爬虫配置</span>
            </el-menu-item>
            <el-menu-item index="/data-management">
              <span>💾 数据管理</span>
            </el-menu-item>
            <el-menu-item index="/algorithm-config">
              <span>⚙️ 算法配置</span>
            </el-menu-item>
          </template>
        </el-menu>
      </el-aside>
      <el-container>
        <!-- 顶部用户信息栏 -->
        <el-header class="app-header">
          <el-dropdown @command="handleCommand" trigger="click">
            <span class="el-dropdown-link" style="cursor: pointer; display: flex; align-items: center;">
              <el-avatar :size="32" :src="userAvatar" icon="User" style="margin-right: 10px;" />
              <span>{{ user?.username || '用户' }}</span>
              <el-tag :type="userRole === 'admin' ? 'danger' : 'info'" size="small" style="margin-left: 10px;">
                {{ userRole === 'admin' ? '管理员' : '普通用户' }}
              </el-tag>
              <i class="el-icon-arrow-down el-icon--right" style="margin-left: 5px;"></i>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">👤 个人资料</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </el-header>
        <el-main style="padding: 0;">
          <router-view/>
        </el-main>
      </el-container>
    </el-container>
    <div v-else>
      <router-view/>
    </div>
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      userAvatar: '',
      currentUser: null
    }
  },
  created() {
    // 初始化时加载用户信息
    this.loadUser()
    
    // 监听 storage 事件 (跨标签页同步)
    window.addEventListener('storage', () => {
      this.loadUser()
    })
  },
  computed: {
    user() {
      return this.currentUser
    },
    userRole() {
      const role = this.currentUser?.role
      return role || 'user'
    }
  },
  methods: {
    loadUser() {
      const userStr = localStorage.getItem('user')
      if (userStr) {
        try {
          this.currentUser = JSON.parse(userStr)
          console.log('Loaded user:', this.currentUser)
          console.log('User role:', this.userRole)
        } catch (e) {
          console.error('Failed to parse user:', e)
          this.currentUser = null
        }
      } else {
        this.currentUser = null
      }
    },
    handleCommand(command) {
      console.log('Dropdown command:', command)
      if (command === 'logout') {
        this.logout()
      } else if (command === 'profile') {
        this.$router.push('/profile')
      }
    },
    logout() {
      this.$confirm('确认退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        // 清除本地存储
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        
        // 重置当前用户
        this.currentUser = null
        
        // 跳转到登录页
        this.$router.push('/login')
        
        this.$message.success('已退出登录')
      }).catch(() => {})
    }
  }
}
</script>

<style>
/* 全局重置，解决缩放溢出 */
* {
  box-sizing: border-box;
}

html, body {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  width: 100%;
  height: 100vh;
  overflow: hidden;
}

.el-container {
  width: 100%;
  height: 100%;
}

/* 侧边栏 */
.el-aside {
  min-width: 200px;
  overflow-y: auto;
  overflow-x: hidden;
}

/* 关键修复：允许右侧内容区收缩 */
.el-container > .el-container {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.app-header {
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding-right: 20px;
  overflow: hidden;
  white-space: nowrap;
}

.el-main {
  padding: 0;
  overflow-x: hidden;
  overflow-y: auto;
}
</style>
