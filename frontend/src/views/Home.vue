<template>
  <div class="home-container">
    <el-container>
      <el-header>
        <h1>中医知识图谱问答系统</h1>
      </el-header>
      <el-main>
        <el-card class="welcome-card">
          <h2>欢迎使用</h2>
          <p>本系统提供以下功能：</p>
          <ul>
            <li>💬 智能问答 - 基于知识图谱的中医问答</li>
            <li>🔍 知识可视化 - 直观展示中医知识图谱</li>
          </ul>
          <el-button type="primary" size="large" @click="$router.push('/qa')">开始问答</el-button>
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<script>
export default {
  name: 'Home'
}
</script>

<style scoped>
.home-container {
  height: 100vh;
}
.el-header {
  background-color: #409EFF;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}
.el-main {
  background-color: #f0f2f5;
  display: flex;
  justify-content: center;
  align-items: center;
}
.welcome-card {
  width: 600px;
  text-align: center;
}
ul {
  list-style: none;
  padding: 0;
  margin: 20px 0;
}
li {
  margin: 15px 0;
  font-size: 16px;
}
</style>
