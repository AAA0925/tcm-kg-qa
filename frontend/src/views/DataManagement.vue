<template>
  <div class="data-management-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <h2>数据管理</h2>
          <el-button type="primary" @click="refreshData" :loading="loading">刷新</el-button>
        </div>
      </template>

      <el-tabs v-model="activeTab" @tab-click="handleTabClick">
        <!-- 实体管理 -->
        <el-tab-pane label="实体管理" name="entities">
          <div class="toolbar">
            <el-input
              v-model="entitySearch"
              placeholder="搜索实体名称"
              clearable
              style="width: 300px; margin-right: 10px"
              @keyup.enter="loadEntities"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-select
              v-model="entityCategoryFilter"
              placeholder="筛选类型"
              clearable
              style="width: 200px; margin-right: 10px"
              @change="loadEntities"
            >
              <el-option
                v-for="type in entityTypes"
                :key="type"
                :label="type"
                :value="type"
              />
            </el-select>
            <el-button type="primary" @click="showAddEntityDialog">
              <el-icon><Plus /></el-icon>新增实体
            </el-button>
          </div>

          <el-table :data="entities" style="margin-top: 20px" stripe v-loading="loading">
            <el-table-column prop="name" label="名称" width="200" />
            <el-table-column prop="category" label="类型" width="150">
              <template #default="scope">
                <el-tag :type="getCategoryTagType(scope.row.category)">
                  {{ scope.row.category }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="描述" show-overflow-tooltip />
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="scope">
                <el-button size="small" type="primary" @click="showEditEntityDialog(scope.row)">
                  编辑
                </el-button>
                <el-button size="small" type="danger" @click="confirmDeleteEntity(scope.row)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination">
            <el-pagination
              v-model:current-page="entityPage"
              v-model:page-size="entityPageSize"
              :total="entityTotal"
              :page-sizes="[20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="loadEntities"
              @current-change="loadEntities"
            />
          </div>
        </el-tab-pane>

        <!-- 关系管理 -->
        <el-tab-pane label="关系管理" name="relations">
          <div class="toolbar">
            <el-input
              v-model="relationSearch"
              placeholder="搜索实体名称"
              clearable
              style="width: 200px; margin-right: 10px"
              @keyup.enter="loadRelations"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-select
              v-model="relationTypeFilter"
              placeholder="筛选关系类型"
              clearable
              style="width: 200px; margin-right: 10px"
              @change="loadRelations"
            >
              <el-option
                v-for="type in relationTypes"
                :key="type"
                :label="relationMap[type] || type"
                :value="type"
              />
            </el-select>
            <el-button type="primary" @click="showAddRelationDialog">
              <el-icon><Plus /></el-icon>新增关系
            </el-button>
          </div>

          <el-table :data="relations" style="margin-top: 20px" stripe v-loading="loading">
            <el-table-column prop="source_entity" label="源实体" width="200" />
            <el-table-column prop="source_type" label="源类型" width="120">
              <template #default="scope">
                <el-tag size="small">{{ scope.row.source_type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="relation_type" label="关系类型" width="180">
              <template #default="scope">
                <el-tag type="warning">{{ relationMap[scope.row.relation_type] || scope.row.relation_type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="target_type" label="目标类型" width="120">
              <template #default="scope">
                <el-tag size="small">{{ scope.row.target_type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="target_entity" label="目标实体" width="200" />
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="scope">
                <el-button size="small" type="primary" @click="showEditRelationDialog(scope.row)">
                  编辑
                </el-button>
                <el-button size="small" type="danger" @click="confirmDeleteRelation(scope.row)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination">
            <el-pagination
              v-model:current-page="relationPage"
              v-model:page-size="relationPageSize"
              :total="relationTotal"
              :page-sizes="[20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="loadRelations"
              @current-change="loadRelations"
            />
          </div>
        </el-tab-pane>

        <!-- 统计信息 -->
        <el-tab-pane label="统计信息" name="statistics">
          <el-row :gutter="20" style="margin-top: 20px">
            <el-col :span="8">
              <el-card shadow="hover">
                <template #header>
                  <div class="stat-header">
                    <el-icon color="#409EFF" size="24"><User /></el-icon>
                    <span>实体总数</span>
                  </div>
                </template>
                <div class="stat-number" style="color: #409EFF">{{ stats.entity_count || 0 }}</div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card shadow="hover">
                <template #header>
                  <div class="stat-header">
                    <el-icon color="#67C23A" size="24"><Connection /></el-icon>
                    <span>关系总数</span>
                  </div>
                </template>
                <div class="stat-number" style="color: #67C23A">{{ stats.relation_count || 0 }}</div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card shadow="hover">
                <template #header>
                  <div class="stat-header">
                    <el-icon color="#E6A23C" size="24"><Grid /></el-icon>
                    <span>实体类型数</span>
                  </div>
                </template>
                <div class="stat-number" style="color: #E6A23C">{{ entityTypes.length }}</div>
              </el-card>
            </el-col>
          </el-row>

          <el-row :gutter="20" style="margin-top: 20px">
            <el-col :span="12">
              <el-card>
                <template #header>实体类型分布</template>
                <div v-if="entityTypeStats.length > 0">
                  <div v-for="item in entityTypeStats" :key="item.name" class="type-stat-item">
                    <span>{{ item.name }}</span>
                    <el-progress :percentage="item.percentage" :stroke-width="8" />
                    <span class="type-stat-count">{{ item.count }}</span>
                  </div>
                </div>
                <el-empty v-else description="暂无数据" />
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card>
                <template #header>关系类型分布</template>
                <div v-if="relationTypeStats.length > 0">
                  <div v-for="item in relationTypeStats" :key="item.name" class="type-stat-item">
                    <span>{{ relationMap[item.name] || item.name }}</span>
                    <el-progress :percentage="item.percentage" :stroke-width="8" color="#67C23A" />
                    <span class="type-stat-count">{{ item.count }}</span>
                  </div>
                </div>
                <el-empty v-else description="暂无数据" />
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 实体对话框 -->
    <el-dialog
      v-model="entityDialogVisible"
      :title="isEditEntity ? '编辑实体' : '新增实体'"
      width="500px"
    >
      <el-form :model="entityForm" :rules="entityRules" ref="entityFormRef" label-width="80px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="entityForm.name" placeholder="请输入实体名称" :disabled="isEditEntity" />
        </el-form-item>
        <el-form-item label="类型" prop="category">
          <el-select v-model="entityForm.category" placeholder="请选择类型" filterable allow-create>
            <el-option
              v-for="type in entityTypes"
              :key="type"
              :label="type"
              :value="type"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="entityForm.description" type="textarea" :rows="3" placeholder="请输入描述（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="entityDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEntity" :loading="submitLoading">保存</el-button>
      </template>
    </el-dialog>

    <!-- 关系对话框 -->
    <el-dialog
      v-model="relationDialogVisible"
      :title="isEditRelation ? '编辑关系' : '新增关系'"
      width="600px"
    >
      <el-form :model="relationForm" :rules="relationRules" ref="relationFormRef" label-width="100px">
        <el-form-item label="源实体" prop="source_entity">
          <el-input v-model="relationForm.source_entity" placeholder="请输入源实体名称" :disabled="isEditRelation" />
        </el-form-item>
        <el-form-item label="关系类型" prop="relation_type">
          <el-select v-model="relationForm.relation_type" placeholder="请选择关系类型" filterable allow-create>
            <el-option
              v-for="type in relationTypes"
              :key="type"
              :label="relationMap[type] || type"
              :value="type"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="目标实体" prop="target_entity">
          <el-input v-model="relationForm.target_entity" placeholder="请输入目标实体名称" :disabled="isEditRelation" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="relationDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveRelation" :loading="submitLoading">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { Search, Plus, User, Connection, Grid } from '@element-plus/icons-vue'
import axios from 'axios'

export default {
  name: 'DataManagement',
  components: {
    Search,
    Plus,
    User,
    Connection,
    Grid
  },
  data() {
    return {
      activeTab: 'entities',
      loading: false,
      submitLoading: false,
      
      // 统计数据
      stats: {},
      
      // 实体相关
      entities: [],
      entityTotal: 0,
      entityPage: 1,
      entityPageSize: 20,
      entitySearch: '',
      entityCategoryFilter: '',
      entityTypes: [],
      
      // 关系相关
      relations: [],
      relationTotal: 0,
      relationPage: 1,
      relationPageSize: 20,
      relationSearch: '',
      relationTypeFilter: '',
      relationTypes: [],
      
      // 实体对话框
      entityDialogVisible: false,
      isEditEntity: false,
      entityFormRef: null,
      entityForm: {
        name: '',
        category: '',
        description: ''
      },
      entityRules: {
        name: [{ required: true, message: '请输入实体名称', trigger: 'blur' }],
        category: [{ required: true, message: '请选择实体类型', trigger: 'change' }]
      },
      
      // 关系对话框
      relationDialogVisible: false,
      isEditRelation: false,
      relationFormRef: null,
      relationForm: {
        source_entity: '',
        relation_type: '',
        target_entity: ''
      },
      relationRules: {
        source_entity: [{ required: true, message: '请输入源实体', trigger: 'blur' }],
        relation_type: [{ required: true, message: '请选择关系类型', trigger: 'change' }],
        target_entity: [{ required: true, message: '请输入目标实体', trigger: 'blur' }]
      },
      
      // 关系类型中英文映射
      relationMap: {
        'HAS_SYMPTOM': '有症状',
        'TREATS': '治疗',
        'TREATED_BY_PRESCRIPTION': '治疗方剂',
        'SUBCLASS_OF': '子类',
        'SUPERCLASS_OF': '父类',
        'FROM_CLASSIC': '出自经典',
        'HAS_EFFECT': '具有功效',
        'GENERATES': '生成',
        'CONTAINED_IN': '包含于',
        'COMMON_DRUG': '常用药',
        'DO_EAT': '宜吃',
        'NO_EAT': '忌吃',
        'RECOMMAND_DRUG': '推荐药物',
        'RECOMMAND_EAT': '推荐食物',
        'ACOMPANY_WITH': '并发症',
        'CURE_WAY': '治疗方式',
        'BELONGS_TO': '属于科室',
        'NEED_CHECK': '需要检查',
        'DRUGS_OF': '生产药品',
        'COMPOSED_OF': '由...组成',
        'BELONGS_TO_MERIDIAN': '归经',
        'HAS_PROPERTY': '具有性味',
        'CORRESPONDS_TO_SYNDROME': '对应证候',
        'TREATED_BY_THERAPY': '采用治法',
        'USES_METHOD': '采用方法',
        'HAS_OPERATION': '操作方法',
        'HAS_FREQUENCY': '使用频次',
        'HAS_CONTRAINT': '禁忌',
        'RELATED_TO_SEASON': '相关节气',
        'RELATED_TO_TIME': '时间相关',
        'CONCEPTUALLY_RELATED': '概念相关',
        'CONTAINS': '包含',
        'RELATED': '相关'
      }
    }
  },
  computed: {
    entityTypeStats() {
      if (!this.entities.length) return []
      const stats = {}
      this.entities.forEach(e => {
        stats[e.category] = (stats[e.category] || 0) + 1
      })
      const total = this.entities.length
      return Object.entries(stats)
        .map(([name, count]) => ({ name, count, percentage: Math.round(count / total * 100) }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 10)
    },
    relationTypeStats() {
      if (!this.relations.length) return []
      const stats = {}
      this.relations.forEach(r => {
        stats[r.relation_type] = (stats[r.relation_type] || 0) + 1
      })
      const total = this.relations.length
      return Object.entries(stats)
        .map(([name, count]) => ({ name, count, percentage: Math.round(count / total * 100) }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 10)
    }
  },
  mounted() {
    this.initData()
  },
  methods: {
    async initData() {
      await Promise.all([
        this.loadStatistics(),
        this.loadEntityTypes(),
        this.loadRelationTypes(),
        this.loadEntities(),
        this.loadRelations()
      ])
    },
    
    async refreshData() {
      this.loading = true
      try {
        await this.initData()
        this.$message.success('刷新成功')
      } catch (error) {
        this.$message.error('刷新失败')
      } finally {
        this.loading = false
      }
    },
    
    handleTabClick(tab) {
      if (tab.paneName === 'statistics') {
        this.loadStatistics()
      } else if (tab.paneName === 'entities') {
        this.loadEntities()
      } else if (tab.paneName === 'relations') {
        this.loadRelations()
      }
    },
    
    // 加载统计数据
    async loadStatistics() {
      try {
        const response = await axios.get('http://localhost:8000/api/kg/stats')
        this.stats = response.data
      } catch (error) {
        console.error('加载统计失败:', error)
      }
    },
    
    // 加载实体类型
    async loadEntityTypes() {
      try {
        const response = await axios.get('http://localhost:8000/api/kg/entity-types')
        this.entityTypes = response.data.types || []
      } catch (error) {
        console.error('加载实体类型失败:', error)
      }
    },
    
    // 加载关系类型
    async loadRelationTypes() {
      try {
        const response = await axios.get('http://localhost:8000/api/kg/relation-types')
        this.relationTypes = response.data.types || []
      } catch (error) {
        console.error('加载关系类型失败:', error)
      }
    },
    
    // 加载实体列表
    async loadEntities() {
      this.loading = true
      try {
        const offset = (this.entityPage - 1) * this.entityPageSize
        const params = {
          limit: this.entityPageSize,
          offset: offset
        }
        if (this.entityCategoryFilter) {
          params.category = this.entityCategoryFilter
        }
        const response = await axios.get('http://localhost:8000/api/kg/entities', { params })
        this.entities = response.data.entities || []
        this.entityTotal = response.data.total || 0
      } catch (error) {
        this.$message.error('加载实体列表失败')
        console.error(error)
      } finally {
        this.loading = false
      }
    },
    
    // 加载关系列表
    async loadRelations() {
      this.loading = true
      try {
        const offset = (this.relationPage - 1) * this.relationPageSize
        const params = {
          limit: this.relationPageSize,
          offset: offset
        }
        if (this.relationSearch) {
          params.source_entity = this.relationSearch
        }
        if (this.relationTypeFilter) {
          params.relation_type = this.relationTypeFilter
        }
        const response = await axios.get('http://localhost:8000/api/kg/relations', { params })
        this.relations = response.data.relations || []
        this.relationTotal = response.data.total || 0
      } catch (error) {
        this.$message.error('加载关系列表失败')
        console.error(error)
      } finally {
        this.loading = false
      }
    },
    
    // 显示新增实体对话框
    showAddEntityDialog() {
      this.isEditEntity = false
      this.entityForm = { name: '', category: '', description: '' }
      this.entityDialogVisible = true
      this.$nextTick(() => {
        this.$refs.entityFormRef?.clearValidate()
      })
    },
    
    // 显示编辑实体对话框
    showEditEntityDialog(row) {
      this.isEditEntity = true
      this.entityForm = {
        name: row.name,
        category: row.category,
        description: row.description || ''
      }
      this.entityDialogVisible = true
      this.$nextTick(() => {
        this.$refs.entityFormRef?.clearValidate()
      })
    },
    
    // 保存实体
    async saveEntity() {
      try {
        await this.$refs.entityFormRef.validate()
        this.submitLoading = true
        
        if (this.isEditEntity) {
          await axios.put(
            `http://localhost:8000/api/kg/entities/${encodeURIComponent(this.entityForm.name)}`,
            this.entityForm
          )
          this.$message.success('实体更新成功')
        } else {
          await axios.post('http://localhost:8000/api/kg/entities', this.entityForm)
          this.$message.success('实体创建成功')
        }
        
        this.entityDialogVisible = false
        await this.loadEntities()
        await this.loadStatistics()
      } catch (error) {
        if (error.response?.data?.detail) {
          this.$message.error(error.response.data.detail)
        } else {
          this.$message.error(this.isEditEntity ? '更新失败' : '创建失败')
        }
        console.error(error)
      } finally {
        this.submitLoading = false
      }
    },
    
    // 确认删除实体
    confirmDeleteEntity(row) {
      this.$confirm(`确定要删除实体"${row.name}"及其所有关系吗？`, '警告', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(async () => {
        try {
          await axios.delete(`http://localhost:8000/api/kg/entities/${encodeURIComponent(row.name)}`)
          this.$message.success('删除成功')
          await this.loadEntities()
          await this.loadStatistics()
        } catch (error) {
          this.$message.error('删除失败')
          console.error(error)
        }
      }).catch(() => {})
    },
    
    // 显示新增关系对话框
    showAddRelationDialog() {
      this.isEditRelation = false
      this.relationForm = { source_entity: '', relation_type: '', target_entity: '' }
      this.relationDialogVisible = true
      this.$nextTick(() => {
        this.$refs.relationFormRef?.clearValidate()
      })
    },
    
    // 显示编辑关系对话框
    showEditRelationDialog(row) {
      this.isEditRelation = true
      this.relationForm = {
        source_entity: row.source_entity,
        relation_type: row.relation_type,
        target_entity: row.target_entity
      }
      this.relationDialogVisible = true
      this.$nextTick(() => {
        this.$refs.relationFormRef?.clearValidate()
      })
    },
    
    // 保存关系
    async saveRelation() {
      try {
        await this.$refs.relationFormRef.validate()
        this.submitLoading = true
        
        if (this.isEditRelation) {
          const oldType = this.relationForm.relation_type
          // 获取原来的关系类型（编辑时不变）
          await axios.put(
            `http://localhost:8000/api/kg/relations/${encodeURIComponent(this.relationForm.source_entity)}/${encodeURIComponent(this.relationForm.target_entity)}/${encodeURIComponent(oldType)}`,
            this.relationForm
          )
          this.$message.success('关系更新成功')
        } else {
          await axios.post('http://localhost:8000/api/kg/relations', this.relationForm)
          this.$message.success('关系创建成功')
        }
        
        this.relationDialogVisible = false
        await this.loadRelations()
        await this.loadStatistics()
      } catch (error) {
        if (error.response?.data?.detail) {
          this.$message.error(error.response.data.detail)
        } else {
          this.$message.error(this.isEditRelation ? '更新失败' : '创建失败')
        }
        console.error(error)
      } finally {
        this.submitLoading = false
      }
    },
    
    // 确认删除关系
    confirmDeleteRelation(row) {
      this.$confirm(
        `确定要删除关系"${row.source_entity}" -[${row.relation_type}]-> "${row.target_entity}"吗？`,
        '警告',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(async () => {
        try {
          await axios.delete(
            `http://localhost:8000/api/kg/relations/${encodeURIComponent(row.source_entity)}/${encodeURIComponent(row.target_entity)}/${encodeURIComponent(row.relation_type)}`
          )
          this.$message.success('删除成功')
          await this.loadRelations()
          await this.loadStatistics()
        } catch (error) {
          this.$message.error('删除失败')
          console.error(error)
        }
      }).catch(() => {})
    },
    
    // 获取类型标签颜色
    getCategoryTagType(category) {
      const typeMap = {
        'Disease': 'danger',
        'Symptom': 'success',
        'Prescription': 'primary',
        'Herb': 'warning',
        'Therapy': 'info',
        'Syndrome': '',
        'Classic': 'danger',
        'Effect': 'warning',
        'Meridian': 'success',
        'WellnessMethod': 'info',
        'Concept': ''
      }
      return typeMap[category] || ''
    }
  }
}
</script>

<style scoped>
.data-management-container {
  padding: 20px;
  min-height: calc(100vh - 100px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  font-size: 20px;
}

.toolbar {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.stat-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 500;
}

.stat-number {
  font-size: 48px;
  font-weight: bold;
  text-align: center;
  margin-top: 10px;
}

.type-stat-item {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.type-stat-item span:first-child {
  min-width: 120px;
  font-size: 14px;
}

.type-stat-count {
  min-width: 40px;
  text-align: right;
  font-size: 14px;
  color: #909399;
}
</style>
