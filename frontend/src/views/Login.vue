<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2 class="login-title">中医知识图谱问答系统</h2>
      
      <el-tabs v-model="activeTab" class="login-tabs">
        <el-tab-pane label="登录" name="login">
          <el-form :model="loginForm" :rules="loginRules" ref="loginFormRef" label-width="80px">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="loginForm.username" placeholder="请输入用户名" />
            </el-form-item>
            
            <el-form-item label="密码" prop="password">
              <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" show-password @keyup.enter="handleLogin" />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" style="width: 100%" :loading="loading" @click="handleLogin">
                登录
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <el-tab-pane label="注册" name="register">
          <el-form :model="registerForm" :rules="registerRules" ref="registerFormRef" label-width="80px">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="registerForm.username" placeholder="请输入用户名" />
            </el-form-item>
            
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="registerForm.email" placeholder="请输入邮箱" />
            </el-form-item>
            
            <el-form-item label="密码" prop="password">
              <el-input v-model="registerForm.password" type="password" placeholder="请输入密码" show-password />
            </el-form-item>
            
            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input v-model="registerForm.confirmPassword" type="password" placeholder="请再次输入密码" show-password />
            </el-form-item>
            
            <el-form-item>
              <el-button type="success" style="width: 100%" :loading="loading" @click="handleRegister">
                注册
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script>
import axios from 'axios'
import request from '@/utils/request'

export default {
  name: 'Login',
  data() {
    const validateConfirmPassword = (rule, value, callback) => {
      if (value !== this.registerForm.password) {
        callback(new Error('两次输入的密码不一致'))
      } else {
        callback()
      }
    }
    
    return {
      activeTab: 'login',
      loading: false,
      loginForm: {
        username: '',
        password: ''
      },
      loginRules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 6, message: '密码长度至少 6 位', trigger: 'blur' }
        ]
      },
      registerForm: {
        username: '',
        email: '',
        password: '',
        confirmPassword: ''
      },
      registerRules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' },
          { min: 3, max: 20, message: '用户名长度 3-20 位', trigger: 'blur' }
        ],
        email: [
          { required: true, message: '请输入邮箱', trigger: 'blur' },
          { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 6, message: '密码长度至少 6 位', trigger: 'blur' }
        ],
        confirmPassword: [
          { required: true, message: '请再次输入密码', trigger: 'blur' },
          { validator: validateConfirmPassword, trigger: 'blur' }
        ]
      }
    }
  },
  methods: {
    async handleLogin() {
      try {
        await this.$refs.loginFormRef.validate()
        this.loading = true
        
        const response = await axios.post('http://localhost:8000/api/auth/login', {
          username: this.loginForm.username,
          password: this.loginForm.password
        })
        
        console.log('Login response:', response.data)
        console.log('User data:', response.data.user)
        
        // 保存 token 和用户信息
        localStorage.setItem('token', response.data.access_token)
        localStorage.setItem('user', JSON.stringify(response.data.user))
        
        // 验证保存的数据
        const savedUser = localStorage.getItem('user')
        console.log('Saved user string:', savedUser)
        
        this.$message.success('登录成功')
        
        // 跳转到首页
        this.$router.push('/')
        
        // 强制刷新页面以更新用户信息
        setTimeout(() => {
          window.location.reload()
        }, 100)
      } catch (error) {
        if (error.response?.status === 401) {
          this.$message.error('用户名或密码错误')
        } else {
          this.$message.error('登录失败：' + error.message)
        }
      } finally {
        this.loading = false
      }
    },
    
    async handleRegister() {
      try {
        await this.$refs.registerFormRef.validate()
        this.loading = true
        
        const { confirmPassword, ...registerData } = this.registerForm
        
        await request.post('http://localhost:8000/api/auth/register', registerData)
        
        this.$message.success('注册成功，请登录')
        this.activeTab = 'login'
        this.registerForm = {
          username: '',
          email: '',
          password: '',
          confirmPassword: ''
        }
      } catch (error) {
        if (error.response?.status === 400) {
          this.$message.error(error.response.data.detail || '注册失败')
        } else {
          this.$message.error('注册失败：' + error.message)
        }
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 450px;
  padding: 20px;
}

.login-title {
  text-align: center;
  color: #303133;
  margin-bottom: 30px;
  font-size: 24px;
}

.login-tabs {
  margin-top: 20px;
}
</style>
