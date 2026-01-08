"""Secretary - The coordinator that analyzes requirements and forms teams."""

import json
import re
from pathlib import Path

from conductor.core.models import (
    PREDEFINED_ROLES,
    AgentRole,
    Message,
    Project,
    ProjectStatus,
    TeamConfig,
    TeamMember,
)
from conductor.integrations.claude_cli import ClaudeCodeCLI


class Secretary:
    """Secretary - analyzes requirements and forms teams.

    The Secretary is the coordinator that:
    1. Analyzes user requirements
    2. Decides which roles are needed
    3. Creates the project and workspace
    4. Forms the team
    """

    EMOJI = "🤖"
    NAME = "秘书"

    def __init__(self, base_workspace: str = "./projects"):
        """Initialize Secretary.

        Args:
            base_workspace: Base directory for project workspaces
        """
        self.base_workspace = Path(base_workspace)
        self.base_workspace.mkdir(parents=True, exist_ok=True)

    async def handle_requirement(self, requirement: str) -> Project:
        """Handle a user requirement - analyze and form team.

        Args:
            requirement: The user's requirement text

        Returns:
            A Project with team formed
        """
        # Create project
        project = Project(requirement=requirement)

        # Add initial message
        project.add_message(Message(
            from_id="user",
            from_name="👤 用户",
            content=requirement,
        ))

        project.add_message(Message(
            from_id="secretary",
            from_name=f"{self.EMOJI} {self.NAME}",
            content="好的，我来分析需求并组建团队...",
        ))

        # Analyze requirement and decide team composition
        team_config = await self.analyze_requirement(requirement)

        # Generate project name
        project.name = await self._generate_project_name(requirement)

        # Create workspace
        project.workspace = str(self.base_workspace / f"project-{project.id}")
        Path(project.workspace).mkdir(parents=True, exist_ok=True)

        # Create .conductor directory for metadata
        conductor_dir = Path(project.workspace) / ".conductor"
        conductor_dir.mkdir(exist_ok=True)

        # Form the team
        project.status = ProjectStatus.FORMING
        for role_id in team_config.roles:
            if role_id in PREDEFINED_ROLES:
                role = PREDEFINED_ROLES[role_id]
                member = TeamMember(role=role)
                project.team.append(member)

        # Save team config
        self._save_team_config(project, team_config)

        # Announce team formation
        team_list = "\n".join(
            f"  {m.role.emoji} {m.role.name} - {m.role.description}"
            for m in project.team
        )
        project.add_message(Message(
            from_id="secretary",
            from_name=f"{self.EMOJI} {self.NAME}",
            content=f"团队已组建完成！\n\n📋 项目: {project.name}\n\n👥 团队成员:\n{team_list}\n\n原因: {team_config.reason}",
        ))

        project.status = ProjectStatus.RUNNING

        return project, team_config

    async def analyze_requirement(self, requirement: str) -> TeamConfig:
        """Analyze requirement and decide team composition.

        Args:
            requirement: The user's requirement

        Returns:
            TeamConfig with roles needed
        """
        # Use Claude to analyze the requirement
        cli = ClaudeCodeCLI(str(self.base_workspace))

        available_roles = "\n".join(
            f"- {role.id}: {role.name} - {role.description}"
            for role in PREDEFINED_ROLES.values()
        )

        prompt = f"""分析以下需求，决定需要哪些角色来完成任务。

需求：
{requirement}

可用角色：
{available_roles}

请返回 JSON 格式（只返回 JSON，不要其他内容）：
```json
{{
    "roles": ["role_id1", "role_id2", ...],
    "reason": "选择这些角色的原因",
    "tasks": {{
        "role_id1": "该角色的具体任务描述",
        "role_id2": "该角色的具体任务描述"
    }}
}}
```

注意：
1. 根据需求复杂度选择合适数量的角色
2. 简单任务（如调研、写文档）可能只需要 1-2 个角色
3. 开发任务通常需要 pm, architect, backend, frontend, tester
4. tasks 中描述每个角色的具体任务
"""

        messages = await cli.execute_and_wait(prompt=prompt)

        # Parse the response
        for msg in reversed(messages):
            if msg.type == "result":
                result_text = msg.content.get("result", "")
                return self._parse_team_config(result_text)

        # Fallback to default team
        return self._default_team_config(requirement)

    def _parse_team_config(self, text: str) -> TeamConfig:
        """Parse team config from Claude response."""
        # Try to extract JSON from code blocks
        json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if json_match:
            text = json_match.group(1)

        # Try to find JSON object
        json_obj_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_obj_match:
            try:
                data = json.loads(json_obj_match.group())
                roles = data.get("roles", ["researcher"])
                tasks = data.get("tasks", {})

                # Auto-add reviewer for teams that produce deliverables
                roles = self._ensure_reviewer(roles, tasks)

                return TeamConfig(
                    roles=roles,
                    reason=data.get("reason", "根据需求分析"),
                    tasks=tasks,
                )
            except json.JSONDecodeError:
                pass

        # Fallback
        return TeamConfig(
            roles=["researcher"],
            reason="无法解析需求，分配默认调研员",
            tasks={"researcher": "完成用户需求"},
        )

    def _ensure_reviewer(self, roles: list[str], tasks: dict[str, str]) -> list[str]:
        """Ensure reviewer is included for teams with deliverables."""
        # Roles that produce deliverables requiring verification
        deliverable_roles = {"frontend", "backend", "architect", "writer", "researcher", "analyst"}

        # If team has deliverable producers, add reviewer
        if any(role in deliverable_roles for role in roles):
            if "reviewer" not in roles:
                roles = roles + ["reviewer"]
                tasks["reviewer"] = "验收所有产出物，确保可用性和完整性"

        return roles

    def _default_team_config(self, requirement: str) -> TeamConfig:
        """Return default team config based on keywords."""
        req_lower = requirement.lower()

        # Check for development keywords
        dev_keywords = ["应用", "app", "网站", "系统", "平台", "开发", "实现", "做一个"]
        if any(kw in req_lower for kw in dev_keywords):
            return TeamConfig(
                roles=["pm", "architect", "backend", "frontend", "tester"],
                reason="这是一个开发任务，需要完整的开发团队",
                tasks={
                    "pm": "分析需求，撰写 PRD",
                    "architect": "设计系统架构和 API",
                    "backend": "实现后端 API",
                    "frontend": "实现前端界面",
                    "tester": "编写和执行测试",
                },
            )

        # Check for research keywords
        research_keywords = ["调研", "分析", "研究", "了解", "查询"]
        if any(kw in req_lower for kw in research_keywords):
            return TeamConfig(
                roles=["researcher"],
                reason="这是一个调研任务",
                tasks={"researcher": requirement},
            )

        # Check for writing keywords
        writing_keywords = ["写", "撰写", "文档", "报告"]
        if any(kw in req_lower for kw in writing_keywords):
            return TeamConfig(
                roles=["writer"],
                reason="这是一个写作任务",
                tasks={"writer": requirement},
            )

        # Default: single researcher
        return TeamConfig(
            roles=["researcher"],
            reason="默认分配调研员处理",
            tasks={"researcher": requirement},
        )

    async def _generate_project_name(self, requirement: str) -> str:
        """Generate a short project name from requirement."""
        # Simple approach: take first 20 chars or first sentence
        name = requirement.split("，")[0].split(",")[0][:30]
        if len(name) < len(requirement):
            name += "..."
        return name

    def _save_team_config(self, project: Project, team_config: TeamConfig) -> None:
        """Save team configuration to workspace."""
        config_path = Path(project.workspace) / ".conductor" / "team.json"
        config_data = {
            "project_id": project.id,
            "project_name": project.name,
            "requirement": project.requirement,
            "roles": team_config.roles,
            "reason": team_config.reason,
            "tasks": team_config.tasks,
            "team": [
                {
                    "id": m.id,
                    "role_id": m.role.id if m.role else None,
                    "role_name": m.role.name if m.role else None,
                    "session_id": m.session_id,
                }
                for m in project.team
            ],
        }
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)

        # Also save requirement to a visible file
        req_path = Path(project.workspace) / "REQUIREMENT.md"
        with open(req_path, "w", encoding="utf-8") as f:
            f.write(f"# 项目需求\n\n{project.requirement}\n")