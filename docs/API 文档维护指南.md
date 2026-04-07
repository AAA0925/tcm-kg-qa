# API 文档自动化维护指南

## 📋 概述

本项目实现了 API 接口文档的自动化生成和维护机制，确保文档与代码保持同步。

## 🛠️ 工具组成

### 1. **API 文档生成器** (`backend/generate_api_docs.py`)

自动扫描所有 API 路由并生成 Markdown 格式的接口文档。

**功能特点**:
- ✅ 自动扫描 `backend/app/api/` 目录下所有 API 文件
- ✅ 提取路由信息（方法、路径、函数名、描述）
- ✅ 生成结构化的 Markdown 文档
- ✅ 智能检测文档变更
- ✅ 包含完整的实体类型和关系类型说明

**使用方法**:
```bash
# 在项目根目录执行
python backend/generate_api_docs.py
```

**输出位置**:
- 文档保存至：`docs/API 接口文档.md`

---

### 2. **Git Pre-commit Hook** (`.githooks/pre-commit`)

在 git commit 时自动检查 API 变更并更新文档。

**工作原理**:
1. 检测暂存区中是否包含 API 相关文件变更
   - `backend/app/api/` - API 路由定义
   - `backend/app/models/` - 数据模型
   - `backend/app/services/` - 服务层
2. 如果有变更，自动运行文档生成器
3. 将更新后的文档自动添加到暂存区

**监控范围**:
- API 路由新增、修改、删除
- 请求参数变更
- 响应格式变更
- 业务逻辑变更

---

## 📖 使用流程

### 方式一：手动生成（推荐用于主动更新）

```bash
# 1. 修改 API 代码后，手动运行生成器
python backend/generate_api_docs.py

# 2. 查看生成的文档
cat docs/API 接口文档.md

# 3. 提交代码和文档
git add .
git commit -m "feat: 添加新的 API 接口"
```

### 方式二：自动更新（Git Hook）

配置好 Git Hook 后，每次 commit 会自动检查并更新文档：

```bash
# 1. 修改 API 代码
# 2. 提交代码
git add .
git commit -m "feat: 更新用户认证接口"

# Pre-commit hook 会自动：
# - 检测 API 相关变更
# - 运行文档生成器
# - 更新 docs/API 接口文档.md
# - 将文档添加到暂存区

# 3. 推送到远程仓库
git push
```

---

## 🔧 配置说明

### Git Hook 配置

已自动配置，无需手动设置：

```bash
# 项目初始化时已执行
git config core.hooksPath .githooks
```

### 自定义监控路径

编辑 `.githooks/pre-commit` 文件中的 `api_files` 列表：

```python
api_files = [
    'backend/app/api/',      # API 路由
    'backend/app/models/',   # 数据模型
    'backend/app/services/'  # 服务层
]
```

---

## 📝 文档结构

生成的 API 文档包含以下部分：

1. **基本信息**
   - 版本号
   - 最后更新时间
   - 基础地址

2. **目录索引**
   - 按模块分类的超链接目录

3. **接口详情**
   - 请求方法和路径
   - 功能描述
   - 请求参数示例
   - 响应示例

4. **公共说明**
   - 错误响应格式
   - HTTP 状态码说明
   - 认证方式

5. **领域知识**
   - 实体类型说明
   - 关系类型说明

---

## 🎯 最佳实践

### ✅ 推荐做法

1. **开发新接口时**:
   ```python
   # 1. 在 API 函数中添加清晰的文档字符串
   @router.post("/example")
   async def create_example(data: ExampleCreate):
       """创建示例数据
       
       详细描述...
       """
       ...
   
   # 2. 提交代码前手动运行生成器
   python backend/generate_api_docs.py
   
   # 3. 补充完善文档中的参数和响应示例
   ```

2. **修改现有接口时**:
   - 及时更新文档字符串
   - 运行生成器更新文档
   - 手动补充参数和响应示例

3. **审查 Pull Request 时**:
   - 检查 API 变更是否有文档更新
   - 验证文档示例是否正确

---

### ❌ 避免做法

1. **不要手动编辑** `docs/API 接口文档.md` 的主体内容
   - 会被自动生成器覆盖
   - 仅可补充参数示例和响应示例

2. **不要忘记运行生成器**
   - Git Hook 只在 commit 时触发
   - 如果只运行不提交，需手动执行生成器

3. **不要忽略文档警告**
   - 如果生成器报错，及时修复
   - 确保文档能正常生成

---

## 🔍 故障排查

### 问题 1: Git Hook 未生效

**症状**: commit 时没有自动更新文档

**解决方案**:
```bash
# 检查 hook 配置
git config core.hooksPath

# 如果不是 .githooks，重新配置
git config core.hooksPath .githooks

# 检查文件权限（Linux/Mac）
chmod +x .githooks/pre-commit
```

---

### 问题 2: 文档生成失败

**症状**: 运行生成器时报错

**解决方案**:
```bash
# 检查 Python 环境
cd backend
python generate_api_docs.py

# 查看详细错误信息
# 通常是语法错误或导入问题
```

---

### 问题 3: 文档内容不完整

**症状**: 生成的文档缺少某些接口

**解决方案**:
1. 检查 API 文件是否使用了 `@router.*` 装饰器
2. 确认 API 文件在 `backend/app/api/` 目录下
3. 查看生成器输出日志，确认已扫描该文件

---

## 📊 统计信息

查看当前 API 接口数量：

```bash
python backend/generate_api_docs.py
```

输出示例：
```
✅ 共发现 6 个 API 模块
📄 文档已保存到：D:\Desktop\2026\tcm-kg-qa\docs\API 接口文档.md
```

---

## 🚀 自动化扩展

### 集成到 CI/CD

可以在 GitHub Actions 或其他 CI 工具中添加文档检查：

```yaml
# .github/workflows/api-docs.yml
name: API Docs Check

on:
  pull_request:
    paths:
      - 'backend/app/api/**'
      - 'backend/app/models/**'
      - 'backend/app/services/**'

jobs:
  check-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Generate API Docs
        run: python backend/generate_api_docs.py
      
      - name: Check for Changes
        run: |
          git diff --exit-code docs/API 接口文档.md || \
          echo "❌ API 文档需要同步更新"
```

---

## 📚 相关资源

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Markdown 语法指南](https://www.markdownguide.org/)
- [Git Hooks 官方文档](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks)

---

## 💡 总结

通过本自动化机制，我们实现了：

✅ **文档与代码同步** - API 变更时自动提醒更新文档  
✅ **减少人工成本** - 无需手动维护文档结构  
✅ **保证一致性** - 统一的文档格式和风格  
✅ **提高可维护性** - 新成员快速了解系统接口  

让我们一起维护高质量的 API 文档！📖✨
