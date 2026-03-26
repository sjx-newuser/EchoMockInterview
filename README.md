# Echo Mock System (AI 模拟面试平台)

## 📌 项目简介

Echo Mock System 是一个由 AI 驱动的沉浸式模拟面试平台。结合 RAG（检索增强生成）架构，平台可提供基于本地或云端大模型的高质量文本分析与真实语音交互，以多维度客观能力雷达图展示测试数据，为您深度评估求职者的真实水平。

## 🛠 技术栈

- **前端层**: Vue 3 (Vite), Pinia (状态管理), ECharts (可视化数据分析雷达)
- **后端层**: FastAPI (Python 异步高并发), LlamaIndex / RAG 系统, SQLAlchemy 内部 ORM 引擎
- **AI 与数据驱动**: PostgreSQL, Redis, ChromaDB, 容器级 GPU 加速组件 (含 SenseVoice、PyTorch 等模型)

---

## 💻 本地开发指南：DevContainers (极度推荐)

本项目基于底层系统级音频依赖（`ffmpeg`, `libsndfile` 等）与复杂的运算库。为彻底杜绝环境污染、版本冲突与平台差异，项目已为您配置好 **VS Code DevContainers**，可一键拉起沙盒式全自动显卡直通式工作栈。

### 1. 准备工作

请在宿主机（Windows或主机Linux皆可）上预先安装：
- **Docker** Engine (建议开启 WSL 2 结合 Docker Desktop)
- *(可选但强烈推荐)* 宿主机 **NVIDIA 显卡驱动** 与 Container Toolkit (便于直通 GPU 到系统底层做音频及模型推理)
- 安装 **Visual Studio Code** 及 **Dev Containers** 插件

### 2. 初始化容器内部开发区

1. 使用 VS Code 打开本项目根目录。
2. 触发弹窗并在命令面板选择 **`Dev Containers: Reopen in Container`**。
3. 首次构建会通过 `.devcontainer/Dockerfile` 拉取包含 `Miniconda` 和底层 C/C++ 音频环境的定制镜像，请耐心等待。
4. 容器内已配置统一插件套件（内置 Volar，Pylance，Prettier，ESLint），无需手动干预。

### 3. 项目运行与功能调试

进入容器终端，环境已经备妥：

- **自动化配置**: 系统创建后会触发 `postCreateCommand`，自动在 `backend` 目录下通过 Conda 和 `environment.yml` （如果存在）自动构建好 Python 专属支持栈。
- **启动前端**: 
  ```bash
  cd frontend
  # 预装 pnpm 全局运行环境
  pnpm install
  pnpm run dev
  # 服务将自动通过内建 forwardPorts 映射到本地测试端口 5173 
  ```
- **启动后端**: 
  ```bash
  cd backend
  poetry install  # 按需加装 Poetry 环境依赖
  poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
  ```

---

## 🚀 生产环境部署 (Docker Compose)

当需要将系统整体上线部署至集群节点或云服务器时，推荐使用项目预置的编排组合（包含 Redis、PG 库等全流程联动）：

```bash
# 1. 确保已复制环境变量凭证，并配置好您的核心云端大模型 API 及授权池
cp .env.example .env

# 2. 一键拉起微服务集群
docker-compose up -d --build
```

系统编排就绪后将对外暴露：
- 🌐 前台面试环境: [http://localhost:5173](http://localhost:5173)
- ⚙️ 后端 API 文档门户: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧩 初始化题库与向量核心

如果是首次冷启动或执行了 `data/` 文件大换血重构方案，请务必执行核心脚本完成初始化打底：

```bash
# 自动建表（User、对话 Session、各项评测维度的细粒度维度 DimensionScore 表等）
python scripts/init_db.py

# 读取 /data/raw/*.md 将考点全量向量化为 ChromaDB 离线知识索引
python scripts/build_vector_index.py
```

---

## 📡 API 接口蓝图

启动后端后，可通过 [http://localhost:8000/docs](http://localhost:8000/docs) 访问 Swagger 在线文档。以下为完整的接口规范。

### 统一响应约定

- 成功请求：直接返回业务 JSON（无额外包装）。
- 失败请求：统一结构如下：
  ```json
  {
    "code": 40001,
    "message": "请求参数校验失败",
    "details": [...]
  }
  ```

### 鉴权机制

所有非公开接口需要在请求头中携带 JWT 令牌：
```
Authorization: Bearer <access_token>
```
令牌通过注册或登录接口获取，有效期 24 小时。过期后需重新登录。

---

### 1. 鉴权模块 (`/api/v1/auth`)

#### `POST /api/v1/auth/register` — 用户注册

创建新账号并直接返回 JWT 令牌，无需二次登录。

**请求体：**
```json
{
  "username": "zhangsan",
  "password": "mypassword123"
}
```

**成功响应 (201)：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**失败场景：**
| 状态码 | 说明 |
|--------|------|
| `409` | 该用户名已被注册 |
| `400` | 参数校验失败（用户名 < 2 字符 或 密码 < 6 字符） |

---

#### `POST /api/v1/auth/login` — 用户登录

**请求体：**
```json
{
  "username": "zhangsan",
  "password": "mypassword123"
}
```

**成功响应 (200)：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**失败场景：**
| 状态码 | 说明 |
|--------|------|
| `401` | 用户名或密码错误 |

---

#### `GET /api/v1/auth/me` — 获取当前用户信息 🔒

**成功响应 (200)：**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "username": "zhangsan"
}
```

---

### 2. 面试场次模块 (`/api/v1/interviews`) 🔒

#### `POST /api/v1/interviews/` — 创建面试场次

**请求体：**
```json
{
  "target_role": "Java 后端"
}
```

**成功响应 (201)：**
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "target_role": "Java 后端",
  "status": "ONGOING",
  "start_time": "2026-03-18T22:30:00",
  "end_time": null,
  "overall_score": null
}
```

---

#### `GET /api/v1/interviews/` — 获取面试历史列表

返回当前用户的全部面试记录，按开始时间**倒序**排列，用于 Dashboard 历史面板展示。

**成功响应 (200)：**
```json
[
  {
    "id": "f47ac10b-...",
    "target_role": "Java 后端",
    "status": "COMPLETED",
    "start_time": "2026-03-18T20:00:00",
    "end_time": "2026-03-18T20:45:00",
    "overall_score": 82.5
  },
  {
    "id": "c9bf9e57-...",
    "target_role": "前端工程师",
    "status": "ONGOING",
    "start_time": "2026-03-18T22:30:00",
    "end_time": null,
    "overall_score": null
  }
]
```

---

#### `GET /api/v1/interviews/{session_id}` — 获取场次详情

返回单个面试场次的完整信息，包含按序排列的**全部对话记录**，用于对话复盘。

**成功响应 (200)：**
```json
{
  "id": "f47ac10b-...",
  "target_role": "Java 后端",
  "status": "COMPLETED",
  "start_time": "2026-03-18T20:00:00",
  "end_time": "2026-03-18T20:45:00",
  "overall_score": 82.5,
  "dimension_scores": {"技术深度": 85, "逻辑表达": 78, "沟通能力": 90},
  "comprehensive_report": "该候选人在 Java 并发编程方面表现优异...",
  "messages": [
    {
      "id": "msg-001",
      "round_seq": 1,
      "speaker": "AI",
      "content": "你好！欢迎参加今天的模拟面试...",
      "audio_file_path": null,
      "created_at": "2026-03-18T20:00:05"
    },
    {
      "id": "msg-002",
      "round_seq": 2,
      "speaker": "USER",
      "content": "你好，我准备好了。",
      "audio_file_path": "/data/audio/session-xxx/round-2.wav",
      "created_at": "2026-03-18T20:00:15"
    }
  ]
}
```

**失败场景：**
| 状态码 | 说明 |
|--------|------|
| `404` | 面试场次不存在（或不属于当前用户） |

---

### 3. 评估报告模块 (`/api/v1/reports`) 🔒

#### `GET /api/v1/reports/{session_id}` — 获取综合评估报告

返回指定面试场次的结构化报告数据，驱动前端**能力雷达图**和**问答明细卡片**的渲染。

**成功响应 (200)：**
```json
{
  "session_id": "f47ac10b-...",
  "target_role": "Java 后端",
  "status": "COMPLETED",
  "overall_score": 82.5,
  "dimension_scores": [
    { "name": "技术深度", "score": 85 },
    { "name": "逻辑表达", "score": 78 },
    { "name": "沟通能力", "score": 90 },
    { "name": "项目经验", "score": 75 },
    { "name": "应变能力", "score": 80 }
  ],
  "comprehensive_report": "## 综合评价\n该候选人整体表现良好...",
  "evaluations": [
    {
      "id": "eval-001",
      "question_content": "请解释 Java 中 synchronized 和 ReentrantLock 的区别",
      "user_answer": "synchronized 是 JVM 层面的内置锁...",
      "audio_analysis_status": "COMPLETED",
      "speech_rate": 156.3,
      "pause_ratio": 0.12,
      "technical_score": 88.0,
      "correction_feedback": "回答基本准确，但缺少对 Condition 接口的说明..."
    },
    {
      "id": "eval-002",
      "question_content": "设计一个支持百万用户的秒杀系统",
      "user_answer": "我会从限流、缓存预热、异步削峰三个层面来设计...",
      "audio_analysis_status": "PENDING",
      "speech_rate": null,
      "pause_ratio": null,
      "technical_score": 72.0,
      "correction_feedback": "方案整体思路正确，但缺少数据库层的乐观锁机制..."
    }
  ]
}
```

---

### 4. WebSocket 实时交互 (`/api/v1/ws`)

#### `WS /api/v1/ws/{session_id}` — 面试全双工通道

建立 WebSocket 长连接后，前后端通过统一的 **JSON 信封格式**进行全双工通信。

**信封结构（双向通用）：**
```json
{
  "id": "uuid-v4",
  "timestamp": 1710784200000,
  "session_id": "f47ac10b-...",
  "type": "消息类型枚举",
  "payload": { ... }
}
```

**消息类型枚举 (`type` 字段)：**

| 类型 | 方向 | 说明 |
|------|------|------|
| `start_interview` | 客户端 → 服务端 | 通知后端开始面试流程 |
| `audio_chunk` | 客户端 → 服务端 | 发送录音切片(含序号防乱序) |
| `stop_speaking` | 客户端 → 服务端 | 用户打断 AI 发言 |
| `text_stream` | 服务端 → 客户端 | AI 回答的增量文本流(打字机效果) |
| `system_status` | 服务端 → 客户端 | AI 状态变更(thinking/listening/evaluating/idle) |
| `audio_chunk` | 服务端 → 客户端 | AI 语音合成切片(TTS) |
| `error` | 服务端 → 客户端 | 错误信息推送 |

**客户端发送示例 — 音频切片：**
```json
{
  "id": "a1b2c3d4-...",
  "timestamp": 1710784200000,
  "session_id": "f47ac10b-...",
  "type": "audio_chunk",
  "payload": {
    "seq": 1,
    "audio_base64": "UklGRiQAA...==",
    "is_last": false
  }
}
```

**服务端推送示例 — AI 文本流：**
```json
{
  "id": "e5f6a7b8-...",
  "timestamp": 1710784201000,
  "session_id": "f47ac10b-...",
  "type": "text_stream",
  "payload": {
    "chunk_id": "answer-001",
    "seq": 3,
    "text": "synchronized 是 JVM 内置的",
    "is_end": false
  }
}
```

**服务端推送示例 — 系统状态：**
```json
{
  "id": "c9d0e1f2-...",
  "timestamp": 1710784202000,
  "session_id": "f47ac10b-...",
  "type": "system_status",
  "payload": {
    "status": "thinking",
    "message": "AI 正在分析您的回答..."
  }
}
```

**服务端推送示例 — 错误信息：**
```json
{
  "id": "d1e2f3a4-...",
  "timestamp": 1710784203000,
  "session_id": "f47ac10b-...",
  "type": "error",
  "payload": {
    "code": 40000,
    "message": "消息解析失败: type 字段缺失"
  }
}
```

---

### 5. 系统接口

#### `GET /health` — 健康检查

**成功响应 (200)：**
```json
{
  "status": "ok"
}
```

> 🔒 标记表示该接口需要在请求头中携带 `Authorization: Bearer <token>` 进行鉴权。
