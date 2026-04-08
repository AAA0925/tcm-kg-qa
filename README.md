# 🏥 基于知识图谱的中医知识问答系统

<div align="center">

**结合 Neo4j 知识图谱与大语言模型的智能中医问答平台**

[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)](https://www.python.org/)
[![Vue3](https://img.shields.io/badge/Vue-3.3+-green?style=flat-square&logo=vue.js)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-teal?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.18+-green?style=flat-square&logo=neo4j)](https://neo4j.com/)
[![License](https://img.shields.io/badge/License-MIT-red?style=flat-square)](LICENSE)

</div>

---

## 📖 项目简介

本项目是一个基于知识图谱与大语言模型（LLM）的智能中医问答系统，采用 RAG（Retrieval-Augmented Generation）技术，结合 Neo4j 图数据库的通义千问（Qwen）大模型，实现对中医疾病、症状、方剂、草药等知识的智能查询与问答。

系统支持用户通过自然语言提问，自动从知识图谱中检索相关信息，并由大模型生成结构化的专业回答，适用于中医学习、辅助诊断、养生保健等场景。

---

## ✨ 核心特性

### 🧠 智能问答
- **RAG 架构**：检索增强生成，确保回答基于真实知识图谱数据
- **意图识别**：自动识别用户问题意图（症状查询、治疗方法、功效作用等）
- **实体提取**：支持多模式实体识别（正则匹配、模糊搜索）
- **大模型集成**：集成通义千问（Qwen）提供自然语言生成能力

### 📊 知识图谱管理
- **可视化展示**：基于 ECharts 的交互式图谱可视化，支持节点展开、模糊匹配、类型筛选
- **CRUD 操作**：完整的实体与关系增删改查功能
- **统计分析**：实体/关系类型分布统计，数据总览
- **Neo4j 集成**：高性能图数据库存储与查询

### 🔐 用户系统
- **注册登录**：基于 JWT 的无状态认证
- **角色权限**：支持管理员、普通用户多级权限控制
- **会话管理**：安全的 Token 机制，自动过期刷新

### 📈 数据管理
- **多数据源融合**：支持 JSON、OWL 本体文件导入
- **实体分类**：自动/手动实体重分类与关系映射
- **批量操作**：支持批量导入、导出、更新

---

## 🛠️ 技术栈

### 后端
| 技术 | 版本 | 用途 |
|------|------|------|
| **Python** | 3.11+ | 主要开发语言 |
| **FastAPI** | 0.104+ | Web API 框架 |
| **Neo4j** | 5.18+ | 图数据库 |
| **DashScope** | 1.14+ | 通义千问大模型 SDK |
| **Pydantic** | 2.5+ | 数据验证与序列化 |
| **Loguru** | 0.7+ | 日志管理 |
| **Uvicorn** | 0.24+ | ASGI 服务器 |

### 前端
| 技术 | 版本 | 用途 |
|------|------|------|
| **Vue 3** | 3.3+ | 前端框架 |
| **Vite** | 5.0+ | 构建工具 |
| **Element Plus** | 2.4+ | UI 组件库 |
| **ECharts** | 5.4+ | 图谱可视化 |
| **Axios** | 1.6+ | HTTP 客户端 |
| **Vue Router** | 4.2+ | 路由管理 |

### 基础设施
- **Docker & Docker Compose**：容器化部署
- **Git**：版本控制
- **PowerShell**：自动化脚本

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                        前端 (Vue 3)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────  ┌──────────┐ │
│  │ 智能问答  │  │ 图谱可视化│  │ 数据管理  │  │ 用户中心  │ │
│  └────┬─────┘  └────┬─────  └────┬─────┘  └────┬───── │
└───────┼──────────────┼──────────────┼──────────────┼──────┘
        │              │              │              │
        └──────────────┴──────────────┴──────────────┘
                           │
                    HTTP / REST API
                           │
┌──────────────────────────┼──────────────────────────────┐
│                     后端 (FastAPI)                        │
│  ┌──────────┐  ┌──────────  ┌──────────┐  ┌──────────┐ │
│  │ QA 引擎   │  │ KG 检索  │  │ 实体提取  │  │ LLM 客户端│ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘ │
│       │              │              │              │      │
│  ┌────┴──────────────┴──────────────┴──────────────┴────┐ │
│  │              Neo4j Client (py2neo)                    │ │
│  └────────────────────┬─────────────────────────────────┘ │
└───────────────────────┼───────────────────────────────────┘
                        │
                 Bolt Protocol
                        │
        ┌───────────────┴────────────────┐
        │       Neo4j 图数据库            │
        │  ┌──────────┐  ┌──────────┐   │
        │  │  实体节点  │  │  关系边   │   │
        │  │  Disease │──│HAS_SYMPTOM│──▶│
        │  │Symptom   │  │TREATS    │   │
        │  └──────────  └──────────┘   │
        └────────────────────────────────┘
```

---

## 🚀 快速开始

### 环境要求

- **Python** >= 3.11
- **Node.js** >= 18
- **JDK** 17（Neo4j 依赖）
- **Docker & Docker Compose**（可选，推荐）

### 1. 克隆项目

```bash
git clone https://github.com/your-username/tcm-kg-qa.git
cd tcm-kg-qa
```

### 2. 配置 Neo4j 数据库

```bash
# 方式一：使用 Docker Compose（推荐）
docker-compose up -d neo4j

# 方式二：本地安装
# 下载 Neo4j Community Edition 5.18+
# 配置环境变量（参考 NEO4J_SETUP.md）
```

### 3. 配置环境变量

```bash
# 复制示例配置
cp backend/.env.example backend/.env

# 编辑配置
vim backend/.env
```

`.env` 文件示例：
```env
# Neo4j 配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# 大模型配置（通义千问）
DASHSCOPE_API_KEY=sk-your-api-key
LLM_MODEL=qwen-plus
```

> ⚠️ **重要**：需要前往 [阿里云百炼平台](https://dashscope.console.aliyun.com/) 申请 API Key

### 4. 安装后端依赖

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 5. 安装前端依赖

```bash
cd ../frontend
npm install
```

### 6. 构建知识图谱（可选）

```bash
cd backend

# 从 OWL 本体文件构建图谱
python build_kg_from_owl.py

# 或从 JSON 数据构建
python build_up_graph.py --website <url> --user <user> --password <pwd>
```

### 7. 启动服务

```bash
# 启动后端（开发模式）
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 启动前端（新终端）
cd frontend
npm run dev
```

### 8. 访问系统

- **前端界面**：http://localhost:3000
- **API 文档**：http://localhost:8000/docs
- **Neo4j Browser**：http://localhost:7474

---

## 📂 项目结构

```
tcm-kg-qa/
├── backend/                      # 后端服务
│   ├── app/
│   │   ├── api/                  # API 路由
│   │   │   ├── auth.py           # 认证接口
│   │   │   ├── qa.py             # 问答接口
│   │   │   ├── kg_management.py  # 图谱管理接口
│   │   │   └── ...
│   │   ├── services/             # 业务逻辑
│   │   │   ├── qa/               # 问答引擎
│   │   │   │   ├── qa_engine.py
│   │   │   │   ├── entity_extractor.py
│   │   │   │   ├── kg_retriever.py
│   │   │   │   └── llm_client.py
│   │   │   ├── kg/               # 图谱服务
│   │   │   └── auth/             # 认证服务
│   │   ├── models/               # 数据模型
│   │   └── core/                 # 核心配置
│   ├── data/                     # 数据文件
│   ├── build_kg_from_owl.py      # 图谱构建脚本
│   ├── main.py                   # 应用入口
│   └── requirements.txt
│
├── frontend/                     # 前端应用
│   ├── src/
│   │   ├── views/                # 页面组件
│   │   │   ├── QA.vue            # 智能问答
│   │   │   ├── KGVisual.vue      # 图谱可视化
│   │   │   ├── DataManagement.vue# 数据管理
│   │   │   └── Login.vue         # 登录注册
│   │   ├── router/               # 路由配置
│   │   └── utils/                # 工具函数
│   └── package.json
│
├── neo4j/                        # Neo4j 配置
│   ├── data/                     # 数据库文件
│   └── plugins/                  # 插件（如 APOC）
│
├── docs/                         # 项目文档
│   ├── 知识图谱Schema设计.md
│   ├── API 接口文档.md
│   └── ...
│
├── docker-compose.yml            # Docker 编排
└── README.md
```

---

## 💡 使用示例

### 智能问答

1. 访问 http://localhost:3000 并登录
2. 进入"智能问答"页面
3. 输入问题，如：
   - `心阴虚有什么症状？`
   - `胃痛怎么治疗？`
   - `人参有什么功效？`
4. 系统自动返回基于知识图谱的专业回答

### 图谱可视化

1. 进入"知识图谱"页面
2. 搜索实体（如"胃痛"）
3. 查看关联节点与关系
4. 支持节点展开、类型筛选、模糊匹配

### 数据管理

1. 进入"数据管理"页面
2. 查看实体/关系列表
3. 支持新增、编辑、删除操作
4. 查看统计数据与分布图表

---

## 🔧 配置说明

### Neo4j 配置

```bash
# docker-compose.yml
services:
  neo4j:
    image: neo4j:5.18-community
    ports:
      - "7474:7474"  # Browser
      - "7687:7687"  # Bolt
    environment:
      - NEO4J_AUTH=neo4j/password
    volumes:
      - ./neo4j/data:/data
      - ./neo4j/plugins:/plugins
```

### 大模型配置

在 `backend/.env` 中配置：

```env
# 通义千问
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
LLM_MODEL=qwen-plus  # 可选：qwen-turbo, qwen-plus, qwen-max
```

> 💡 **获取 API Key**：访问 [阿里云百炼平台](https://dashscope.console.aliyun.com/apiKey)

---

## 📊 知识图谱 Schema

核心实体类型：
- **Disease**（疾病）：胃痛、心阴虚、感冒等
- **Symptom**（症状）：多梦、盗汗、潮热等
- **Prescription**（方剂）：天王补心丸、十全大补丸等
- **Herb**（草药）：人参、黄芪、当归等
- **Therapy**（疗法）：针灸、推拿、艾灸等

核心关系类型：
- **HAS_SYMPTOM**（有症状）：疾病 → 症状
- **TREATED_BY_PRESCRIPTION**（治疗方剂）：疾病 → 方剂
- **CONTAINS_HERB**（包含草药）：方剂 → 草药
- **HAS_EFFECT**（具有功效）：草药/方剂 → 功效
- **BELONGS_TO_MERIDIAN**（归经）：草药 → 经络

详细设计请参考：[知识图谱 Schema 设计](docs/知识图谱 Schema 设计.md)

---

## 🧪 测试

### 后端测试

```bash
cd backend

# 运行测试脚本
python test_api.py          # API 接口测试
python test_query.py        # 图谱查询测试
python test_rag.py          # RAG 流程测试
```

### 前端测试

```bash
cd frontend

# 开发模式（含热重载）
npm run dev

# 构建生产版本
npm run build
```

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 📞 联系方式

- **项目维护者**：[AAA0925](mailto:your-email@example.com)
- **项目地址**：https://github.com/AAA0925/tcm-kg-qa
- **问题反馈**：请在 GitHub Issues 中提交

---

## 🙏 致谢

- [Neo4j](https://neo4j.com/) - 图数据库
- [FastAPI](https://fastapi.tiangolo.com/) - 高性能 Web 框架
- [Vue 3](https://vuejs.org/) - 渐进式 JavaScript 框架
- [通义千问](https://help.aliyun.com/zh/dashscope/) - 大语言模型
- [ECharts](https://echarts.apache.org/) - 可视化图表库

---

<div align="center">

**如果这个项目对你有帮助，请给个 ⭐ Star 支持一下！**

Made with ❤️ by TCM-KG-QA Team

</div>
