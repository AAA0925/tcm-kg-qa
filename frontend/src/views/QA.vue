<template>
  <div class="qa-container">
    <el-container>
      <el-header>
        <h1>智能问答</h1>
      </el-header>
      <el-main>
        <el-card>
          <el-input
            v-model="question"
            type="textarea"
            :rows="3"
            placeholder="请输入您的问题，如'感冒有什么症状？'"
          />
          <el-row style="margin-top: 20px;">
            <el-button type="primary" @click="submitQuestion" :loading="loading">提问</el-button>
            <el-select v-model="topK" style="margin-left: 10px;">
              <el-option label="返回 5 条" :value="5" />
              <el-option label="返回 10 条" :value="10" />
              <el-option label="返回 20 条" :value="20" />
            </el-select>
          </el-row>
        </el-card>

        <el-card v-if="answer" style="margin-top: 20px;">
          <h3>回答结果</h3>
          <p>{{ answer.answer }}</p>
          <el-tag v-for="(entity, index) in answer.entities" :key="index" style="margin-right: 5px; margin-top: 5px;">
            {{ entity }}
          </el-tag>
          <div style="margin-top: 10px; color: #999; font-size: 12px;">
            置信度：{{ (answer.confidence * 100).toFixed(2) }}%
          </div>
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'QA',
  data() {
    return {
      question: '',
      topK: 5,
      loading: false,
      answer: null
    }
  },
  methods: {
    async submitQuestion() {
      if (!this.question.trim()) {
        this.$message.warning('请输入问题')
        return
      }

      this.loading = true
      try {
        const response = await axios.post('http://localhost:8000/api/qa/ask', {
          question: this.question,
          top_k: this.topK
        })
        this.answer = response.data
        this.$message.success('回答成功')
      } catch (error) {
        this.$message.error('回答失败：' + error.message)
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.qa-container {
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
