# 中医知识图谱可视化系统 Bug 修复文档

## 📋 修复记录概览

| 日期 | 修复内容 | 影响范围 | 优先级 |
|------|---------|---------|--------|
| 2026-04-05 | Neo4j 关系查询返回0条 | 后端核心查询 | 🔴 高 |
| 2026-04-05 | 节点点击展开功能404 | 前后端API对接 | 🔴 高 |
| 2026-04-05 | 节点点击无反应 | 前端状态更新 | 🟡 中 |
| 2026-04-05 | 图例颜色不一致 | 前端UI渲染 | 🟢 低 |
| 2026-04-05 | 模糊搜索控制 | 用户体验优化 | 🟡 中 |
| 2026-04-05 | 实体类型筛选动态更新 | 交互体验优化 | 🟡 中 |

---

## 🔴 Bug 1: 关系查询返回0条（核心问题）

### 问题描述
搜索"心阴虚"时，系统显示关系数为0，节点之间没有连线。但通过 Neo4j 浏览器查询确认，数据库中存在12条关系（4个 TREATED_BY_PRESCRIPTION + 8个 HAS_SYMPTOM）。

### 错误现象
```
前端显示：节点数 13，关系数 0
后端日志：实体 '心阴虚' 没有直接关系，尝试模糊匹配...
```

### 根本原因分析

#### 1. 第一次尝试：添加模糊匹配
最初误以为是没有直接关系，添加了模糊匹配逻辑，但实际数据库中**有直接关系**。

#### 2. 第二次尝试：添加调试代码
创建多个调试脚本验证：
- `check_xinyinxu.py` - 确认数据库有关系
- `check_relations.py` - 直接用 Cypher 查询，返回12条关系
- `debug_query.py` - 调试 Neo4j 驱动返回值

#### 3. 关键发现
通过 `debug_query.py` 输出发现：
```
记录 1:
  r = <Relationship element_id='...' nodes=(...) type='TREATED_BY_PRESCRIPTION' properties={}>
  r type = <class 'abc.TREATED_BY_PRESCRIPTION'>
  r.type = TREATED_BY_PRESCRIPTION
```
**关系对象确实存在，且有正确的 type 属性！**

但后端日志显示：
```
DEBUG | app.services.kg.neo4j_client:query_by_entity:69 - 记录: n=心阴虚, m=通脉养心丸, r=None
```

#### 4. 问题根源
**Python 字节码缓存问题** + **对象判断逻辑不当**

原有代码：
```python
# ❌ 错误的判断方式
if node_n and node_m and rel_r:
    # 处理关系
```

问题：
1. Neo4j Python 驱动返回的关系对象在某些情况下，虽然存在但可能被视为"假值"
2. Python 的 `__pycache__` 缓存了旧的 `.pyc` 文件，导致新代码未生效

### 修复方案

#### 修改文件：`backend/app/services/kg/neo4j_client.py`

```python
# ✅ 修复后的代码
def query_by_entity(self, entity_name: str, enable_fuzzy: bool = False) -> List[Dict]:
    # ... 前面代码 ...
    
    for record in result:
        node_n = record['n']
        node_m = record['m']
        rel_r = record['r']
        
        # ✅ 明确使用 is not None 判断
        if node_n is not None and node_m is not None and rel_r is not None:
            labels_n = list(node_n.labels)
            labels_m = list(node_m.labels)
            
            results.append({
                'n': {
                    'name': node_n.get('name'),
                    'category': labels_n[0] if labels_n else 'Concept'
                },
                'm': {
                    'name': node_m.get('name'),
                    'category': labels_m[0] if labels_m else 'Concept'
                },
                'r': {
                    'type': rel_r.type
                }
            })
```

#### 清理缓存
```powershell
# 删除所有 __pycache__ 目录
Get-ChildItem -Path . -Filter __pycache__ -Recurse -Directory | Remove-Item -Recurse -Force

# 重启后端服务
Get-Process python | Stop-Process -Force
python main.py
```

### 验证结果
```
✅ 心阴虚查询成功：返回 12 条记录
✅ 前端显示：节点数 13，关系数 12
✅ 图谱显示：心阴虚为中心，连接 8个症状 + 4个方剂
```

---

## 🔴 Bug 2: 节点点击展开功能 404 错误

### 问题描述
点击节点时报错：
```
POST /api/kg/expand/%E9%80%9A%E8%84%89%E5%85%BB%E5%BF%83%E4%B8%B8?depth=1&limit=50 HTTP/1.1" 404 Not Found
```

### 根本原因
后端缺少 `/api/kg/expand/{entity_name}` 端点

### 修复方案

#### 1. 添加 API 端点
**文件：** `backend/app/api/kg_management.py`

```python
@router.post("/expand/{entity_name}")
async def expand_entity_relations(entity_name: str, depth: int = 1, limit: int = 50):
    try:
        results = kg_client.expand_entity(entity_name, depth, limit)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### 2. 实现后端方法
**文件：** `backend/app/services/kg/neo4j_client.py`

```python
def expand_entity(self, entity_name: str, depth: int = 1, limit: int = 50) -> List[Dict]:
    """展开实体的关联节点"""
    if not self.connected:
        logger.warning("Neo4j 未连接，无法展开")
        return []
    
    with self.driver.session() as session:
        if depth == 1:
            cypher = """
            MATCH (n {name: $name})-[r]-(m)
            RETURN n, r, m
            LIMIT $limit
            """
        else:
            cypher = """
            MATCH path = (n {name: $name})-[*1..$depth]-(m)
            WITH n, m, relationships(path) as rels
            UNWIND rels as r
            RETURN n, r, m
            LIMIT $limit
            """
        
        logger.info(f"展开实体: {entity_name}, depth={depth}")
        result = session.run(cypher, name=entity_name, depth=depth, limit=limit)
        
        results = []
        seen = set()
        for record in result:
            node_n = record['n']
            node_m = record['m']
            rel_r = record['r']
            
            # ✅ 使用 is not None 判断
            if node_n is not None and node_m is not None and rel_r is not None:
                labels_n = list(node_n.labels)
                labels_m = list(node_m.labels)
                
                edge_key = f"{node_n.get('name')}->{node_m.get('name')}:{rel_r.type}"
                if edge_key not in seen:
                    seen.add(edge_key)
                    results.append({
                        'n': {
                            'name': node_n.get('name'),
                            'category': labels_n[0] if labels_n else 'Concept'
                        },
                        'm': {
                            'name': node_m.get('name'),
                            'category': labels_m[0] if labels_m else 'Concept'
                        },
                        'r': {
                            'type': rel_r.type
                        }
                    })
        
        logger.info(f"展开实体 '{entity_name}' 返回 {len(results)} 条记录")
        return results
```

### 验证结果
```
✅ 后端日志：展开实体 '心阴虚', depth=1 → 返回 12 条记录
✅ 前端：点击节点不再报404错误
```

---

## 🟡 Bug 3: 节点点击展开后无变化

### 问题描述
点击节点后，虽然不再报404错误，但图谱没有任何变化，节点和关系数量不变。

### 根本原因
前端 `expandNode` 方法中：
1. 新添加的节点缺少 `symbolSize` 和 `itemStyle` 属性
2. 调用 `updateChartDisplay()` 时没有传递 categories 参数
3. 缺少新增节点/关系的提示信息

### 修复方案

**文件：** `frontend/src/views/KGVisual.vue`

```javascript
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
    const newCategories = new Set() // ✅ 收集新增的实体类型
    
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
          symbolSize: this.getNodeSize(category),  // ✅ 添加节点大小
          itemStyle: {
            color: this.colorMap[category] || '#999'  // ✅ 添加颜色
          }
        })
        existingNames.add(item.n.name)
        newNodesCount++
        newCategories.add(category)  // ✅ 收集实体类型
      }
      
      // ... 目标节点类似处理 ...
      
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
    
    // ✅ 更新可用实体类型列表（添加新发现的类型）
    let addedNewCategories = false
    newCategories.forEach(cat => {
      if (!this.availableCategories.includes(cat)) {
        this.availableCategories.push(cat)
        addedNewCategories = true
      }
    })
    
    // ✅ 如果有新类型，自动添加到选中列表
    if (addedNewCategories) {
      this.selectedCategories = [...this.availableCategories]
    }
    
    // ✅ 应用筛选逻辑
    if (this.selectedCategories.length > 0) {
      this.applyCategoryFilter()
    } else {
      const allCategories = [...new Set(this.currentNodes.map(n => n.category))]
      this.updateChartDisplay(allCategories)
    }
    
    // ✅ 友好的提示信息
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
}
```

### 验证结果
```
✅ 点击"心阴虚" → 展开 12 个节点，12 条关系
✅ 点击"通脉养心丸" → 展开关联的草药（Herb）
✅ 提示：展开成功：新增 X 个节点，Y 条关系，发现 Z 种新实体类型
```

---

## 🟢 Bug 4: 图例颜色与节点颜色不一致

### 问题描述
图谱中的节点颜色和左上角图例显示的颜色不匹配。

### 根本原因
ECharts 的 legend 配置中，`categories` 数组没有为每个类别设置 `itemStyle` 颜色。

### 修复方案

**文件：** `frontend/src/views/KGVisual.vue`

```javascript
updateChartDisplay(categories = []) {
  if (categories.length === 0) {
    categories = [...new Set(this.currentNodes.map(n => n.category))]
  }
  
  // ✅ 为每个 category 设置颜色
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
      categories: categoryList,  // ✅ 使用带颜色的 categoryList
      data: this.currentNodes,
      links: this.currentLinks
    }]
  })
  
  this.nodeCount = this.currentNodes.length
  this.linkCount = this.currentLinks.length
  this.categoryCount = categories.length
}
```

### 验证结果
```
✅ 图例：Disease（红色）→ 节点：红色
✅ 图例：Symptom（青色）→ 节点：青色
✅ 图例：Prescription（蓝色）→ 节点：蓝色
```

---

## 🟡 功能增强 1: 模糊搜索开关

### 需求描述
用户希望添加一个复选框，控制是否启用模糊搜索：
- **不勾选**（默认）：只有在没有直接关系时才触发模糊匹配
- **勾选**：即使有直接关系也进行模糊匹配

### 实现方案

#### 1. 前端添加复选框

**文件：** `frontend/src/views/KGVisual.vue`

```vue
<!-- 搜索选项 -->
<el-row :gutter="20" style="margin-top: 15px;" align="middle">
  <el-col :span="12">
    <el-checkbox v-model="enableFuzzySearch">
      启用模糊搜索（有直接关系时也进行模糊匹配）
    </el-checkbox>
  </el-col>
  <!-- ... 实体类型筛选 ... -->
</el-row>
```

#### 2. 前端传递参数

```javascript
async searchEntity() {
  // ...
  const response = await axios.get(
    `http://localhost:8000/api/kg/entities/${encodeURIComponent(this.searchKeyword)}?enable_fuzzy=${this.enableFuzzySearch}`
  )
  // ...
}
```

#### 3. 后端接收参数

**文件：** `backend/app/api/kg_management.py`

```python
@router.get("/entities/{entity_name}")
async def get_entity_relations(entity_name: str, enable_fuzzy: bool = False):
    try:
        results = kg_client.query_by_entity(entity_name, enable_fuzzy)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### 4. 后端查询逻辑

**文件：** `backend/app/services/kg/neo4j_client.py`

```python
def query_by_entity(self, entity_name: str, enable_fuzzy: bool = False) -> List[Dict]:
    # ... 第一步：查询直接关系 ...
    
    # ✅ 第二步：模糊匹配逻辑
    should_do_fuzzy = (not results) or enable_fuzzy
    
    if should_do_fuzzy:
        if enable_fuzzy and results:
            logger.info(f"实体 '{entity_name}' 启用了模糊搜索，进行扩展匹配...")
        else:
            logger.info(f"实体 '{entity_name}' 没有直接关系，尝试模糊匹配...")
        
        # ... 模糊匹配逻辑 ...
```

---

## 🟡 功能增强 2: 实体类型筛选动态更新

### 需求描述
搜索后会出现实体类型筛选下拉框，但展开节点时发现新实体类型后，筛选选项不会更新。

### 方案设计

| 方案 | 优点 | 缺点 | 选择 |
|------|------|------|------|
| 方案1：搜索前加载所有类型 | 用户一次性看到所有类型 | 需要额外API调用，可能加载无关数据 | ❌ |
| **方案2：展开时动态更新** | ✅ 按需加载，体验流畅，符合探索心智模型 | 无明显缺点 | ✅ |
| 方案3：混合方案 | 最完整 | 复杂度高 | ❌ |

### 实现方案

#### 1. 搜索时收集实体类型

```javascript
updateChart(data) {
  const nodes = []
  const links = []
  const nodeSet = new Set()
  const categories = new Set()
  
  data.forEach(item => {
    // ... 处理节点 ...
    categories.add(category)
  })
  
  this.currentNodes = nodes
  this.currentLinks = links
  
  // ✅ 更新可用实体类型列表
  const allCategories = Array.from(categories)
  allCategories.forEach(cat => {
    if (!this.availableCategories.includes(cat)) {
      this.availableCategories.push(cat)
    }
  })
  
  // 默认选中所有类型
  this.selectedCategories = allCategories
  
  this.updateChartDisplay(allCategories)
}
```

#### 2. 展开时动态添加新类型

```javascript
async expandNode(entityName) {
  // ... 前面代码 ...
  
  const newCategories = new Set() // ✅ 收集新增的实体类型
  
  newResults.forEach(item => {
    // ... 处理节点时 ...
    newCategories.add(category)
  })
  
  // ✅ 更新可用实体类型列表（添加新发现的类型）
  let addedNewCategories = false
  newCategories.forEach(cat => {
    if (!this.availableCategories.includes(cat)) {
      this.availableCategories.push(cat)
      addedNewCategories = true
    }
  })
  
  // ✅ 如果有新类型，自动添加到选中列表
  if (addedNewCategories) {
    this.selectedCategories = [...this.availableCategories]
  }
  
  // ... 后续代码 ...
}
```

#### 3. 重置时清除筛选状态

```javascript
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
  this.availableCategories = []  // ✅ 清除可用类型
  this.selectedCategories = []   // ✅ 清除选中状态
}
```

#### 4. 实体类型筛选方法

```javascript
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
}
```

---

## 📊 修复效果对比

### 修复前
| 功能 | 状态 | 问题 |
|------|------|------|
| 关系查询 | ❌ 失败 | 返回0条关系 |
| 节点展开 | ❌ 404错误 | 端点不存在 |
| 节点颜色 | ⚠️ 不一致 | 图例与节点颜色不匹配 |
| 模糊搜索 | ❌ 无法控制 | 总是触发 |
| 实体筛选 | ❌ 不支持 | 无筛选功能 |

### 修复后
| 功能 | 状态 | 效果 |
|------|------|------|
| 关系查询 | ✅ 成功 | 心阴虚返回12条关系 |
| 节点展开 | ✅ 正常 | 点击展开关联节点 |
| 节点颜色 | ✅ 一致 | 图例与节点颜色匹配 |
| 模糊搜索 | ✅ 可控 | 复选框控制开关 |
| 实体筛选 | ✅ 动态更新 | 展开时自动发现新类型 |

---

## 🔧 技术总结

### 1. Neo4j Python 驱动注意事项
```python
# ❌ 错误：使用真值判断
if rel_r:
    # 可能误判

# ✅ 正确：明确使用 is not None
if rel_r is not None:
    # 准确判断
```

### 2. Python 字节码缓存问题
```powershell
# 遇到代码更新未生效时，清理缓存
Get-ChildItem -Path . -Filter __pycache__ -Recurse -Directory | Remove-Item -Recurse -Force
```

### 3. ECharts 图例颜色配置
```javascript
// ✅ 为每个 category 设置 itemStyle
const categoryList = categories.map(cat => ({
  name: cat,
  itemStyle: {
    color: this.colorMap[cat] || '#999'
  }
}))
```

### 4. 前端状态管理最佳实践
```javascript
// ✅ 展开节点时同步更新多个状态
newCategories.forEach(cat => {
  if (!this.availableCategories.includes(cat)) {
    this.availableCategories.push(cat)
  }
})
```

---

## 📝 调试工具记录

### 创建的调试脚本

1. **check_xinyinxu.py** - 检查心阴虚的关系统计
2. **check_relations.py** - 直接使用 Cypher 查询心阴虚的关系
3. **debug_query.py** - 调试 Neo4j 查询结果的详细输出
4. **test_rel_bool.py** - 测试关系对象的布尔值判断

### 关键调试命令

```powershell
# 查看后端日志
Get-Content backend/logs/app.log -Tail 50

# 检查端口占用
netstat -ano | findstr :8000

# 强制终止 Python 进程
Get-Process python | Stop-Process -Force

# 清理 Python 缓存
Get-ChildItem -Path . -Filter __pycache__ -Recurse -Directory | Remove-Item -Recurse -Force
```

---

## ✅ 验证清单

- [x] 搜索"心阴虚" → 返回 13 个节点，12 条关系
- [x] 图谱显示：心阴虚为中心，连接 8个症状 + 4个方剂
- [x] 图例颜色与节点颜色一致
- [x] 点击节点 → 展开关联节点和关系
- [x] 展开后 → 自动发现新实体类型并添加到筛选列表
- [x] 模糊搜索开关 → 勾选后即使有关系也进行模糊匹配
- [x] 实体类型筛选 → 可以筛选显示的实体类型
- [x] 重置视图 → 清除所有数据和筛选状态

---

**文档生成时间：** 2026-04-05  
**修复人员：** AI Assistant  
**版本：** v1.0
