"""Core data models for Conductor."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ProjectStatus(Enum):
    """Project status."""
    PLANNING = "planning"      # 需求分析中
    FORMING = "forming"        # 组建团队中
    RUNNING = "running"        # 执行中
    PAUSED = "paused"          # 暂停
    COMPLETED = "completed"    # 完成
    FAILED = "failed"          # 失败


class AgentStatus(Enum):
    """Agent status."""
    IDLE = "idle"              # 空闲
    WORKING = "working"        # 工作中
    WAITING = "waiting"        # 等待中 (等其他 agent)
    DONE = "done"              # 完成


@dataclass
class AgentRole:
    """Agent role definition."""
    id: str                    # 角色 ID (pm, backend, frontend, etc.)
    name: str                  # 显示名称
    emoji: str                 # 头像 emoji
    description: str           # 角色描述
    system_prompt: str         # 角色的 system prompt


# 预定义角色
PREDEFINED_ROLES: dict[str, AgentRole] = {
    "pm": AgentRole(
        id="pm",
        name="产品经理",
        emoji="🎯",
        description="负责需求分析、PRD 撰写、功能规划",
        system_prompt="""你是一个专业的产品经理。你的职责是：
1. 分析用户需求，理解核心诉求
2. 撰写清晰的 PRD (产品需求文档)
3. 定义功能列表和优先级
4. 与团队成员沟通需求细节

输出文档到 docs/prd.md""",
    ),
    "architect": AgentRole(
        id="architect",
        name="架构师",
        emoji="🏗️",
        description="负责系统架构设计、技术选型、API 设计",
        system_prompt="""你是一个资深的系统架构师。你的职责是：
1. 设计系统整体架构
2. 进行技术选型
3. 设计 API 接口规范
4. 设计数据库模型

输出文档到 docs/architecture.md 和 docs/api_design.md""",
    ),
    "backend": AgentRole(
        id="backend",
        name="后端开发",
        emoji="💻",
        description="负责后端 API 开发、数据库实现",
        system_prompt="""你是一个后端开发工程师。你的职责是：
1. 根据 API 设计文档实现后端接口
2. 实现数据库模型和迁移
3. 编写业务逻辑
4. 确保代码质量和可运行性

技术栈: FastAPI + SQLAlchemy + PostgreSQL
代码输出到 backend/ 目录""",
    ),
    "frontend": AgentRole(
        id="frontend",
        name="前端开发",
        emoji="🎨",
        description="负责前端 UI 开发、交互实现",
        system_prompt="""你是一个前端开发工程师。你的职责是：
1. 根据 PRD 和设计实现前端页面
2. 与后端 API 对接
3. 实现用户交互
4. 确保代码质量和可运行性

技术栈: React + TypeScript + TailwindCSS
代码输出到 frontend/ 目录""",
    ),
    "tester": AgentRole(
        id="tester",
        name="测试工程师",
        emoji="🧪",
        description="负责测试用例编写、测试执行",
        system_prompt="""你是一个测试工程师。你的职责是：
1. 编写测试用例
2. 执行自动化测试
3. 发现并报告 bug
4. 验证修复结果

后端测试: pytest
前端测试: Playwright
测试代码输出到 tests/ 目录""",
    ),
    "researcher": AgentRole(
        id="researcher",
        name="调研员",
        emoji="🔍",
        description="负责信息收集、资料整理",
        system_prompt="""你是一个专业的调研员。你的职责是：
1. 收集相关信息和资料
2. 整理和分析数据
3. 撰写调研报告
4. 提供有价值的洞察

输出报告到 docs/research.md""",
    ),
    "analyst": AgentRole(
        id="analyst",
        name="分析师",
        emoji="📊",
        description="负责数据分析、趋势研判",
        system_prompt="""你是一个数据分析师。你的职责是：
1. 分析数据和信息
2. 发现规律和趋势
3. 提供分析结论
4. 给出建议

输出分析报告到 docs/analysis.md""",
    ),
    "writer": AgentRole(
        id="writer",
        name="撰稿人",
        emoji="✍️",
        description="负责文档撰写、内容创作",
        system_prompt="""你是一个专业的撰稿人。你的职责是：
1. 撰写清晰、专业的文档
2. 整理和润色内容
3. 确保文档结构清晰
4. 输出高质量的文档

输出到 docs/ 目录""",
    ),
    "reviewer": AgentRole(
        id="reviewer",
        name="验收员",
        emoji="✅",
        description="负责产出物验收、质量检查",
        system_prompt="""你是一个严格的验收员。你的职责是：
1. 检查所有产出物是否完整
2. 验证代码/文档是否可用：
   - 代码项目：检查依赖是否安装，尝试运行构建命令
   - 文档：检查内容是否完整，链接是否有效
   - 前端项目：必须能直接打开或提供完整的运行说明
3. 发现问题时，明确指出问题并 @相关角色要求修复
4. 确认可用后，输出验收报告

验收标准：
- 代码项目必须能成功运行（npm install && npm run build 等）
- 静态页面必须能直接在浏览器打开
- 文档必须内容完整、格式正确

如果发现问题，必须 @相关角色 要求修复，不能放过任何问题。
验收通过后输出 docs/acceptance.md""",
    ),
}


@dataclass
class TeamMember:
    """A team member (agent instance)."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    role: AgentRole = None
    session_id: str | None = None  # Claude CLI session ID
    status: AgentStatus = AgentStatus.IDLE
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def display_name(self) -> str:
        """Get display name with emoji."""
        return f"{self.role.emoji} {self.role.name}" if self.role else "Unknown"


@dataclass
class Message:
    """A message in the project chat."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    from_id: str = ""          # agent id, 'user', or 'system'
    from_name: str = ""        # display name
    content: str = ""
    mentions: list[str] = field(default_factory=list)  # mentioned agent ids
    attachments: list[str] = field(default_factory=list)  # file paths
    timestamp: datetime = field(default_factory=datetime.now)

    def format_for_display(self) -> str:
        """Format message for terminal display."""
        time_str = self.timestamp.strftime("%H:%M:%S")
        mentions_str = " ".join(f"@{m}" for m in self.mentions) if self.mentions else ""
        return f"[{time_str}] {self.from_name}: {self.content} {mentions_str}".strip()


@dataclass
class TeamConfig:
    """Team configuration from requirement analysis."""
    roles: list[str]           # role ids needed
    reason: str                # why these roles
    tasks: dict[str, str] = field(default_factory=dict)  # role_id -> initial task


@dataclass
class Project:
    """A project with team and workspace."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    requirement: str = ""
    workspace: str = ""        # workspace directory path
    status: ProjectStatus = ProjectStatus.PLANNING
    team: list[TeamMember] = field(default_factory=list)
    messages: list[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def get_member_by_role(self, role_id: str) -> TeamMember | None:
        """Get team member by role id."""
        for member in self.team:
            if member.role and member.role.id == role_id:
                return member
        return None

    def get_member_by_id(self, member_id: str) -> TeamMember | None:
        """Get team member by id."""
        for member in self.team:
            if member.id == member_id:
                return member
        return None

    def add_message(self, message: Message) -> None:
        """Add a message to project chat."""
        message.project_id = self.id
        self.messages.append(message)