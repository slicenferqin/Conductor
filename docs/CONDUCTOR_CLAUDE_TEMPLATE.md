# CLAUDE.md (Conductor 项目模板)

> 复制此文件到 conductor 项目根目录作为 CLAUDE.md

## 项目概述

Conductor 是一个多会话 Agent 协同系统，使用单一智能体（Claude）的多实例协同完成复杂的软件开发任务。

### 核心架构

```
用户 → 秘书会话(Master) → 分发任务 → 多个角色会话
                                    ├── PM（需求分析）
                                    ├── 架构师（系统设计）
                                    ├── 后端开发
                                    ├── 前端开发
                                    └── 测试工程师
```

### 通信方式

- **会话间**：文件系统（.workspace/ 目录下的 JSON 文件）
- **状态同步**：progress.json（轮询模式）
- **消息传递**：messages.json（追加模式）
- **依赖管理**：dependencies.json（检查点模式）

## 命令

```bash
# 安装依赖
pip install -r requirements.txt

# 启动协调器
python main.py

# 启动单个角色会话（调试用）
python -m conductor.sessions.manager --role pm --task "分析需求"
```

## 关键经验（来自 claude-code-bot）

### Claude Code CLI 使用

```bash
# 推荐的调用方式
claude --print "任务" \
    --session-id "unique-id" \
    --output-format stream-json \
    --dangerously-skip-permissions
```

### 已知限制

1. **--print 模式下 Hook 不触发** - 无法用 Hook 做权限控制
2. **SDK can_use_tool 有 bug** - 暂时不可用，等官方修复
3. **必须用 --dangerously-skip-permissions** - 否则权限请求会导致 Stream closed

### stream-json 输入格式

```json
{"type": "user", "message": {"role": "user", "content": "你的消息"}}
```

## 目录结构

```
conductor/
├── CLAUDE.md              # 本文件
├── config.yaml            # 配置
├── main.py                # 入口
│
├── coordinator/           # 秘书协调器
│   ├── planner.py         # 任务分解
│   ├── scheduler.py       # 角色调度
│   └── monitor.py         # 进度监控
│
├── sessions/              # 会话管理
│   ├── manager.py         # 多会话管理
│   └── claude_cli.py      # CLI 调用封装
│
├── roles/                 # 角色定义
│   └── base.py            # 角色基类
│
├── skills/                # 角色技能配置（Markdown）
│   ├── secretary/
│   ├── pm/
│   ├── architect/
│   ├── backend_java/
│   ├── backend_python/
│   ├── frontend_react/
│   ├── frontend_vue/
│   └── tester/
│
└── .workspace/            # 运行时工作区（Git 忽略）
    ├── coordinator.json   # 秘书状态
    ├── progress.json      # 各角色进度
    ├── messages.json      # 会话间消息
    └── dependencies.json  # 任务依赖
```

## 开发规范

### 会话管理

```python
# 启动会话
process = subprocess.Popen(
    ["claude", "--print", prompt, "--session-id", session_id,
     "--output-format", "stream-json", "--dangerously-skip-permissions"],
    cwd=workspace,
    stdout=subprocess.PIPE,
    text=True,
)

# 解析输出
for line in process.stdout:
    msg = json.loads(line.strip())
    if msg["type"] == "result":
        # 任务完成
        pass
```

### 进度更新

```python
# 更新自己的进度
def update_progress(role: str, status: str, output: list):
    with open(".workspace/progress.json", "r+") as f:
        data = json.load(f)
        data[role] = {"status": status, "output": output}
        f.seek(0)
        json.dump(data, f, indent=2)
        f.truncate()

# 检查依赖是否完成
def check_dependency(depends_on: str) -> bool:
    with open(".workspace/progress.json") as f:
        data = json.load(f)
        return data.get(depends_on, {}).get("status") == "completed"
```

### 会话间消息

```python
# 发送消息
def send_message(from_role: str, to_role: str, content: str):
    with open(".workspace/messages.json", "r+") as f:
        data = json.load(f)
        data["messages"].append({
            "from": from_role,
            "to": to_role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        f.seek(0)
        json.dump(data, f, indent=2)

# 读取消息
def get_messages(role: str) -> list:
    with open(".workspace/messages.json") as f:
        data = json.load(f)
        return [m for m in data["messages"] if m["to"] == role]
```

## Skills 配置

每个角色的 skills 文件夹包含该角色的专业知识：

```markdown
# skills/backend_java/spring_boot.md

## Spring Boot 最佳实践

### 项目结构
- controller/ - REST 控制器
- service/ - 业务逻辑
- repository/ - 数据访问
- entity/ - 实体类
- dto/ - 数据传输对象

### 代码规范
- 使用 @RestController 而非 @Controller
- Service 层使用接口 + 实现类
- 异常使用 @ControllerAdvice 统一处理
...
```

## 注意事项

1. **状态持久化** - 每次重要操作后更新 progress.json
2. **幂等性** - 任务可以安全重复执行
3. **超时处理** - 等待依赖时设置合理超时（建议 30 分钟）
4. **日志记录** - 所有操作记录日志，便于调试
5. **Git 追踪** - 代码文件用 Git 管理，可以回滚

## 参考

- [经验总结文档](./docs/LESSONS_LEARNED.md)
- [Claude Code 文档](https://docs.anthropic.com/en/docs/claude-code)