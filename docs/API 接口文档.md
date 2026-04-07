# 中医知识图谱问答系统 - API 接口文档

> **版本**: v1.0.0  
> **最后更新**: 2026-04-03  
> **基础地址**: http://localhost:8000/api  
> **维护方式**: 自动生成框架 + 手动补充示例

---

## 📋 目录

- [认证接口](#认证接口)
- [管理员接口](#管理员接口)
- [知识图谱接口](#知识图谱接口)
- [问答接口](#问答接口)
- [爬虫接口](#爬虫接口)
- [搜索接口](#搜索接口)

---

## 🔐 认证接口

### 1. 用户注册

**POST** `/auth/register`

注册用户账号。

**请求参数**:
```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "your_password",
  "role": "user"
}
```

**响应示例**:
```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "role": "user",
  "created_at": "2026-04-03T10:00:00",
  "is_active": true
}
```

---

### 2. 用户登录

**POST** `/auth/login`

用户登录获取访问令牌。

**请求参数**:
```json
{
  "username": "testuser",
  "password": "your_password"
}
```

**响应示例**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "role": "user",
    "created_at": "2026-04-03T10:00:00",
    "is_active": true
  }
}
```

---

### 3. 获取当前用户信息

**GET** `/auth/me`

获取当前登录用户的详细信息。

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应示例**:
```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "role": "user",
  "created_at": "2026-04-03T10:00:00",
  "is_active": true
}
```

---

### 4. 更新用户资料

**PUT** `/auth/profile`

更新当前用户的个人信息。

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求参数**:
```json
{
  "username": "newusername",
  "email": "newemail@example.com"
}
```

---

### 5. 修改密码

**PUT** `/auth/password`

修改当前用户的登录密码。

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求参数**:
```json
{
  "old_password": "old_password",
  "new_password": "new_password"
}
```

---

## 👨‍💼 管理员接口

> ⚠️ **仅管理员角色可访问**

### 1. 获取所有用户列表

**GET** `/admin/users`

**请求头**:
```
Authorization: Bearer <admin_access_token>
```

**查询参数**:
- `skip` (可选，默认 0): 跳过记录数
- `limit` (可选，默认 100): 返回记录数

---

### 2. 激活/禁用用户

**PUT** `/admin/users/{user_id}/activate`

**请求头**:
```
Authorization: Bearer <admin_access_token>
```

**路径参数**:
- `user_id`: 用户 ID

---

### 3. 更新用户角色

**PUT** `/admin/users/{user_id}/role`

**请求头**:
```
Authorization: Bearer <admin_access_token>
```

**路径参数**:
- `user_id`: 用户 ID

**查询参数**:
- `role`: 新角色 (user 或 admin)

---

## 🗂️ 知识图谱接口

### 1. 获取图谱统计信息

**GET** `/kg/stats`

**响应示例**:
```json
{
  "entity_count": 17640,
  "relation_count": 152529
}
```

---

### 2. 查询实体及其关系 ⭐

**GET** `/kg/entities/{entity_name}`

根据实体名称查询该实体及其关联的所有其他实体和关系。

**路径参数**:
- `entity_name`: 实体名称（如"感冒"）

**响应示例**:
```json
{
  "results": [
    {
      "n": {
        "name": "感冒",
        "category": "Disease"
      },
      "m": {
        "name": "阿司匹林",
        "category": "Drug"
      },
      "r": {
        "type": "common_drug"
      }
    },
    {
      "n": {
        "name": "感冒",
        "category": "Disease"
      },
      "m": {
        "name": "发烧",
        "category": "Symptom"
      },
      "r": {
        "type": "has_symptom"
      }
    }
  ]
}
```

---

### 3. 创建实体

**POST** `/kg/entities`

**请求参数**:
```json
{
  "name": "实体名称",
  "category": "Disease",
  "description": "实体描述",
  "properties": {}
}
```

---

### 4. 创建关系

**POST** `/kg/relations`

**请求参数**:
```json
{
  "source_entity": "实体 A",
  "target_entity": "实体 B",
  "relation_type": "treat_with",
  "properties": {}
}
```

---

## 🤖 问答接口

### 1. 智能问答

**POST** `/qa/ask`

输入问题，获取基于知识图谱的智能回答。

**请求参数**:
```json
{
  "question": "感冒吃什么药？",
  "top_k": 5
}
```

---

## 🕷️ 爬虫接口

### 1. 创建爬取任务

**POST** `/crawler/tasks`

**请求参数**:
```json
{
  "url": "https://example.com/tcm-data",
  "depth": 2,
  "allow_domains": ["example.com"],
  "config": {}
}
```

**响应示例**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "config": {},
  "created_at": "2026-04-03T10:00:00"
}
```

---

### 2. 获取任务状态

**GET** `/crawler/tasks/{task_id}`

**路径参数**:
- `task_id`: 任务 ID

---

### 3. 停止爬取任务

**POST** `/crawler/tasks/{task_id}/stop`

**路径参数**:
- `task_id`: 任务 ID

---

### 4. 获取所有任务列表

**GET** `/crawler/tasks`

---

## 🔍 搜索接口

### 1. 全文搜索

**GET** `/search/fulltext`

**查询参数**:
- `keyword`: 搜索关键词
- `limit` (可选，默认 10): 返回结果数量

---

## 📝 错误响应格式

所有接口在发生错误时统一返回以下格式：

```json
{
  "detail": "错误描述信息"
}
```

常见 HTTP 状态码说明：
- `200 OK`: 请求成功
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 未授权访问（缺少或无效的 token）
- `403 Forbidden`: 禁止访问（权限不足）
- `404 Not Found`: 资源不存在
- `500 Internal Server Error`: 服务器内部错误

---

## 🔑 认证说明

需要认证的接口需要在请求头中包含 `Authorization` 字段：

```
Authorization: Bearer <your_access_token>
```

Token 通过 `/api/auth/login` 接口登录后获得。

---

## 📊 实体类型说明

系统支持的实体类型：
- `Disease`: 疾病
- `Drug`: 药品
- `Food`: 食物
- `Check`: 检查
- `Department`: 科室
- `Producer`: 生产商
- `Symptom`: 症状
- `Cure`: 疗法

---

## 🔗 关系类型说明

系统支持的关系类型：
- `belongs_to`: 属于
- `common_drug`: 常用药
- `do_eat`: 宜吃
- `drugs_of`: 药物治疗
- `need_check`: 需要检查
- `no_eat`: 忌吃
- `recommand_drug`: 推荐药
- `recommand_eat`: 推荐食物
- `has_symptom`: 症状
- `acompany_with`: 并发症
- `cure_way`: 治疗方法

---

## 🛠️ 文档维护说明

本文档采用"自动生成 + 手动完善"的混合维护模式：

1. **自动生成**: 使用 `python backend/generate_api_docs.py` 扫描 API 路由
2. **手动补充**: 在生成的框架基础上补充参数示例和响应示例
3. **Git Hook**: commit 时自动检测 API 变更并提醒更新文档

详见：[API 文档维护指南.md](./API 文档维护指南.md)

*文档最后更新*: 2026-04-03

---

## 🕷️ 爬虫接口


### GET `/tasks`

获取所有任务列表

**请求参数**:

```json
// TODO: 补充参数示例
```

**响应示例**:

```json
// TODO: 补充响应示例
```


### GET `/tasks/{task_id}`

获取任务状态

**请求参数**:

```json
// TODO: 补充参数示例
```

**响应示例**:

```json
// TODO: 补充响应示例
```


### POST `/tasks/{task_id}/stop`

停止爬取任务

**请求参数**:

```json
// TODO: 补充参数示例
```

**响应示例**:

```json
// TODO: 补充响应示例
```


---

## 🗂️ 知识图谱接口


### POST `/entities`

**请求参数**:

```json
// TODO: 补充参数示例
```

**响应示例**:

```json
// TODO: 补充响应示例
```


### GET `/entities/{entity_name}`

**请求参数**:

```json
// TODO: 补充参数示例
```

**响应示例**:

```json
// TODO: 补充响应示例
```


### POST `/relations`

**请求参数**:

```json
// TODO: 补充参数示例
```

**响应示例**:

```json
// TODO: 补充响应示例
```


### GET `/stats`

**请求参数**:

```json
// TODO: 补充参数示例
```

**响应示例**:

```json
// TODO: 补充响应示例
```


---

## 🔍 搜索接口


### GET `/fulltext`

**请求参数**:

```json
// TODO: 补充参数示例
```

**响应示例**:

```json
// TODO: 补充响应示例
```


---

## 📝 错误响应格式

所有接口在发生错误时统一返回以下格式：

```json
{
  "detail": "错误描述信息"
}
```

常见 HTTP 状态码说明：
- `200 OK`: 请求成功
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 未授权访问（缺少或无效的 token）
- `403 Forbidden`: 禁止访问（权限不足）
- `404 Not Found`: 资源不存在
- `500 Internal Server Error`: 服务器内部错误

---

## 🔑 认证说明

需要认证的接口需要在请求头中包含 `Authorization` 字段：

```
Authorization: Bearer <your_access_token>
```

Token 通过 `/api/auth/login` 接口登录后获得。

---

## 📊 实体类型说明

系统支持的实体类型：
- `Disease`: 疾病
- `Drug`: 药品
- `Food`: 食物
- `Check`: 检查
- `Department`: 科室
- `Producer`: 生产商
- `Symptom`: 症状
- `Cure`: 疗法

## 🔗 关系类型说明

系统支持的关系类型：
- `belongs_to`: 属于
- `common_drug`: 常用药
- `do_eat`: 宜吃
- `drugs_of`: 药物治疗
- `need_check`: 需要检查
- `no_eat`: 忌吃
- `recommand_drug`: 推荐药
- `recommand_eat`: 推荐食物
- `has_symptom`: 症状
- `acompany_with`: 并发症
- `cure_way`: 治疗方法


*文档由 API 文档生成器自动生成*
