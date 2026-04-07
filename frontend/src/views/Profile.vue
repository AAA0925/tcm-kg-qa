<template>
  <div class="profile-container">
    <el-container>
      <el-header>
        <h1>个人资料</h1>
      </el-header>
      <el-main>
        <el-card style="max-width: 600px; margin: 20px auto;">
          <el-tabs v-model="activeTab">
            <!-- 基本信息 -->
            <el-tab-pane label="基本信息" name="basic">
              <el-form :model="profileForm" :rules="profileRules" ref="profileFormRef" label-width="100px">
                <el-form-item label="头像">
                  <div style="text-align: center;">
                    <el-avatar :size="100" :src="avatarUrl || defaultAvatar" style="margin-bottom: 20px;" />
                    <br />
                    <el-upload
                      action="#"
                      :http-request="uploadAvatar"
                      :show-file-list="false"
                      accept="image/*"
                    >
                      <el-button type="primary" size="small">更换头像</el-button>
                    </el-upload>
                  </div>
                </el-form-item>
                
                <el-form-item label="用户名" prop="username">
                  <el-input v-model="profileForm.username" placeholder="请输入用户名" />
                </el-form-item>
                
                <el-form-item label="邮箱" prop="email">
                  <el-input v-model="profileForm.email" placeholder="请输入邮箱" disabled />
                </el-form-item>
                
                <el-form-item label="角色">
                  <el-tag :type="userRole === 'admin' ? 'danger' : 'info'">
                    {{ userRole === 'admin' ? '管理员' : '普通用户' }}
                  </el-tag>
                </el-form-item>
                
                <el-form-item>
                  <el-button type="primary" @click="updateProfile" :loading="loading">保存修改</el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>
            
            <!-- 修改密码 -->
            <el-tab-pane label="修改密码" name="password">
              <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef" label-width="100px">
                <el-form-item label="当前密码" prop="oldPassword">
                  <el-input v-model="passwordForm.oldPassword" type="password" placeholder="请输入当前密码" show-password />
                </el-form-item>
                
                <el-form-item label="新密码" prop="newPassword">
                  <el-input v-model="passwordForm.newPassword" type="password" placeholder="请输入新密码" show-password />
                </el-form-item>
                
                <el-form-item label="确认密码" prop="confirmPassword">
                  <el-input v-model="passwordForm.confirmPassword" type="password" placeholder="请再次输入新密码" show-password />
                </el-form-item>
                
                <el-form-item>
                  <el-button type="success" @click="updatePassword" :loading="loading">修改密码</el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<script>
import axios from 'axios'
import { getToken } from '@/utils/auth'

export default {
  name: 'Profile',
  data() {
    const validateConfirmPassword = (rule, value, callback) => {
      if (value !== this.passwordForm.newPassword) {
        callback(new Error('两次输入的密码不一致'))
      } else {
        callback()
      }
    }
    
    return {
      activeTab: 'basic',
      loading: false,
      avatarUrl: '',
      defaultAvatar: '',
      profileForm: {
        username: '',
        email: ''
      },
      profileRules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' },
          { min: 3, max: 20, message: '用户名长度 3-20 位', trigger: 'blur' }
        ],
        email: [
          { required: true, message: '请输入邮箱', trigger: 'blur' },
          { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
        ]
      },
      passwordForm: {
        oldPassword: '',
        newPassword: '',
        confirmPassword: ''
      },
      passwordRules: {
        oldPassword: [
          { required: true, message: '请输入当前密码', trigger: 'blur' },
          { min: 6, message: '密码长度至少 6 位', trigger: 'blur' }
        ],
        newPassword: [
          { required: true, message: '请输入新密码', trigger: 'blur' },
          { min: 6, message: '密码长度至少 6 位', trigger: 'blur' }
        ],
        confirmPassword: [
          { required: true, message: '请再次输入新密码', trigger: 'blur' },
          { validator: validateConfirmPassword, trigger: 'blur' }
        ]
      }
    }
  },
  computed: {
    userRole() {
      const user = localStorage.getItem('user')
      return user ? JSON.parse(user).role : 'user'
    }
  },
  watch: {
    // 监听 activeTab 变化，确保表单正确显示
    activeTab(newVal) {
      console.log('Tab changed to:', newVal)
    }
  },
  created() {
    this.loadUserProfile()
  },
  methods: {
    async loadUserProfile() {
      try {
        console.log('Loading user profile...')
        const response = await axios.get('http://localhost:8000/api/auth/me', {
          headers: {
            'Authorization': `Bearer ${getToken()}`
          }
        })
        
        console.log('Loaded user profile:', response.data)
        this.profileForm.username = response.data.username
        this.profileForm.email = response.data.email
        this.$message.success('加载用户信息成功')
      } catch (error) {
        console.error('Load profile error:', error)
        if (error.response?.status === 401) {
          this.$message.error('登录已过期，请重新登录')
          setTimeout(() => {
            localStorage.removeItem('token')
            localStorage.removeItem('user')
            this.$router.push('/login')
          }, 1500)
        } else {
          this.$message.error('加载用户信息失败')
        }
      }
    },
    
    async uploadAvatar(file) {
      // 这里可以对接真实的文件上传接口
      // 暂时使用本地预览
      const reader = new FileReader()
      reader.onload = (e) => {
        this.avatarUrl = e.target.result
        // 实际项目中应该调用后端 API 上传
        this.$message.success('头像上传成功（暂未接入后端）')
      }
      reader.readAsDataURL(file.file)
    },
    
    async updateProfile() {
      try {
        if (!this.$refs.profileFormRef) {
          this.$message.error('表单未初始化')
          return
        }
        
        await this.$refs.profileFormRef.validate()
        this.loading = true
        
        const response = await axios.put('http://localhost:8000/api/auth/profile', {
          username: this.profileForm.username,
          email: this.profileForm.email
        }, {
          headers: { 'Authorization': `Bearer ${getToken()}` }
        })
        
        console.log('Profile updated:', response.data)
        
        // 更新本地存储的用户信息
        localStorage.setItem('user', JSON.stringify(response.data))
        
        // 通知 App.vue 更新用户信息 (通过事件或自定义事件)
        window.dispatchEvent(new Event('storage'))
        
        this.$message.success('资料更新成功')
        
        // 重新加载用户信息
        await this.loadUserProfile()
      } catch (error) {
        console.error('Update profile error:', error)
        this.$message.error('更新失败：' + (error.response?.data?.detail || error.message))
      } finally {
        this.loading = false
      }
    },
    
    async updatePassword() {
      try {
        await this.$refs.passwordFormRef.validate()
        this.loading = true
        
        await axios.put('http://localhost:8000/api/auth/password', {
          old_password: this.passwordForm.oldPassword,
          new_password: this.passwordForm.newPassword
        }, {
          headers: { 'Authorization': `Bearer ${getToken()}` }
        })
        
        this.$message.success('密码修改成功，请重新登录')
        this.passwordForm = {
          oldPassword: '',
          newPassword: '',
          confirmPassword: ''
        }
        
        // 延迟跳转到登录页
        setTimeout(() => {
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          this.$router.push('/login')
        }, 1500)
      } catch (error) {
        this.$message.error('修改失败：' + (error.response?.data?.detail || error.message))
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.profile-container {
  height: 100vh;
}
.el-header {
  background-color: #409EFF;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
}
.el-main {
  background-color: #f0f2f5;
}
</style>
