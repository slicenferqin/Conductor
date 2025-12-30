"""Task Decomposer - Breaks down requirements into actionable plan using Claude."""

import json
import re
from dataclasses import dataclass, field
from typing import Any

from conductor.integrations.claude_cli import ClaudeCodeCLI


@dataclass
class Plan:
    """A development plan."""
    requirement: str
    summary: str
    features: list[str]
    tech_stack: dict[str, str]
    stages: list[dict[str, Any]]
    estimated_time: str
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "requirement": self.requirement,
            "summary": self.summary,
            "features": self.features,
            "tech_stack": self.tech_stack,
            "stages": self.stages,
            "estimated_time": self.estimated_time,
            "warnings": self.warnings,
        }

    def format_for_display(self) -> str:
        """Format plan for terminal display."""
        lines = []
        lines.append(f"\n{'━' * 50}")
        lines.append(f"📋 项目计划: {self.summary}")
        lines.append(f"{'━' * 50}")

        lines.append("\n📝 功能列表:")
        for feature in self.features:
            lines.append(f"   ✓ {feature}")

        lines.append("\n🔧 技术栈:")
        for key, value in self.tech_stack.items():
            lines.append(f"   • {key}: {value}")

        lines.append("\n📅 执行阶段:")
        for i, stage in enumerate(self.stages, 1):
            lines.append(f"   {i}. {stage['name']}: {stage['description']}")

        lines.append(f"\n⏱️  预计时间: {self.estimated_time}")

        if self.warnings:
            lines.append("\n⚠️  注意事项:")
            for warning in self.warnings:
                lines.append(f"   • {warning}")

        lines.append(f"{'━' * 50}\n")

        return "\n".join(lines)


# Plan generation prompt template
PLAN_PROMPT = '''分析以下需求，生成开发计划。

需求：
{requirement}

技术栈（固定）：
- 后端：FastAPI + SQLAlchemy + PostgreSQL
- 前端：React + TypeScript + TailwindCSS
- 测试：pytest + Playwright
- 部署：Docker + docker-compose

请以 JSON 格式输出开发计划，格式如下：
```json
{{
    "summary": "项目一句话描述",
    "features": [
        "功能1",
        "功能2"
    ],
    "stages": [
        {{
            "name": "设计",
            "description": "PRD、架构设计、API设计、数据库设计",
            "outputs": ["docs/prd.md", "docs/architecture.md", "docs/api_design.md"]
        }},
        {{
            "name": "后端开发",
            "description": "实现 API 接口",
            "outputs": ["backend/"]
        }},
        {{
            "name": "前端开发",
            "description": "实现用户界面",
            "outputs": ["frontend/"]
        }},
        {{
            "name": "测试",
            "description": "单元测试和集成测试",
            "outputs": ["tests/"]
        }},
        {{
            "name": "部署配置",
            "description": "Docker 配置",
            "outputs": ["docker-compose.yml", "Dockerfile"]
        }}
    ],
    "estimated_time": "15-20 分钟",
    "warnings": [
        "可能需要的注意事项"
    ]
}}
```

只输出 JSON，不要其他内容。'''


class TaskDecomposer:
    """Decomposes requirements into development plans."""

    # Fixed tech stack for MVP
    DEFAULT_TECH_STACK = {
        "后端": "FastAPI + SQLAlchemy + PostgreSQL",
        "前端": "React + TypeScript + TailwindCSS",
        "测试": "pytest + Playwright",
        "部署": "Docker + docker-compose",
    }

    def __init__(self, workspace: str):
        """Initialize decomposer.

        Args:
            workspace: Working directory for Claude Code
        """
        self.workspace = workspace
        self.claude = ClaudeCodeCLI(workspace)

    async def decompose(self, requirement: str) -> Plan:
        """Decompose a requirement into a development plan.

        Args:
            requirement: The project requirement

        Returns:
            A Plan object
        """
        prompt = PLAN_PROMPT.format(requirement=requirement)

        # Call Claude to generate plan
        messages = await self.claude.execute_and_wait(
            prompt=prompt,
            allowed_tools=["Read", "Glob", "Grep"],  # Read-only tools for analysis
        )

        # Extract the result
        plan_data = self._extract_plan_from_messages(messages)

        return Plan(
            requirement=requirement,
            summary=plan_data.get("summary", "项目开发"),
            features=plan_data.get("features", []),
            tech_stack=self.DEFAULT_TECH_STACK,
            stages=plan_data.get("stages", self._default_stages()),
            estimated_time=plan_data.get("estimated_time", "15-20 分钟"),
            warnings=plan_data.get("warnings", []),
        )

    def _extract_plan_from_messages(self, messages: list) -> dict[str, Any]:
        """Extract plan data from Claude messages."""
        for msg in reversed(messages):
            if msg.type == "result":
                return self._parse_plan_json(msg.content.get("result", ""))
            elif msg.type == "assistant":
                content = msg.content.get("message", {}).get("content", "")
                if isinstance(content, str):
                    result = self._parse_plan_json(content)
                    if result:
                        return result

        # Fallback to default plan
        return {}

    def _parse_plan_json(self, text: str) -> dict[str, Any]:
        """Parse JSON from text that might contain markdown code blocks."""
        if not text:
            return {}

        # Try to extract JSON from code blocks
        json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if json_match:
            text = json_match.group(1)

        # Try to parse as JSON
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            # Try to find JSON object in text
            json_obj_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_obj_match:
                try:
                    return json.loads(json_obj_match.group())
                except json.JSONDecodeError:
                    pass

        return {}

    def _default_stages(self) -> list[dict[str, Any]]:
        """Return default stages if parsing fails."""
        return [
            {
                "name": "设计",
                "description": "PRD、架构设计、API设计、数据库设计",
                "outputs": ["docs/prd.md", "docs/architecture.md", "docs/api_design.md"],
            },
            {
                "name": "后端开发",
                "description": "实现 FastAPI 后端接口",
                "outputs": ["backend/"],
            },
            {
                "name": "前端开发",
                "description": "实现 React 前端界面",
                "outputs": ["frontend/"],
            },
            {
                "name": "测试",
                "description": "单元测试和端到端测试",
                "outputs": ["tests/"],
            },
            {
                "name": "部署配置",
                "description": "Docker 和 docker-compose 配置",
                "outputs": ["docker-compose.yml"],
            },
        ]