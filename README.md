# Conductor

> 你的 AI 团队，一人公司的标配

**Conductor** 是一个 AI 团队协作平台，将多 agent 协作可视化为熟悉的**群聊体验**。提交需求，看 AI 团队自动组建、分工协作，最终交付成果。

## 项目亮点

| 特性 | 说明 |
|------|------|
| **群聊隐喻** | 把 AI 协作映射成群聊，直观易懂 |
| **动态组队** | 秘书根据需求智能组建团队 |
| **实时可视** | WebSocket 实时推送，看到每个 agent 的工作过程 |
| **文件浏览** | 内置工作目录浏览器，支持 Markdown 渲染 |
| **即时反馈** | 提交需求秒进聊天，无需等待 |

## 用户体验

```
1. 创建项目 → 输入需求 "做一个待办清单应用"
2. 秒进聊天 → 看到秘书加入并分析需求
3. 团队组建 → 秘书拆解需求，组建 PM + Backend + Frontend + Tester
4. 实时协作 → 群聊中看到各 agent 的工作进度和沟通
5. 交付成果 → 项目完成，代码在工作目录中
```

## Quick Start

### 1. 克隆项目

```bash
git clone https://github.com/slicenferqin/Conductor.git
cd Conductor
```

### 2. 安装后端依赖

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -e ".[dev]"
```

### 3. 安装前端依赖

```bash
cd frontend
npm install
```

### 4. 启动服务

```bash
# 终端 1: 启动后端
cd conductor/api
uvicorn main:app --reload --port 8000

# 终端 2: 启动前端
cd frontend
npm run dev
```

### 5. 打开浏览器

访问 http://localhost:5173，创建你的第一个项目！

## 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | React 19 + TypeScript + Tailwind CSS v4 + Zustand |
| **后端** | Python 3.11+ + FastAPI + WebSocket |
| **AI 引擎** | Claude Code CLI (每个 agent 一个独立 session) |
| **实时通信** | WebSocket 双向推送 |

## 项目结构

```
conductor/
├── frontend/                # React 前端
│   ├── src/
│   │   ├── components/      # UI 组件
│   │   │   ├── chat/        # 聊天区域
│   │   │   ├── sidebar/     # 左侧项目列表
│   │   │   └── workspace/   # 右侧工作区面板
│   │   ├── hooks/           # WebSocket 等 hooks
│   │   ├── stores/          # Zustand 状态管理
│   │   └── App.tsx
│   └── package.json
│
├── conductor/
│   ├── api/                 # FastAPI 后端
│   │   ├── routers/         # API 路由
│   │   ├── schemas/         # Pydantic 模型
│   │   ├── services/        # 业务逻辑
│   │   ├── websocket/       # WebSocket 管理
│   │   └── main.py
│   │
│   ├── core/                # 核心逻辑
│   │   ├── secretary.py     # 秘书 (需求分析/组队)
│   │   ├── agent.py         # Agent 基类
│   │   ├── message_bus.py   # 消息总线
│   │   └── orchestrator.py  # 编排引擎
│   │
│   └── integrations/
│       └── claude_cli.py    # Claude Code CLI 集成
│
├── docs/
│   ├── PRODUCT_SPEC.md      # 产品规格书
│   └── PRD-project-creation-flow.md
│
└── pyproject.toml
```

## 核心概念

### 角色 (Roles)

| 角色 | 职责 |
|------|------|
| **秘书** | 需求分析、团队组建、任务分配、进度监控 |
| **PM** | 产品需求分析，输出 PRD |
| **Architect** | 技术架构设计 |
| **Backend** | 后端 API 开发 |
| **Frontend** | 前端 UI 开发 |
| **Tester** | 测试验证 |
| **Researcher** | 信息调研 |

### 动态组队示例

| 需求 | 组建的团队 |
|------|-----------|
| "做一个待办应用" | PM + Architect + Backend + Frontend + Tester |
| "调研 OpenAI" | Researcher |
| "写一份技术方案" | Architect + Writer |

## 开发状态

### 已完成

- [x] React 前端基础框架
- [x] 项目列表 + 群聊界面
- [x] WebSocket 实时消息推送
- [x] 项目创建流程 (秘书分析→组队→任务分配)
- [x] 团队面板实时状态
- [x] 工作目录文件浏览
- [x] Markdown 文件渲染
- [x] 消息置顶 (需求/任务分解)

### 进行中

- [ ] Agent 实际执行任务
- [ ] Agent 间消息路由 (@提及)
- [ ] 项目停止/暂停功能完善

### 规划中

- [ ] 更多角色支持
- [ ] 项目导出/下载
- [ ] 用户自定义角色
- [ ] 历史记录持久化

## 相关项目

- [Claude Code](https://claude.ai/code) - Anthropic 官方 AI 编程助手
- [Beads](https://github.com/steveyegge/beads) - Agent 记忆系统

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**Stop babysitting. Start delegating.**