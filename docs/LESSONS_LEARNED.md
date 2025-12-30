# Claude Code Bot 经验总结

> 本文档总结了 claude-code-bot 项目开发过程中积累的经验教训，供后续项目（如 conductor）参考。

## 1. Claude Code CLI 使用经验

### 1.1 基本调用方式

```bash
# 最简单的调用
claude --print "你的任务"

# 带会话 ID（保持上下文）
claude --print "你的任务" --session-id "your-session-id"

# 恢复会话
claude --print "继续之前的任务" --resume "your-session-id"

# 流式 JSON 输出（推荐，便于解析）
claude --print "你的任务" --output-format stream-json

# 跳过权限确认（危险但目前必须）
claude --print "你的任务" --dangerously-skip-permissions
```

### 1.2 输出格式

`--output-format stream-json` 会输出多行 JSON，每行一个消息：

```json
{"type":"system","message":"..."}
{"type":"assistant","message":{"role":"assistant","content":"思考中..."}}
{"type":"tool_use","tool":"Read","input":{"file_path":"/path/to/file"}}
{"type":"tool_result","tool":"Read","output":"文件内容..."}
{"type":"result","result":"最终结果..."}
```

### 1.3 重要参数

| 参数 | 说明 |
|------|------|
| `--print` | 非交互模式，执行完退出 |
| `--session-id` | 指定会话 ID |
| `--resume` | 恢复已有会话 |
| `--output-format stream-json` | 流式 JSON 输出 |
| `--dangerously-skip-permissions` | 跳过所有权限确认 |
| `--allowedTools "Read,Glob,Grep"` | 预授权特定工具 |
| `--verbose` | 详细输出 |

---

## 2. 已知的坑和限制

### 2.1 Hook 在 --print 模式下不触发

**问题**：Claude Code 的 Hook 机制只在交互式终端模式下工作，`--print` 模式下不会触发任何 Hook。

**影响**：无法通过 Hook 实现：
- 实时进度推送
- 权限请求拦截
- 任务完成通知

**解决方案**：
- 解析 `--output-format stream-json` 的输出来获取进度
- 使用 `--dangerously-skip-permissions` 跳过权限
- 或使用 `--allowedTools` 预授权

### 2.2 SDK can_use_tool 回调不工作

**问题**：Claude Code SDK 的 `can_use_tool` 权限回调从不触发。

**错误信息**：
```
Tool permission request failed: Error: Stream closed
```

**根因**：这是 CLI 本身的 bug（GitHub issue 已提交，状态 open）。CLI 在请求权限时，通信管道会意外关闭。

**影响**：
- SDK 的权限控制功能完全不可用
- CLI 可能在后台无限重试，消耗大量 token

**解决方案**：
- 暂时使用 `--dangerously-skip-permissions`
- 等官方修复
- 或使用双阶段执行方案（见下文）

### 2.3 stream-json 输入格式

**问题**：`--input-format stream-json` 需要特定格式。

**正确格式**：
```json
{"type": "user", "message": {"role": "user", "content": "你的消息"}}
```

**错误格式**：
```json
{"role": "user", "content": "你的消息"}  // 缺少 type 和 message 包装
```

### 2.4 Hook 配置格式变更

**问题**：Claude Code 更新后，Hook 配置格式发生变化。

**旧格式（不工作）**：
```json
{
  "Stop": [{
    "matcher": {},  // 空对象会报错
    "hooks": [...]
  }]
}
```

**新格式（正确）**：
```json
{
  "Stop": [{
    "hooks": [...]  // 不指定 matcher 表示匹配所有
  }]
}
```

或使用字符串 matcher：
```json
{
  "PostToolUse": [{
    "matcher": "Bash",  // 只匹配 Bash 工具
    "hooks": [...]
  }]
}
```

---

## 3. 权限控制方案对比

| 方案 | 可行性 | 说明 |
|------|--------|------|
| SDK `can_use_tool` | ❌ 不工作 | CLI bug，Stream closed |
| CLI Hook | ❌ --print 模式不触发 | 只在交互模式工作 |
| `--dangerously-skip-permissions` | ✅ 可用 | 跳过所有权限，有安全风险 |
| `--allowedTools` 预授权 | ✅ 可用 | 只允许指定工具 |
| 双阶段执行 | ✅ 可用 | 先探索后执行 |

### 3.1 双阶段执行方案

```
第一阶段：只读探索
    claude --print "分析任务" --allowedTools "Read,Glob,Grep"
    → 输出需要执行的操作列表
    ↓
用户确认
    ↓
第二阶段：授权执行
    claude --print "执行任务" --resume session-id --allowedTools "Read,Write,Edit,Bash"
```

---

## 4. Python 集成经验

### 4.1 subprocess 调用（推荐）

```python
import subprocess
import json

def call_claude(prompt: str, session_id: str, workspace: str) -> list:
    """调用 Claude Code CLI"""
    cmd = [
        "claude",
        "--print", prompt,
        "--session-id", session_id,
        "--output-format", "stream-json",
        "--dangerously-skip-permissions",
    ]

    process = subprocess.Popen(
        cmd,
        cwd=workspace,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    messages = []
    for line in process.stdout:
        line = line.strip()
        if line:
            try:
                msg = json.loads(line)
                messages.append(msg)
                # 实时处理消息
                handle_message(msg)
            except json.JSONDecodeError:
                pass

    process.wait()
    return messages

def handle_message(msg: dict):
    """处理单条消息"""
    msg_type = msg.get("type")

    if msg_type == "assistant":
        # Claude 的文本回复
        content = msg.get("message", {}).get("content", "")
        print(f"Claude: {content}")

    elif msg_type == "tool_use":
        # 工具调用
        tool = msg.get("tool")
        print(f"使用工具: {tool}")

    elif msg_type == "result":
        # 最终结果
        result = msg.get("result")
        print(f"完成: {result}")
```

### 4.2 异步调用

```python
import asyncio
import subprocess

async def call_claude_async(prompt: str, session_id: str, workspace: str):
    """异步调用 Claude Code CLI"""
    cmd = [
        "claude",
        "--print", prompt,
        "--session-id", session_id,
        "--output-format", "stream-json",
        "--dangerously-skip-permissions",
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=workspace,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    async for line in process.stdout:
        line = line.decode().strip()
        if line:
            try:
                msg = json.loads(line)
                yield msg
            except json.JSONDecodeError:
                pass

    await process.wait()
```

### 4.3 多进程管理

```python
class SessionManager:
    """管理多个 Claude 会话"""

    def __init__(self):
        self.sessions: Dict[str, subprocess.Popen] = {}

    def start_session(self, session_id: str, prompt: str, workspace: str) -> subprocess.Popen:
        """启动新会话"""
        if session_id in self.sessions:
            self.stop_session(session_id)

        process = subprocess.Popen(
            [
                "claude",
                "--print", prompt,
                "--session-id", session_id,
                "--output-format", "stream-json",
                "--dangerously-skip-permissions",
            ],
            cwd=workspace,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        self.sessions[session_id] = process
        return process

    def stop_session(self, session_id: str):
        """停止会话"""
        if session_id in self.sessions:
            process = self.sessions[session_id]
            process.terminate()
            process.wait(timeout=5)
            del self.sessions[session_id]

    def stop_all(self):
        """停止所有会话"""
        for session_id in list(self.sessions.keys()):
            self.stop_session(session_id)
```

---

## 5. 通信方案经验

### 5.1 文件系统通信（推荐用于多会话协同）

**优点**：
- 简单可靠
- 人类可读
- Git 可追踪
- 无需额外依赖

**实现**：
```python
# 写状态
def update_progress(session_id: str, status: str, output: list):
    progress_file = ".workspace/progress.json"
    with open(progress_file, "r+") as f:
        data = json.load(f)
        data[session_id] = {
            "status": status,
            "output": output,
            "updated_at": datetime.now().isoformat()
        }
        f.seek(0)
        json.dump(data, f, indent=2)
        f.truncate()

# 读状态
def get_progress(session_id: str) -> dict:
    with open(".workspace/progress.json") as f:
        data = json.load(f)
        return data.get(session_id, {})

# 检查依赖
def wait_for_dependency(depends_on: str, timeout: int = 1800):
    start = time.time()
    while time.time() - start < timeout:
        progress = get_progress(depends_on)
        if progress.get("status") == "completed":
            return True
        time.sleep(30)  # 每 30 秒检查一次
    return False
```

### 5.2 IPC 通信（用于实时通知）

**场景**：Bot 需要实时接收 CLI 的进度更新

**实现**：Unix Domain Socket

```python
# 服务端 (Bot)
import socket
import os

SOCKET_PATH = "/tmp/conductor.sock"

def start_ipc_server():
    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(SOCKET_PATH)
    server.listen(5)

    while True:
        conn, _ = server.accept()
        data = conn.recv(4096).decode()
        message = json.loads(data)
        handle_ipc_message(message)
        conn.close()

# 客户端 (Hook 脚本)
def send_ipc_message(message: dict):
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(SOCKET_PATH)
    client.send(json.dumps(message).encode())
    client.close()
```

---

## 6. 飞书集成经验

### 6.1 长连接模式

使用飞书的 WebSocket 长连接而非 Webhook，无需公网服务器：

```python
from lark_oapi.ws import Client

def start_feishu():
    client = Client(
        app_id="your_app_id",
        app_secret="your_app_secret",
    )

    @client.on("im.message.receive_v1")
    def on_message(event):
        # 处理消息
        pass

    client.start()
```

### 6.2 消息格式化

```python
def format_progress_message(tool: str, status: str) -> str:
    emoji = {
        "running": "🔄",
        "completed": "✅",
        "failed": "❌",
    }.get(status, "📍")

    return f"{emoji} {tool}: {status}"

def format_result_message(result: str, files: list) -> str:
    msg = f"✅ 任务完成\n\n{result}\n"

    if files:
        msg += "\n修改的文件:\n"
        for f in files:
            msg += f"  - {f}\n"

    return msg
```

---

## 7. 架构建议

### 7.1 对于 Conductor 项目

```
conductor/
├── coordinator/           # 秘书协调器
│   ├── planner.py         # 任务分解
│   ├── scheduler.py       # 角色调度
│   └── monitor.py         # 进度监控
│
├── sessions/              # 会话管理
│   ├── manager.py         # 多会话管理
│   ├── claude_cli.py      # CLI 调用封装
│   └── communication.py   # 会话间通信
│
├── roles/                 # 角色定义
│   ├── base.py            # 角色基类
│   ├── pm.py              # 产品经理
│   ├── architect.py       # 架构师
│   ├── developer.py       # 开发者
│   └── tester.py          # 测试工程师
│
├── skills/                # 角色技能配置
│   ├── pm/
│   ├── architect/
│   ├── backend_java/
│   ├── backend_python/
│   ├── frontend_react/
│   └── tester/
│
├── workspace/             # 工作区管理
│   ├── initializer.py     # 初始化项目结构
│   ├── git_ops.py         # Git 操作
│   └── file_lock.py       # 文件锁
│
└── config.yaml            # 配置文件
```

### 7.2 关键设计原则

1. **状态持久化**：每个会话定期保存状态到文件，支持断点恢复
2. **松耦合通信**：使用文件系统而非直接进程间通信
3. **幂等操作**：同一任务重复执行应产生相同结果
4. **人工介入点**：关键决策处暂停等待确认
5. **完整日志**：所有操作记录到文件，便于调试和审计

---

## 8. 待解决的问题

1. **CLI 权限 bug**：等待官方修复 `can_use_tool` 回调
2. **长时间任务稳定性**：需要实现心跳检测和自动重启
3. **并发写冲突**：多会话同时修改同一文件的处理
4. **Token 消耗监控**：防止单会话消耗过多 token

---

## 9. 参考资源

- [Claude Code 官方文档](https://docs.anthropic.com/en/docs/claude-code)
- [Claude Code SDK](https://www.npmjs.com/package/@anthropic-ai/claude-code-sdk)
- [Hooks 配置文档](https://code.claude.com/docs/en/hooks)
- [GitHub Issue: Stream closed bug](https://github.com/anthropics/claude-code/issues) (搜索 "Stream closed")

---

*文档更新日期：2024-12-24*
*基于 claude-code-bot V2 开发经验*