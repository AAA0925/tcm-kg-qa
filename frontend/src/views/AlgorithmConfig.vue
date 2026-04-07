<template>
  <div class="algorithm-config-container">
    <el-container>
      <el-header>
        <h1>算法参数调整</h1>
      </el-header>
      <el-main>
        <el-card>
          <h3>问答模型参数</h3>
          <el-form :model="config" label-width="150px">
            <el-form-item label="推理模型层数">
              <el-slider v-model="config.gat_layers" :min="1" :max="10" :step="1" show-input />
            </el-form-item>
            
            <el-form-item label="注意力头数">
              <el-slider v-model="config.attention_heads" :min="1" :max="8" :step="1" show-input />
            </el-form-item>
            
            <el-form-item label="学习率">
              <el-input-number v-model="config.learning_rate" :step="0.001" :precision="3" :min="0.001" :max="0.1" />
            </el-form-item>
            
            <el-form-item label="Dropout 率">
              <el-slider v-model="config.dropout" :min="0" :max="1" :step="0.1" show-input />
            </el-form-item>
            
            <el-form-item label="批量大小">
              <el-select v-model="config.batch_size">
                <el-option label="16" :value="16" />
                <el-option label="32" :value="32" />
                <el-option label="64" :value="64" />
              </el-select>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="saveConfig">保存配置</el-button>
              <el-button @click="resetConfig">重置默认</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card style="margin-top: 20px;">
          <h3>当前配置效果</h3>
          <p>准确率：<strong>{{ performance.accuracy }}%</strong></p>
          <p>F1 分数：<strong>{{ performance.f1_score }}</strong></p>
          <p>平均响应时间：<strong>{{ performance.avg_response_time }}ms</strong></p>
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<script>
export default {
  name: 'AlgorithmConfig',
  data() {
    return {
      config: {
        gat_layers: 2,
        attention_heads: 4,
        learning_rate: 0.001,
        dropout: 0.1,
        batch_size: 32
      },
      performance: {
        accuracy: 85.5,
        f1_score: 0.82,
        avg_response_time: 120
      }
    }
  },
  methods: {
    saveConfig() {
      this.$message.success('配置已保存')
    },
    resetConfig() {
      this.config = {
        gat_layers: 2,
        attention_heads: 4,
        learning_rate: 0.001,
        dropout: 0.1,
        batch_size: 32
      }
    }
  }
}
</script>

<style scoped>
.algorithm-config-container {
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
