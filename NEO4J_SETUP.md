# Neo4j 数据库安装指南

## 方法一：使用 Docker（推荐）

### 步骤 1：启动 Docker Desktop
1. 在 Windows 中找到并打开 "Docker Desktop" 应用程序
2. 等待 Docker Desktop 完全启动（底部状态栏显示绿色）
3. 确认 Docker 正常运行：在 PowerShell 中执行 `docker ps`

### 步骤 2：启动 Neo4j 容器
```powershell
cd D:\Desktop\2026\tcm-kg-qa
docker-compose up -d
```

### 步骤 3：验证安装
```powershell
docker ps | Select-String "tcm-neo4j"
```

### 访问地址
- **Neo4j Browser**: http://localhost:7474
- **用户名**: neo4j
- **密码**: password

---

## 方法二：直接安装 Neo4j（无需 Docker）

### 步骤 1：下载 Neo4j
访问 https://neo4j.com/download-center/
选择 "Neo4j Desktop" 或 "Neo4j Community Server"

### 步骤 2：安装
1. 运行下载的安装程序
2. 按照安装向导完成安装
3. 设置密码为：`password`

### 步骤 3：启动 Neo4j
1. 打开 Neo4j Desktop
2. 创建新项目
3. 添加本地 Neo4j 实例
4. 点击启动按钮

### 步骤 4：修改配置
编辑 Neo4j 配置文件，确保以下配置：
```
dbms.security.auth_enabled=true
dbms.default_listen_address=0.0.0.0
```

---

## 初始化数据库

### 方式 1：通过 Neo4j Browser（推荐）

1. 打开浏览器访问 http://localhost:7474
2. 登录（用户名：neo4j，密码：password）
3. 首次登录会要求修改密码，可以改为相同的 `password`
4. 在查询框中执行：
   ```cypher
   :source neo4j/init.cypher
   ```
5. 然后执行示例数据：
   ```cypher
   :source neo4j/sample_data.cypher
   ```

### 方式 2：使用 Cypher Shell

```powershell
# 进入 Neo4j 安装目录
cd "C:\Program Files\Neo4j\bin"

# 执行初始化脚本
.\cypher-shell -u neo4j -p password -f "D:\Desktop\2026\tcm-kg-qa\neo4j\init.cypher"

# 执行示例数据
.\cypher-shell -u neo4j -p password -f "D:\Desktop\2026\tcm-kg-qa\neo4j\sample_data.cypher"
```

---

## 验证连接

### 测试后端连接
重启后端服务，查看日志：
```powershell
cd D:\Desktop\2026\tcm-kg-qa\backend
python -m uvicorn main:app --reload
```

如果看到以下日志表示连接成功：
```
INFO | Neo4j 连接成功
```

### 测试 API
```powershell
# 获取知识图谱统计
Invoke-RestMethod -Uri http://localhost:8000/api/kg/stats

# 查询实体
Invoke-RestMethod -Uri "http://localhost:8000/api/kg/entities/感冒"
```

---

## 常用 Cypher 查询

### 查看所有节点和关系
```cypher
MATCH (n)-[r]-(m)
RETURN n, r, m
LIMIT 100;
```

### 查看特定病症的信息
```cypher
MATCH (d:Disease {name: '感冒'})-[r]-(related)
RETURN d, r, related;
```

### 查看中药推荐
```cypher
MATCH (d:Disease {name: '感冒'})-[:RECOMMEND_HERB]->(h:Herb)
RETURN h.name, h.effects;
```

### 查看处方组成
```cypher
MATCH (p:Prescription {name: '银翘散'})-[:CONTAINS_HERB]->(h:Herb)
RETURN h.name, h.effects;
```

---

## 故障排查

### 问题 1：Docker 无法启动
**解决**：
- 确保 Docker Desktop 已启动
- 检查 Hyper-V 是否启用
- 重启 Docker Desktop

### 问题 2：端口被占用
**解决**：
```powershell
# 查看端口占用
netstat -ano | findstr :7687
netstat -ano | findstr :7474

# 停止占用端口的进程
taskkill /PID <进程 ID> /F
```

### 问题 3：后端无法连接 Neo4j
**解决**：
1. 检查 Neo4j 是否运行：`docker ps`
2. 检查配置文件 `.env` 中的连接信息
3. 查看后端日志中的详细错误信息

---

## 下一步

Neo4j 安装完成后：
1. ✅ 执行初始化脚本创建约束和索引
2. ✅ 导入示例数据
3. ✅ 重启后端服务
4. ✅ 在前端访问"知识可视化"页面查看图谱
5. ✅ 测试问答功能

祝您安装顺利！🎉
