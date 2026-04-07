<template>
  <div class="kg-visual-container">
    <el-header>
      <h1>知识图谱可视化</h1>
    </el-header>
    <el-main>
      <!-- 搜索区域 -->
      <el-card class="search-card">
        <el-row :gutter="20" align="middle">
          <el-col :span="16">
            <el-input
              v-model="searchKeyword"
              placeholder="输入关键词，如：心阴虚、胃痛、香砂六君子汤..."
              size="large"
              @keyup.enter="searchEntity"
              clearable
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
              <template #append>
                <el-button type="primary" @click="searchEntity" :loading="loading">
                  <el-icon><Search /></el-icon>
                  搜索
                </el-button>
              </template>
            </el-input>
          </el-col>
          <el-col :span="8">
            <el-button @click="resetView" size="large">
              <el-icon><Refresh /></el-icon>
              重置视图
            </el-button>
            <el-button @click="exportData" size="large">
              <el-icon><Download /></el-icon>
              导出数据
            </el-button>
          </el-col>
        </el-row>
        
        <!-- 搜索选项 -->
        <el-row :gutter="20" style="margin-top: 15px;" align="middle">
          <el-col :span="12">
            <el-checkbox v-model="enableFuzzySearch">
              启用模糊搜索（有直接关系时也进行模糊匹配）
            </el-checkbox>
          </el-col>
          <el-col :span="12" v-if="availableCategories.length > 0">
            <el-select 
              v-model="selectedCategories" 
              multiple 
              collapse-tags 
              placeholder="筛选实体类型" 
              style="width: 100%;" 
              clearable
              @change="applyCategoryFilter"
            >
              <el-option
                v-for="cat in availableCategories"
                :key="cat"
                :label="cat"
                :value="cat"
              >
                <span style="float: left">{{ cat }}</span>
                <span style="float: right; color: #8492a6; font-size: 13px">
                  <el-tag :color="colorMap[cat]" size="small" style="margin-left: 5px">{{ cat }}</el-tag>
                </span>
              </el-option>
            </el-select>
          </el-col>
        </el-row>
        
        <!-- 搜索历史 -->
        <div v-if="searchHistory.length > 0" class="search-history">
          <span class="history-label">搜索历史：</span>
          <el-tag
            v-for="(keyword, index) in searchHistory"
            :key="index"
            size="small"
            closable
            @close="removeHistory(index)"
            @click="loadHistory(keyword)"
            class="history-tag"
          >
            {{ keyword }}
          </el-tag>
          <el-button link type="danger" size="small" @click="clearHistory">
            清空
          </el-button>
        </div>
      </el-card>

      <!-- 统计信息 -->
      <el-card v-if="currentNodes.length > 0" class="stats-card">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-statistic title="节点数" :value="nodeCount" />
          </el-col>
          <el-col :span="8">
            <el-statistic title="关系数" :value="linkCount" />
          </el-col>
          <el-col :span="8">
            <el-statistic title="实体类型" :value="categoryCount" />
          </el-col>
        </el-row>
      </el-card>

      <!-- ECharts 图表容器 -->
      <div ref="chartContainer" class="chart-container"></div>
      
      <!-- 加载提示 -->
      <div v-if="loading" class="loading-overlay">
        <el-icon class="is-loading" :size="40"><Loading /></el-icon>
        <p>正在查询知识图谱...</p>
      </div>
    </el-main>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import axios from 'axios'
import { Search, Refresh, Download, Loading } from '@element-plus/icons-vue'

export default {
  name: 'KGVisual',
  components: {
    Search,
    Refresh,
    Download,
    Loading
  },
  data() {
    return {
      searchKeyword: '',
      chart: null,
      loading: false,
      
      // 统计数据
      nodeCount: 0,
      linkCount: 0,
      categoryCount: 0,
      
      // 搜索历史
      searchHistory: [],
      
      // 当前图谱数据
      currentNodes: [],
      currentLinks: [],
      
      // 模糊搜索开关
      enableFuzzySearch: false,
      
      // 实体类型筛选
      availableCategories: [], // 所有可用的实体类型
      selectedCategories: [], // 选中的实体类型
      
      // 颜色映射（不同实体类型使用不同颜色）
      colorMap: {
        'Disease': '#FF6B6B',
        'Symptom': '#4ECDC4',
        'Prescription': '#45B7D1',
        'Herb': '#96CEB4',
        'Therapy': '#FFEAA7',
        'Syndrome': '#DDA0DD',
        'Classic': '#F38181',
        'Effect': '#AA96DA',
        'Meridian': '#FCBAD3',
        'WellnessMethod': '#FFFFD2',
        'Concept': '#A8E6CF'
      },
      
      // 实体类型中英文映射
      categoryMap: {
        'Disease': '疾病',
        'Symptom': '症状',
        'Prescription': '方剂',
        'Herb': '草药',
        'Therapy': '疗法',
        'Syndrome': '证候',
        'Classic': '经典',
        'Effect': '功效',
        'Meridian': '经络',
        'WellnessMethod': '养生方法',
        'Concept': '概念'
      },
      
      // 关系类型中英文映射
      relationMap: {
        'HAS_SYMPTOM': '有症状',
        'TREATED_BY_PRESCRIPTION': '治疗方剂',
        'CONTAINS_HERB': '包含草药',
        'HAS_EFFECT': '具有功效',
        'BELONGS_TO_MERIDIAN': '归经',
        'USED_FOR': '用于治疗',
        'PART_OF': '属于',
        'TREATS': '治疗',
        'CAUSES': '导致',
        'RELATED': '相关',
        'SUBCLASS_OF': '子类',
        'FROM_CLASSIC': '出自经典',
        'HAS_PROPERTY': '具有属性',
        'ISA': '是一种'
      }
    }
  },
  mounted() {
    this.initChart()
    this.loadSearchHistory()
    // 窗口大小改变时重新调整图表
    window.addEventListener('resize', this.handleResize)
  },
  methods: {
    handleResize() {
      if (this.chart) {
        this.chart.resize()
      }
    },
    
    initChart() {
      this.chart = echarts.init(this.$refs.chartContainer)
      
      const option = {
        tooltip: {
          trigger: 'item',
          formatter: (params) => {
            if (params.dataType === 'node') {
              // 使用 categoryMap 转换为中文
              const category = params.data.category || 'Concept'
              const categoryCN = this.categoryMap[category] || category
              return `
                <div style="padding: 5px;">
                  <strong>${params.name}</strong><br/>
                  <span style="color: #999;">类型：</span>${categoryCN}
                </div>
              `
            } else if (params.dataType === 'edge') {
              // 使用 relationMap 转换为中文
              const relationType = params.data.name || 'RELATED'
              const relationCN = this.relationMap[relationType] || relationType
              // 关系方向：source -> target 与箭头方向一致
              return `
                <div style="padding: 5px;">
                  <strong>${params.data.source} → ${params.data.target}</strong><br/>
                  <span style="color: #999;">关系：</span>${relationCN}
                </div>
              `
            }
            return ''
          }
        },
        legend: [{
          top: '10px',
          left: '10px',
          orient: 'vertical',
          data: [],
          textStyle: {
            fontSize: 12
          }
        }],
        series: [{
          type: 'graph',
          layout: 'force',
          data: [],
          links: [],
          categories: [],
          roam: true,
          draggable: true,
          label: {
            show: true,
            position: 'right',
            fontSize: 11,
            color: '#333',
            formatter: '{b}'
          },
          edgeSymbol: ['circle', 'arrow'],
          edgeSymbolSize: [4, 10],
          edgeLabel: {
            show: true,
            fontSize: 10,
            color: '#666',
            formatter: '{c}'
          },
          force: {
            repulsion: 800,
            edgeLength: [100, 250],
            gravity: 0.1,
            layoutAnimation: true
          },
          emphasis: {
            focus: 'adjacency',
            lineStyle: {
              width: 4,
              opacity: 0.8
            },
            itemStyle: {
              shadowBlur: 20,
              shadowColor: 'rgba(0, 0, 0, 0.3)'
            }
          },
          lineStyle: {
            width: 2,
            curveness: 0.2,
            opacity: 0.6
          },
          itemStyle: {
            borderColor: '#fff',
            borderWidth: 2,
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.2)'
          }
        }]
      }
      
      this.chart.setOption(option, true)
      
      // 点击节点展开关联
      this.chart.on('click', (params) => {
        if (params.dataType === 'node') {
          this.expandNode(params.name)
        }
      })
    },
    async searchEntity() {
      if (!this.searchKeyword.trim()) {
        this.$message.warning('请输入关键词')
        return
      }
      
      this.loading = true
      try {
        const response = await axios.get(
          `http://localhost:8000/api/kg/entities/${encodeURIComponent(this.searchKeyword)}?enable_fuzzy=${this.enableFuzzySearch}`
        )
        
        if (!response.data.results || response.data.results.length === 0) {
          this.$message.warning(`未找到与"${this.searchKeyword}"相关的实体`)
          this.resetView()
          return
        }
        
        this.updateChart(response.data.results)
        this.addToHistory(this.searchKeyword)
        this.$message.success(`找到 ${this.nodeCount} 个节点，${this.linkCount} 条关系`)
      } catch (error) {
        this.$message.error('搜索失败：' + (error.response?.data?.detail || error.message))
        console.error('搜索错误:', error)
      } finally {
        this.loading = false
      }
    },
    
    async expandNode(entityName) {
      this.loading = true
      try {
        const response = await axios.post(
          `http://localhost:8000/api/kg/expand/${encodeURIComponent(entityName)}?depth=1&limit=50`
        )
        
        const newResults = response.data.results || []
        if (newResults.length === 0) {
          this.$message.info('该节点没有更多关联')
          return
        }
        
        const existingNames = new Set(this.currentNodes.map(n => n.id))
        let newNodesCount = 0
        let newLinksCount = 0
        const newCategories = new Set() // 收集新增的实体类型
        
        newResults.forEach(item => {
          // 处理源节点
          if (item.n && item.n.name && !existingNames.has(item.n.name)) {
            let category = item.n.category || 'Concept'
            if (Array.isArray(category)) {
              category = category[0] || 'Concept'
            }
            
            this.currentNodes.push({
              id: item.n.name,
              name: item.n.name,
              category: category,
              symbolSize: this.getNodeSize(category),
              itemStyle: {
                color: this.colorMap[category] || '#999'
              }
            })
            existingNames.add(item.n.name)
            newNodesCount++
            newCategories.add(category)
          }
          
          // 处理目标节点
          if (item.m && item.m.name && !existingNames.has(item.m.name)) {
            let category = item.m.category || 'Concept'
            if (Array.isArray(category)) {
              category = category[0] || 'Concept'
            }
            
            this.currentNodes.push({
              id: item.m.name,
              name: item.m.name,
              category: category,
              symbolSize: this.getNodeSize(category),
              itemStyle: {
                color: this.colorMap[category] || '#999'
              }
            })
            existingNames.add(item.m.name)
            newNodesCount++
            newCategories.add(category)
          }
          
          // 处理关系
          if (item.r && item.n && item.m) {
            this.currentLinks.push({
              source: item.n.name,
              target: item.m.name,
              name: item.r.type || 'RELATED',
              value: item.r.type || 'RELATED',
              lineStyle: {
                width: 2,
                curveness: 0.2
              }
            })
            newLinksCount++
          }
        })
        
        // 更新可用实体类型列表（添加新发现的类型）
        let addedNewCategories = false
        newCategories.forEach(cat => {
          if (!this.availableCategories.includes(cat)) {
            this.availableCategories.push(cat)
            addedNewCategories = true
          }
        })
        
        // 如果有新类型，自动添加到选中列表
        if (addedNewCategories) {
          this.selectedCategories = [...this.availableCategories]
        }
        
        // 应用筛选逻辑（使用选中的类型）
        if (this.selectedCategories.length > 0) {
          this.applyCategoryFilter()
        } else {
          const allCategories = [...new Set(this.currentNodes.map(n => n.category))]
          this.updateChartDisplay(allCategories)
        }
        
        if (newNodesCount > 0 || newLinksCount > 0) {
          let msg = `展开成功：新增 ${newNodesCount} 个节点，${newLinksCount} 条关系`
          if (addedNewCategories) {
            msg += `，发现 ${newCategories.size} 种新实体类型`
          }
          this.$message.success(msg)
        }
      } catch (error) {
        this.$message.error('展开节点失败：' + (error.response?.data?.detail || error.message))
        console.error('展开错误:', error)
      } finally {
        this.loading = false
      }
    },
    
    updateChart(data) {
      const nodes = []
      const links = []
      const nodeSet = new Set()
      const categories = new Set()
      
      data.forEach(item => {
        // 处理源节点
        if (item.n && item.n.name && !nodeSet.has(item.n.name)) {
          // 确保 category 是字符串，如果是数组则取第一个
          let category = item.n.category || 'Concept'
          if (Array.isArray(category)) {
            category = category[0] || 'Concept'
          }
          
          nodes.push({
            id: item.n.name,
            name: item.n.name,
            category: category,
            symbolSize: this.getNodeSize(category),
            itemStyle: {
              color: this.colorMap[category] || '#999'
            }
          })
          nodeSet.add(item.n.name)
          categories.add(category)
        }
        
        // 处理目标节点
        if (item.m && item.m.name && !nodeSet.has(item.m.name)) {
          // 确保 category 是字符串，如果是数组则取第一个
          let category = item.m.category || 'Concept'
          if (Array.isArray(category)) {
            category = category[0] || 'Concept'
          }
          
          nodes.push({
            id: item.m.name,
            name: item.m.name,
            category: category,
            symbolSize: this.getNodeSize(category),
            itemStyle: {
              color: this.colorMap[category] || '#999'
            }
          })
          nodeSet.add(item.m.name)
          categories.add(category)
        }
        
        // 处理关系
        if (item.r && item.n && item.m) {
          links.push({
            source: item.n.name,
            target: item.m.name,
            name: item.r.type || 'RELATED',
            value: item.r.type || 'RELATED',
            lineStyle: {
              width: 2,
              curveness: 0.2
            }
          })
        }
      })
      
      this.currentNodes = nodes
      this.currentLinks = links
      
      // 更新可用实体类型列表
      const allCategories = Array.from(categories)
      allCategories.forEach(cat => {
        if (!this.availableCategories.includes(cat)) {
          this.availableCategories.push(cat)
        }
      })
      
      // 默认选中所有类型
      this.selectedCategories = allCategories
      
      this.updateChartDisplay(allCategories)
    },
    
    getNodeSize(category) {
      // 根据节点类型设置不同大小
      const sizeMap = {
        'Disease': 50,
        'Symptom': 40,
        'Prescription': 45,
        'Herb': 35,
        'Therapy': 40,
        'Syndrome': 40,
        'Classic': 35,
        'Effect': 30,
        'Meridian': 35,
        'WellnessMethod': 35,
        'Concept': 30
      }
      return sizeMap[category] || 30
    },
    
    updateChartDisplay(categories = []) {
      if (categories.length === 0) {
        categories = [...new Set(this.currentNodes.map(n => n.category))]
      }
      
      // 为每个 category 设置颜色
      const categoryList = categories.map(cat => ({
        name: cat,
        itemStyle: {
          color: this.colorMap[cat] || '#999'
        }
      }))
      
      this.chart.setOption({
        legend: [{
          data: categories,
          textStyle: {
            fontSize: 12,
            color: '#333'
          }
        }],
        series: [{
          categories: categoryList,
          data: this.currentNodes,
          links: this.currentLinks
        }]
      })
      
      this.nodeCount = this.currentNodes.length
      this.linkCount = this.currentLinks.length
      this.categoryCount = categories.length
    },
    
    resetView() {
      this.chart.setOption({
        legend: [{
          data: [],
          selected: {}
        }],
        series: [{
          data: [],
          links: [],
          categories: []
        }]
      })
      this.currentNodes = []
      this.currentLinks = []
      this.nodeCount = 0
      this.linkCount = 0
      this.categoryCount = 0
      this.availableCategories = []
      this.selectedCategories = []
    },
    
    applyCategoryFilter() {
      // 根据选中的实体类型筛选节点和关系
      if (this.selectedCategories.length === 0) {
        // 如果没有选中任何类型，显示全部
        this.updateChartDisplay(this.availableCategories)
        return
      }
      
      // 筛选节点
      const filteredNodes = this.currentNodes.filter(node => 
        this.selectedCategories.includes(node.category)
      )
      const filteredNodeIds = new Set(filteredNodes.map(n => n.id))
      
      // 筛选关系（只保留两端节点都在筛选结果中的关系）
      const filteredLinks = this.currentLinks.filter(link => 
        filteredNodeIds.has(link.source) && filteredNodeIds.has(link.target)
      )
      
      // 更新图表显示
      this.chart.setOption({
        legend: [{
          data: this.selectedCategories,
          textStyle: {
            fontSize: 12,
            color: '#333'
          }
        }],
        series: [{
          categories: this.selectedCategories.map(cat => ({
            name: cat,
            itemStyle: {
              color: this.colorMap[cat] || '#999'
            }
          })),
          data: filteredNodes,
          links: filteredLinks
        }]
      })
      
      this.nodeCount = filteredNodes.length
      this.linkCount = filteredLinks.length
      this.categoryCount = this.selectedCategories.length
    },
    
    exportData() {
      const data = {
        nodes: this.currentNodes,
        links: this.currentLinks,
        timestamp: new Date().toISOString()
      }
      
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `kg-export-${Date.now()}.json`
      a.click()
      URL.revokeObjectURL(url)
      
      this.$message.success('数据已导出')
    },
    
    addToHistory(keyword) {
      if (!this.searchHistory.includes(keyword)) {
        this.searchHistory.unshift(keyword)
        if (this.searchHistory.length > 10) {
          this.searchHistory.pop()
        }
        localStorage.setItem('kgSearchHistory', JSON.stringify(this.searchHistory))
      }
    },
    
    loadSearchHistory() {
      const history = localStorage.getItem('kgSearchHistory')
      if (history) {
        this.searchHistory = JSON.parse(history)
      }
    },
    
    removeHistory(index) {
      this.searchHistory.splice(index, 1)
      localStorage.setItem('kgSearchHistory', JSON.stringify(this.searchHistory))
    },
    
    clearHistory() {
      this.searchHistory = []
      localStorage.removeItem('kgSearchHistory')
    },
    
    loadHistory(keyword) {
      this.searchKeyword = keyword
      this.searchEntity()
    }
  },
  beforeDestroy() {
    if (this.chart) {
      this.chart.dispose()
    }
  }
}
</script>

<style scoped>
.kg-visual-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f5f7fa;
}

.el-header {
  background-color: #409EFF;
  color: white;
  display: flex;
  align-items: center;
  padding: 0 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.el-header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 500;
}

.el-main {
  flex: 1;
  overflow: hidden;
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.search-card {
  margin-bottom: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.search-history {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #EBEEF5;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.history-label {
  font-size: 13px;
  color: #606266;
  font-weight: 500;
}

.history-tag {
  cursor: pointer;
  transition: all 0.3s;
}

.history-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.stats-card {
  margin-bottom: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.chart-container {
  flex: 1;
  width: 100%;
  min-height: 500px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.loading-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background-color: rgba(255, 255, 255, 0.95);
  padding: 30px 50px;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.loading-overlay p {
  margin-top: 15px;
  font-size: 14px;
  color: #606266;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .el-header h1 {
    font-size: 18px;
  }
  
  .search-card :deep(.el-row) {
    flex-direction: column;
  }
  
  .search-card :deep(.el-col) {
    width: 100%;
    margin-bottom: 10px;
  }
  
  .chart-container {
    min-height: 400px;
  }
}
</style>
