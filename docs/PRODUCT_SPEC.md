# Conductor 产品规划

> 把 AI 开发从"同步交互"变成"异步托管"

## 一句话定义

**Conductor** - 提交需求，后台自动开发，完成后通知你。

## 核心痛点

现在让 AI 做项目（APP、小程序、网站）的体验：

| 痛点 | 描述 |
|------|------|
| 要等待 | AI 在跑，你得盯着 |
| 要交互 | 每一步都问你，要不要继续 |
| 要跟踪 | 做到哪了？什么状态？ |
| 要测试 | 做完了你得手动测 |
| 要反馈 | 发现问题得告诉它 |
| 要修复 | 来回改好几轮 |
| 离开就停 | 关电脑 = 进度停止 |

**本质问题**：AI 开发是"同步阻塞"的，人必须在场。

## 解决方案

### 异步托管模式

```
现在:
  你在电脑前 → AI 工作
  你离开电脑 → AI 停止

Conductor:
  提交需求 → 后台持续运行 → 手机收到通知 → 随时查看进度
            ↑
       不管你在不在电脑前
```

### 关键能力

| 能力 | 说明 |
|------|------|
| 后台运行 | 不依赖终端会话，7x24 执行 |
| 自治循环 | 自动测试、发现问题、修复、再测试 |
| 关键检查点 | Plan 确认、交付验收，避免跑偏 |
| 多端通知 | 微信/飞书/邮件，随时知道进度 |
| 断点恢复 | 任务可暂停、可恢复 |

## 用户体验

### 提交任务

```bash
$ conductor submit "做一个待办清单，支持用户登录和任务增删改查"

📋 任务已创建: task-20241230-001
📝 正在生成 Plan，完成后推送到你的微信等待确认
```

### Plan 确认（手机）

```
🔔 Conductor: Plan 待确认

待办清单应用 计划:
━━━━━━━━━━━━━━━━━━━━━━
功能:
  ✓ 用户注册/登录 (JWT)
  ✓ 任务增删改查
  ✓ 任务标记完成/未完成
  ✓ 按创建时间排序

技术栈:
  后端: FastAPI + SQLAlchemy + PostgreSQL
  前端: React + TypeScript + TailwindCSS

预计: 15-20 分钟
预估 Token: ~50k

[✅ 确认开始] [✏️ 我要调整] [❌ 取消]
```

### 执行中（可选查看）

```
🔔 Conductor: 进度更新

待办清单应用
━━━━━━━━━━━━━━━━━━━━━━
[=====>    ] 50%

✅ Plan 已确认
✅ 设计完成
🔄 后端开发中 (5/8 接口)
⏳ 前端开发
⏳ 测试验证

预计剩余: 8 分钟
```

### 完成通知

```
🎉 Conductor: 任务完成！

待办清单应用 已交付
━━━━━━━━━━━━━━━━━━━━━━
✅ 后端: 8 个 API 接口
✅ 前端: 5 个页面
✅ 测试: 23/23 通过
✅ 文档: PRD + 架构设计 + API 文档

📦 获取代码: conductor pull task-20241230-001
🌐 预览: http://localhost:3000 (docker-compose up)

[👀 查看详情] [📥 下载代码]
```

### 需要帮助时

```
⚠️ Conductor: 需要你的帮助

任务: 待办清单应用
阶段: 前端开发
问题: 自动修复 3 次仍失败

错误摘要:
  登录接口 CORS 错误，后端配置问题...

[🔧 我来介入] [🤖 继续尝试] [⏸️ 暂停任务]
```

## 检查点设计

```
┌─────────────────────────────────────┐
│ Plan [必须确认]                      │
│ 确保方向正确，避免白跑               │
└──────────────┬──────────────────────┘
               ↓ 确认后自动执行
┌─────────────────────────────────────┐
│ 设计 [自动]                          │
│ PRD、架构、API、数据库设计            │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 开发 [自动 + 自治循环]               │
│ 生成 → 测试 → 修复 → 重测            │
│ 最多自动修复 N 次                    │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 交付 [必须验收]                      │
│ 最终把关                            │
└─────────────────────────────────────┘
```

### 检查点配置

```yaml
checkpoints:
  plan:
    mode: required          # 必须人工确认
    timeout: 30m            # 30分钟未确认则提醒

  design:
    mode: auto              # 自动执行
    notify: false           # 不单独通知

  development:
    mode: auto              # 自动执行
    max_fix_attempts: 3     # 最多自动修复 3 次
    notify_on_stuck: true   # 卡住时通知

  delivery:
    mode: required          # 必须人工验收
```

## 技术架构

### 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    Conductor Server                      │
│                    (后台服务, 7x24)                       │
├─────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ 任务队列  │→│ 执行引擎  │→│ 自治循环  │→│ 通知服务 │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
└───────────────────────┬─────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ↓               ↓               ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  OpenSkills  │ │    Beads     │ │  Agent Mail  │
│  技能加载     │ │   任务记忆    │ │  Agent 通信  │
└──────────────┘ └──────────────┘ └──────────────┘
        │               │               │
        └───────────────┼───────────────┘
                        ↓
                ┌──────────────┐
                │ Claude Code  │
                │   执行引擎    │
                └──────────────┘
```

### 目录结构

```
conductor/
├── server/                     # 后台服务
│   ├── main.py                 # FastAPI 入口
│   ├── api/                    # REST API
│   │   ├── tasks.py            # 任务管理
│   │   └── progress.py         # 进度查询
│   ├── core/
│   │   ├── task_queue.py       # 任务队列
│   │   ├── executor.py         # 执行引擎
│   │   ├── decomposer.py       # 任务分解
│   │   └── auto_fix.py         # 自动修复
│   ├── notifications/          # 通知服务
│   │   ├── wechat.py           # 微信通知
│   │   ├── feishu.py           # 飞书通知
│   │   └── email.py            # 邮件通知
│   └── integrations/           # 外部集成
│       ├── claude_cli.py       # Claude Code
│       ├── beads.py            # Beads 记忆
│       ├── openskills.py       # OpenSkills
│       └── agent_mail.py       # Agent Mail
│
├── cli/                        # 命令行客户端
│   └── main.py                 # conductor submit/status/pull
│
├── web/                        # Web 界面 (Phase 2)
│   └── ...
│
├── roles/                      # 角色配置
│   ├── pm.yaml
│   ├── architect.yaml
│   ├── backend.yaml
│   ├── frontend.yaml
│   └── tester.yaml
│
└── templates/                  # 项目模板
    ├── fullstack-react-fastapi/
    └── ...
```

### 自治循环

```python
class AutonomousLoop:
    """自治循环：测试 → 分析 → 修复 → 重测"""

    def __init__(self, max_attempts: int = 3):
        self.max_attempts = max_attempts
        self.attempt = 0

    async def run(self, stage: Stage) -> Result:
        while self.attempt < self.max_attempts:
            # 1. 执行当前阶段
            result = await stage.execute()

            # 2. 运行测试
            test_result = await self.run_tests()

            if test_result.passed:
                return Result.success(result)

            # 3. 分析错误
            analysis = await self.analyze_failure(test_result)

            # 4. 自动修复
            await self.auto_fix(analysis)
            self.attempt += 1

        # 超过重试次数，请求人工介入
        return Result.need_help(test_result)
```

## 与现有工具的关系

| 工具 | 作用 | Conductor 如何使用 |
|------|------|-------------------|
| **Claude Code** | 代码执行 | 核心执行引擎 |
| **Beads** | 任务记忆 | 跨会话状态持久化（后续引入） |
| **Agent Mail** | Agent 通信 | 多角色协作时使用（后续引入） |
| **OpenSkills** | 技能加载 | 角色专业知识（后续引入） |

**Conductor 的定位**：整合者 + 产品化 + 自治循环

## 与 claude-code-bot 集成

### 背景

[claude-code-bot](https://github.com/slicenferqin/claude-code-bot) 是一个飞书机器人，支持：
- 飞书 WebSocket 长连接（双向通信）
- 接收用户消息并执行 Claude Code 任务
- 支持命令交互（ok/no/cancel/diff/commit 等）

**问题**：普通的 Webhook 通知只能单向推送，无法接收用户回复（如 Plan 确认）。

### 集成方案：claude-code-bot 作为入口

```
用户 → 飞书 → claude-code-bot → 判断任务复杂度
                    │
           ┌───────┴───────┐
           ↓               ↓
      简单任务          复杂任务
           │               │
           ↓               ↓
    直接执行          conductor.execute()
           │               │
           ↓               ↓
           └───────┬───────┘
                   ↓
             结果返回飞书
```

### 职责划分

| 组件 | 职责 |
|------|------|
| **claude-code-bot** | 飞书通信、任务分发、用户交互 |
| **Conductor** | 复杂任务执行、自治循环、进度管理 |

### 接口设计

```python
# claude-code-bot 调用 Conductor

class ConductorClient:
    """Conductor 客户端，供 claude-code-bot 调用"""

    async def execute(
        self,
        requirement: str,
        on_plan_ready: Callable[[Plan], Awaitable[bool]],  # Plan 确认回调
        on_progress: Callable[[Progress], None],           # 进度更新回调
        on_need_help: Callable[[HelpRequest], Awaitable[str]],  # 需要帮助回调
    ) -> ExecutionResult:
        """执行复杂任务

        Args:
            requirement: 需求描述
            on_plan_ready: Plan 生成后的回调，返回 True 确认，False 取消
            on_progress: 进度更新回调
            on_need_help: 需要人工介入时的回调

        Returns:
            执行结果
        """
        pass
```

```python
# claude-code-bot 中的使用

class Bot:
    async def handle_task(self, prompt: str, chat_id: str):
        if self.is_complex_task(prompt):
            # 复杂任务交给 Conductor
            result = await self.conductor.execute(
                requirement=prompt,
                on_plan_ready=lambda plan: self.request_confirm(chat_id, plan),
                on_progress=lambda p: self.send_progress(chat_id, p),
                on_need_help=lambda h: self.request_help(chat_id, h),
            )
        else:
            # 简单任务直接执行
            result = await self.claude_cli.execute(prompt)

        self.send_to_feishu(chat_id, result)

    def is_complex_task(self, prompt: str) -> bool:
        """判断是否为复杂任务

        复杂任务特征：
        - 包含"项目"、"应用"、"系统"等关键词
        - 需要多个文件/模块
        - 需要前后端配合
        """
        complex_keywords = ["项目", "应用", "系统", "网站", "APP", "小程序"]
        return any(kw in prompt for kw in complex_keywords)
```

### 通信流程

```
1. 用户在飞书发送: "做一个待办清单应用"

2. claude-code-bot 判断为复杂任务，调用 Conductor

3. Conductor 生成 Plan，通过回调通知 claude-code-bot

4. claude-code-bot 将 Plan 发送到飞书，等待用户确认

5. 用户回复 "ok"

6. claude-code-bot 通过回调告知 Conductor 继续执行

7. Conductor 执行各阶段，定期通过回调更新进度

8. claude-code-bot 将进度推送到飞书

9. 完成后，Conductor 通过回调返回结果

10. claude-code-bot 将结果发送到飞书
```

### MVP 简化方案

初期可以不改造 claude-code-bot，Conductor 独立运行：

```
方案 A（完整集成）：
  飞书 ↔ claude-code-bot ↔ Conductor

方案 B（MVP 简化）：
  CLI → Conductor（本地执行）
  飞书 ← Conductor（单向通知）

  Plan 确认通过 CLI 交互：
  $ conductor submit "待办清单"
  [显示 Plan]
  确认执行? [y/n]: y
```

后续再实现 claude-code-bot 完整集成。

## MVP 范围

### 包含

- [x] 后台服务（daemon 模式）
- [x] CLI 客户端（submit/status/pull）
- [x] Plan 检查点（必须确认）
- [x] 自治循环（测试 → 修复）
- [x] 微信通知（或飞书）
- [x] 单一技术栈：Python + React + PostgreSQL

### 不包含（后续迭代）

- [ ] Web 界面
- [ ] 多技术栈支持
- [ ] 多用户/团队
- [ ] 自定义模板
- [ ] 成本预估和控制

## 验收标准

### 场景：待办清单应用

**输入**：
```
做一个待办清单应用，要求：
1. 用户注册、登录、登出
2. 任务的增删改查
3. 任务可以标记完成/未完成
```

**验收**：

| # | 检查项 | 标准 |
|---|--------|------|
| 1 | Plan 推送 | 手机收到 Plan，可确认/调整 |
| 2 | 后台执行 | 确认后自动执行，不需要人盯 |
| 3 | 进度通知 | 关键节点推送进度 |
| 4 | 自动测试 | 测试失败自动修复 |
| 5 | 完成通知 | 手机收到完成通知 |
| 6 | 代码可用 | docker-compose up 可运行 |
| 7 | 测试通过 | 所有测试用例通过 |

## 里程碑

### Phase 1: 核心功能
- 后台服务框架
- Claude Code 集成
- 任务队列和执行引擎
- 自治循环（测试 → 修复）
- CLI 客户端
- 微信/飞书通知

### Phase 2: 体验优化
- Web 界面
- 更多通知渠道
- 成本监控
- 任务历史

### Phase 3: 扩展
- 多技术栈
- 自定义模板
- 团队协作

---

*文档更新日期：2024-12-30*