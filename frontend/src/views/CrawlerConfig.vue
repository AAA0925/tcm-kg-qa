<template>
  <div class="crawler-config-container">
    <el-container>
      <el-header>
        <h1>爬虫参数配置</h1>
      </el-header>
      <el-main>
        <el-card>
          <el-form :model="config" label-width="120px">
            <el-form-item label="数据源 URL">
              <el-input
                v-model="urlInput"
                placeholder="输入 URL，按回车添加"
                @keyup.enter="addUrl"
              />
              <div style="margin-top: 10px;">
                <el-tag
                  v-for="(url, index) in config.source_urls"
                  :key="index"
                  closable
                  @close="removeUrl(index)"
                  style="margin-right: 5px;"
                >
                  {{ url }}
                </el-tag>
              </div>
            </el-form-item>
            
            <el-form-item label="最大深度">
              <el-input-number v-model="config.max_depth" :min="1" :max="10" />
            </el-form-item>
            
            <el-form-item label="爬取间隔 (秒)">
              <el-input-number v-model="config.crawl_interval" :min="0" :max="10" />
            </el-form-item>
            
            <el-form-item label="超时时间 (秒)">
              <el-input-number v-model="config.timeout" :min="10" :max="300" />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="startCrawl">开始爬取</el-button>
              <el-button @click="resetConfig">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card v-if="taskId" style="margin-top: 20px;">
          <h3>当前任务状态</h3>
          <p>任务 ID: {{ taskId }}</p>
          <p>状态：{{ taskStatus }}</p>
          <el-progress :percentage="progress" />
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'CrawlerConfig',
  data() {
    return {
      config: {
        source_urls: [],
        max_depth: 3,
        crawl_interval: 1,
        timeout: 30,
        enabled: true
      },
      urlInput: '',
      taskId: null,
      taskStatus: 'pending',
      progress: 0
    }
  },
  methods: {
    addUrl() {
      if (this.urlInput.trim() && !this.config.source_urls.includes(this.urlInput.trim())) {
        this.config.source_urls.push(this.urlInput.trim())
        this.urlInput = ''
      }
    },
    removeUrl(index) {
      this.config.source_urls.splice(index, 1)
    },
    async startCrawl() {
      if (this.config.source_urls.length === 0) {
        this.$message.warning('请至少添加一个数据源 URL')
        return
      }

      try {
        const response = await axios.post('http://localhost:8000/api/crawler/tasks', this.config)
        this.taskId = response.data.task_id
        this.taskStatus = 'running'
        this.progress = 0
        this.$message.success('爬虫任务已启动')
        
        this.pollTaskStatus()
      } catch (error) {
        this.$message.error('启动失败：' + error.message)
      }
    },
    async pollTaskStatus() {
      const poll = async () => {
        try {
          const response = await axios.get(`http://localhost:8000/api/crawler/tasks/${this.taskId}`)
          this.taskStatus = response.data.status
          this.progress = Math.min(100, Math.floor((response.data.items_crawled / 100) * 100))
          
          if (this.taskStatus === 'running') {
            setTimeout(poll, 2000)
          }
        } catch (error) {
          console.error('轮询失败:', error)
        }
      }
      poll()
    },
    resetConfig() {
      this.config = {
        source_urls: [],
        max_depth: 3,
        crawl_interval: 1,
        timeout: 30,
        enabled: true
      }
    }
  }
}
</script>

<style scoped>
.crawler-config-container {
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
