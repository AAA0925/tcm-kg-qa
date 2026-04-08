<template>
  <div class="qa-container">
    <div class="chat-header">
      <h2>🏥 中医智能问答助手</h2>
      <el-tag type="info" size="small">基于知识图谱 RAG 技术</el-tag>
    </div>

    <div class="chat-messages" ref="messageContainer">
      <div v-if="messages.length === 0" class="welcome-screen">
        <div class="welcome-icon">🤖</div>
        <h3>你好！我是中医知识图谱助手</h3>
        <p>我可以帮你解答中医疾病、症状、方剂、草药等问题</p>
        <div class="suggestions">
          <el-button @click="askSuggestion('心阴虚有什么症状？')" round size="small">心阴虚有什么症状？</el-button>
          <el-button @click="askSuggestion('胃痛怎么治疗？')" round size="small">胃痛怎么治疗？</el-button>
          <el-button @click="askSuggestion('人参有什么功效？')" round size="small">人参有什么功效？</el-button>
          <el-button @click="askSuggestion('感冒注意事项')" round size="small">感冒注意事项</el-button>
        </div>
      </div>

      <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.role]">
        <div class="message-avatar">{{ msg.role === 'user' ? '👤' : '🤖' }}</div>
        <div class="message-content">
          <div class="message-text" v-html="formatMessage(msg.content)"></div>
          <div v-if="msg.meta" class="message-meta">
            <el-tag v-if="msg.meta.entities && msg.meta.entities.length > 0" size="small" type="info">
              关联实体：{{ msg.meta.entities.join(', ') }}
            </el-tag>
          </div>
        </div>
      </div>

      <div v-if="loading" class="message ai">
        <div class="message-avatar">🤖</div>
        <div class="message-content">
          <div class="typing-indicator">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </div>

    <div class="chat-input">
      <el-input
        v-model="question"
        type="textarea"
        :rows="1"
        placeholder="请输入你的中医问题..."
        @keyup.enter.native="handleEnter"
        :disabled="loading"
        resize="none"
        class="input-box"
      />
      <el-button
        type="primary"
        :icon="loading ? '' : 'el-icon-s-promotion'"
        :loading="loading"
        @click="submitQuestion"
        :disabled="!question.trim() || loading"
        class="send-btn"
        circle
      >
      </el-button>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'QA',
  data() {
    return {
      question: '',
      loading: false,
      messages: []
    }
  },
  methods: {
    handleEnter(e) {
      if (!e.shiftKey) {
        e.preventDefault()
        this.submitQuestion()
      }
    },
    askSuggestion(text) {
      this.question = text
      this.submitQuestion()
    },
    async submitQuestion() {
      if (!this.question.trim() || this.loading) return

      const userMsg = this.question.trim()
      // 1. 立即将用户消息加入列表并清空输入框
      this.messages.push({ role: 'user', content: userMsg })
      this.question = ''
      this.loading = true

      this.$nextTick(() => {
        this.scrollToBottom()
      })

      try {
        const response = await axios.post('http://localhost:8000/api/qa/ask', {
          question: userMsg,
          top_k: 20
        })

        const aiMsg = {
          role: 'ai',
          content: response.data.answer,
          meta: {
            entities: response.data.entities
          }
        }
        this.messages.push(aiMsg)
      } catch (error) {
        this.messages.push({
          role: 'ai',
          content: '抱歉，回答失败：' + (error.response?.data?.detail || error.message),
          meta: null
        })
      } finally {
        this.loading = false
        this.$nextTick(() => {
          this.scrollToBottom()
        })
      }
    },
    scrollToBottom() {
      const container = this.$refs.messageContainer
      if (container) {
        container.scrollTop = container.scrollHeight
      }
    },
    formatMessage(text) {
      return text || ''
    }
  }
}
</script>

<style scoped>
.qa-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f7f7f8;
  min-height: 100vh;  /* 确保页面至少占满一个视口高度 */
}

.chat-header {
  background: white;
  padding: 20px;
  border-bottom: 1px solid #e5e5e5;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-header h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  overflow-x: hidden;
  max-height: calc(100vh - 160px);  /* 减去头部和输入框的高度 */
}

.welcome-screen {
  text-align: center;
  padding: 60px 20px;
  color: #666;
}

.welcome-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.welcome-screen h3 {
  margin: 10px 0;
  color: #333;
}

.suggestions {
  margin-top: 30px;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
}

.message {
  display: flex;
  margin-bottom: 20px;
  animation: fadeIn 0.3s;
  width: 100%;
  box-sizing: border-box;
  padding: 0 8px;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  min-width: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  background: #e5e5e5;
  margin-top: 4px;
}

.message.user .message-avatar {
  background: #409EFF;
}

.message-content {
  flex: 0 1 auto;
  max-width: 70%;
  min-width: 0;
  word-break: break-word;
  margin: 0 8px;
}

.message.user .message-content {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.message-text {
  background: white;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
  color: #333;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
  word-wrap: break-word;
  overflow-wrap: break-word;
  width: fit-content;
  max-width: 100%;
}

.message.user .message-text {
  background: #409EFF;
  color: white;
  border-top-right-radius: 4px;
}

.message.ai .message-text {
  border-top-left-radius: 4px;
}

.message-meta {
  margin-top: 8px;
  font-size: 12px;
  color: #999;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #999;
  border-radius: 50%;
  animation: bounce 1.4s infinite;
}

.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-8px); }
}

.chat-input {
  background: white;
  padding: 16px 20px;
  border-top: 1px solid #e5e5e5;
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-box {
  flex: 1;
}

.input-box :deep(textarea) {
  padding: 10px 12px;
  font-size: 14px;
}

.send-btn {
  width: 44px;
  height: 44px;
}
</style>
