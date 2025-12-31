"""Task Executor - Orchestrates Claude Code sessions with autonomous loop."""

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

from conductor.integrations.claude_cli import ClaudeCodeCLI
from conductor.core.decomposer import Plan


class StageStatus(Enum):
    """Stage execution status."""
    PENDING = "pending"
    RUNNING = "running"
    TESTING = "testing"
    FIXING = "fixing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class StageResult:
    """Result of a stage execution."""
    stage_name: str
    status: StageStatus
    output: str | None = None
    error: str | None = None
    fix_attempts: int = 0


@dataclass
class ExecutionProgress:
    """Execution progress information."""
    current_stage: str
    stage_index: int
    total_stages: int
    status: StageStatus
    message: str
    percentage: int

    def format_for_display(self) -> str:
        """Format progress for terminal display."""
        bar_width = 30
        filled = int(bar_width * self.percentage / 100)
        bar = "=" * filled + ">" + " " * (bar_width - filled - 1)
        return f"[{bar}] {self.percentage}% - {self.current_stage}: {self.message}"


# Stage execution prompts
STAGE_PROMPTS = {
    "设计": '''作为架构师，为以下项目创建设计文档。

项目需求：
{requirement}

功能列表：
{features}

技术栈：
- 后端：FastAPI + SQLAlchemy + PostgreSQL
- 前端：React + TypeScript + TailwindCSS

请创建以下文档：
1. docs/prd.md - 产品需求文档
2. docs/architecture.md - 架构设计文档
3. docs/api_design.md - API 设计文档（包含所有接口定义）

确保 API 设计包含完整的请求/响应格式。''',

    "后端开发": '''作为后端开发者，实现 FastAPI 后端。

参考设计文档 docs/api_design.md 中的 API 定义。

技术要求：
- FastAPI + SQLAlchemy 2.0 + PostgreSQL
- JWT 认证
- Pydantic 模型验证
- 完整的错误处理

请创建完整的后端项目结构：
backend/
├── app/
│   ├── main.py          # FastAPI 入口
│   ├── config.py        # 配置
│   ├── database.py      # 数据库连接
│   ├── models/          # SQLAlchemy 模型
│   ├── schemas/         # Pydantic 模式
│   ├── api/             # API 路由
│   └── services/        # 业务逻辑
├── requirements.txt
└── Dockerfile

实现所有 API 接口，确保代码可运行。''',

    "前端开发": '''作为前端开发者，实现 React 前端。

参考：
- docs/prd.md 中的功能需求
- docs/api_design.md 中的 API 定义

技术要求：
- React 18 + TypeScript
- TailwindCSS 样式
- Zustand 状态管理
- Axios 请求

请创建完整的前端项目结构：
frontend/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── components/      # 通用组件
│   ├── pages/           # 页面组件
│   ├── stores/          # Zustand stores
│   ├── services/        # API 调用
│   └── types/           # TypeScript 类型
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── Dockerfile

实现所有页面，确保与后端 API 对接。''',

    "测试": '''作为测试工程师，为项目编写测试。

测试要求：
1. 后端单元测试（pytest）
   - 测试所有 API 接口
   - 测试认证流程
   - 使用 pytest-asyncio

2. 端到端测试（Playwright）
   - 测试核心用户流程
   - 测试页面交互

创建测试文件：
tests/
├── backend/
│   ├── conftest.py
│   ├── test_api.py
│   └── test_auth.py
└── e2e/
    └── test_app.spec.ts

确保测试覆盖主要功能。''',

    "部署配置": '''创建 Docker 部署配置。

创建以下文件：

1. docker-compose.yml - 包含：
   - PostgreSQL 数据库
   - 后端服务
   - 前端服务
   - 网络配置

2. .env.example - 环境变量示例

3. README.md - 项目说明，包含：
   - 项目介绍
   - 快速启动指南
   - API 文档链接
   - 开发说明

确保 docker-compose up 可以一键启动整个项目。''',
}

TEST_PROMPT = '''运行测试并报告结果。

执行以下测试：
1. 后端测试：cd backend && pytest -v
2. 检查后端代码语法：cd backend && python -m py_compile app/main.py

报告测试结果，如果有失败，详细说明失败原因。'''

FIX_PROMPT = '''测试失败，请修复问题。

错误信息：
{error}

请分析错误原因并修复代码。修复后说明做了哪些修改。'''


class TaskExecutor:
    """Executes tasks through multiple stages with autonomous loop."""

    def __init__(
        self,
        workspace: str,
        max_fix_attempts: int = 3,
        on_progress: Callable[[ExecutionProgress], None] | None = None,
    ) -> None:
        """Initialize executor.

        Args:
            workspace: Working directory for the project
            max_fix_attempts: Maximum auto-fix attempts per stage
            on_progress: Callback for progress updates
        """
        self.workspace = workspace
        self.max_fix_attempts = max_fix_attempts
        self.on_progress = on_progress
        self.claude = ClaudeCodeCLI(workspace)

    async def execute(self, plan: Plan) -> list[StageResult]:
        """Execute all stages in the plan.

        Each stage runs as an independent Claude session (agent).
        Agents communicate via the file system - each stage reads
        outputs from previous stages and writes its own outputs.

        Args:
            plan: The development plan

        Returns:
            List of stage results
        """
        results: list[StageResult] = []
        stages = [s["name"] for s in plan.stages]

        for i, stage in enumerate(plan.stages):
            stage_name = stage["name"]

            # Report progress
            self._report_progress(
                stage_name=stage_name,
                stage_index=i,
                total_stages=len(stages),
                status=StageStatus.RUNNING,
                message="执行中...",
            )

            # Execute stage with autonomous loop
            result = await self._execute_stage_with_loop(
                stage_name=stage_name,
                stage_index=i,
                total_stages=len(stages),
                plan=plan,
            )

            results.append(result)

            # Stop if stage failed
            if result.status == StageStatus.FAILED:
                break

            # Report completion
            self._report_progress(
                stage_name=stage_name,
                stage_index=i,
                total_stages=len(stages),
                status=StageStatus.COMPLETED,
                message="完成",
            )

        return results

    async def _execute_stage_with_loop(
        self,
        stage_name: str,
        stage_index: int,
        total_stages: int,
        plan: Plan,
    ) -> StageResult:
        """Execute a single stage with test-fix loop.

        Args:
            stage_name: Name of the stage
            stage_index: Index of the stage
            total_stages: Total number of stages
            plan: The development plan

        Returns:
            Stage result
        """
        fix_attempts = 0

        # Execute the stage
        prompt = self._get_stage_prompt(stage_name, plan)
        await self._execute_claude(prompt)

        # For development stages, run test-fix loop
        if stage_name in ["后端开发", "前端开发"]:
            while fix_attempts < self.max_fix_attempts:
                # Run tests
                self._report_progress(
                    stage_name=stage_name,
                    stage_index=stage_index,
                    total_stages=total_stages,
                    status=StageStatus.TESTING,
                    message=f"运行测试 (尝试 {fix_attempts + 1}/{self.max_fix_attempts})...",
                )

                test_result = await self._run_tests()

                if test_result["passed"]:
                    return StageResult(
                        stage_name=stage_name,
                        status=StageStatus.COMPLETED,
                        fix_attempts=fix_attempts,
                    )

                # Try to fix
                fix_attempts += 1

                if fix_attempts >= self.max_fix_attempts:
                    return StageResult(
                        stage_name=stage_name,
                        status=StageStatus.FAILED,
                        error=test_result.get("error", "测试失败"),
                        fix_attempts=fix_attempts,
                    )

                self._report_progress(
                    stage_name=stage_name,
                    stage_index=stage_index,
                    total_stages=total_stages,
                    status=StageStatus.FIXING,
                    message=f"自动修复中 ({fix_attempts}/{self.max_fix_attempts})...",
                )

                await self._auto_fix(test_result.get("error", ""))

        return StageResult(
            stage_name=stage_name,
            status=StageStatus.COMPLETED,
            fix_attempts=fix_attempts,
        )

    def _get_stage_prompt(self, stage_name: str, plan: Plan) -> str:
        """Get the prompt for a stage."""
        template = STAGE_PROMPTS.get(stage_name, "执行 {stage_name} 阶段")

        return template.format(
            requirement=plan.requirement,
            features="\n".join(f"- {f}" for f in plan.features),
            stage_name=stage_name,
        )

    async def _execute_claude(self, prompt: str) -> list[Any]:
        """Execute a prompt with Claude as an independent session."""
        messages = await self.claude.execute_and_wait(prompt=prompt)

        if not messages:
            raise RuntimeError("Claude CLI 未返回任何结果，请检查 claude 命令是否可用")

        # Check for errors in result
        for msg in messages:
            if msg.type == "result" and msg.content.get("is_error"):
                raise RuntimeError(f"Claude 执行出错: {msg.content.get('result', '未知错误')}")

        return messages

    async def _run_tests(self) -> dict[str, Any]:
        """Run tests and return results."""
        messages = await self.claude.execute_and_wait(prompt=TEST_PROMPT)

        if not messages:
            return {"passed": False, "error": "Claude CLI 未返回任何结果"}

        # Parse test results from messages
        for msg in reversed(messages):
            if msg.type == "result":
                result_text = msg.content.get("result", "")
                # Simple heuristic: check for failure indicators
                if any(word in result_text.lower() for word in ["fail", "error", "failed"]):
                    return {"passed": False, "error": result_text}
                return {"passed": True}

        return {"passed": False, "error": "未找到测试结果"}

    async def _auto_fix(self, error: str) -> None:
        """Attempt to automatically fix an error."""
        prompt = FIX_PROMPT.format(error=error)
        await self.claude.execute_and_wait(prompt=prompt)

    def _report_progress(
        self,
        stage_name: str,
        stage_index: int,
        total_stages: int,
        status: StageStatus,
        message: str,
    ) -> None:
        """Report progress to callback."""
        if self.on_progress:
            progress = ExecutionProgress(
                current_stage=stage_name,
                stage_index=stage_index,
                total_stages=total_stages,
                status=status,
                message=message,
                percentage=int((stage_index + (0.5 if status == StageStatus.RUNNING else 1)) / total_stages * 100),
            )
            self.on_progress(progress)