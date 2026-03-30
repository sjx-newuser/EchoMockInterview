# 🚀 EchoMock - 协作开发分支 (Dev Branch)

欢迎来到 **EchoMock** 的开发协作中心！此分支是项目的核心心脏，所有的最新特性、试验性改动和社区贡献都会首先在这里汇聚。

---

## 🎯 分支定位
- **主战场**：此分支用于日常开发、特性实现及 Bug 修复。
- **合并规则**：代码在 `dev` 分支验证稳定后，将定期通过 Pull Request 合并至 `main` 分支。

---

## 🤝 如何参与协作

我们珍视每一份贡献！为了保证代码质量和协作效率，请遵循以下流程：

### 1. 领取任务
- 在参与开发前，请先查看 **Issues** 或与团队成员讨论，避免重复劳动。

### 2. 创建特性分支 (Feature Branch)
请尽量不要直接在 `dev` 分支提交重大的全局性改动。建议根据任务类型创建新分支：
- `feat/xxx`：用于新功能开发
- `fix/xxx`：用于修复 Bug
- `docs/xxx`：用于完善文档
- `refactor/xxx`：用于代码重构

### 3. 环境准备
为了彻底解决“在我的电脑上跑不起来”的问题，本项目**强制推荐**使用 Docker 进行协作开发。
👉 **[详解：Docker 本地开发指南 (README-DOCKER.md)](./README-DOCKER.md)**

### 4. 代码提交规范
- **Commit Message**: 请编写清晰且具有描述性的提交信息。
- **代码风格**: 请遵循项目根目录下的 `.editorconfig` 规范。
- **自测**: 提交前请确保运行 `docker-compose up` 能够正常拉起 full-stack 服务。

### 5. 开启 Pull Request (PR)
- 完成开发并推送分支后，请发起指向 `dev` 分支的 Pull Request。
- 至少需要一名其他团队成员 Review 后方可合并。

---

## 🛠 核心组件速览
- **`backend/`**: FastAPI 驱动，集成了 LlamaIndex RAG 架构与 ASR/TTS 引擎。
- **`frontend/`**: Vue 3 (Vite) 驱动，包含实时音视频交互与 ECharts 评估雷达图。
- **`deploy_scripts/`**: 存放数据库初始化、向量索引构建等核心运维脚本。

---

## 📅 近期开发路线 (Roadmap)
- [ ] 接入更多的开源大模型适配层。
- [ ] 优化实时语音通话的延迟 (WebSockets + Chunking)。
- [ ] 增强评估报告的 PDF 导出功能。

---

让我们一起打造全球最专业的 AI 模拟面试平台！✨
