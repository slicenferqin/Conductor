"""Agent - Independent Claude session with a specific role."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

from conductor.core.models import (
    AgentRole,
    AgentStatus,
    Message,
    TeamMember,
)
from conductor.integrations.claude_cli import ClaudeCodeCLI


@dataclass
class AgentContext:
    """Context information for an agent."""
    project_id: str
    workspace: str
    requirement: str
    team_info: str  # Description of team members
    initial_task: str  # Task assigned by secretary


class Agent:
    """An AI agent with a specific role.

    Each agent runs as an independent Claude CLI session.
    Agents communicate via the message bus and collaborate
    through the shared file system (workspace).
    """

    def __init__(
        self,
        member: TeamMember,
        context: AgentContext,
        on_message: Callable[[Message], None] | None = None,
        on_status_change: Callable[[str, AgentStatus, str | None], None] | None = None,
    ):
        """Initialize agent.

        Args:
            member: The team member configuration
            context: Project context
            on_message: Callback when agent sends a message
            on_status_change: Callback when agent status changes (agent_id, status, current_action)
        """
        self.member = member
        self.role = member.role
        self.context = context
        self.on_message = on_message
        self.on_status_change = on_status_change
        self.cli = ClaudeCodeCLI(context.workspace)
        self._status = AgentStatus.IDLE

    def _set_status(self, status: AgentStatus, current_action: str | None = None) -> None:
        """Update agent status and notify listeners."""
        self._status = status
        self.member.status = status
        if self.on_status_change:
            self.on_status_change(self.id, status, current_action)

    @property
    def id(self) -> str:
        return self.member.id

    @property
    def display_name(self) -> str:
        return self.member.display_name

    @property
    def status(self) -> AgentStatus:
        return self._status

    def _build_system_context(self) -> str:
        """Build the system context for Claude."""
        return f"""你是一个 AI 团队成员，扮演 {self.role.name} 角色。

{self.role.system_prompt}

## 项目信息
- 项目 ID: {self.context.project_id}
- 工作目录: {self.context.workspace}

## 需求
{self.context.requirement}

## 团队成员
{self.context.team_info}

## 协作规则
1. 在工作目录下创建和编辑文件
2. 需要其他角色协助时，使用上面列出的 @mention 格式联系
3. 完成任务后，说明产出了什么文件
4. 发现问题时，及时沟通
5. 收到 @mention 时，要回复确认或提出疑问
6. **非常重要 - 工作汇报**：
   - 开始工作时，先简短说明你打算做什么（1句话）
   - 每完成一个关键步骤，简短汇报进度（如"已完成XX，接下来做YY"）
   - 这是团队协作，请保持沟通活跃
7. **非常重要 - 依赖检查**：
   - 开始工作前，先判断是否需要其他角色的产出（如文档、代码、分析报告等）
   - 检查工作目录下是否已有所需文件
   - 如果需要依赖但文件不存在：**只输出一句话说明在等待谁，然后立即结束**
   - 例如："等待 @架构师 完成架构设计后开始。"
8. **非常重要 - 输出精简**：
   - 所有产出内容（报告、代码、文档等）必须写入文件，不要在消息中输出完整内容
   - 消息中只输出简短摘要（3-5句话）+ 文件路径
   - 例如："已完成调研报告，主要发现：1)... 2)... 详见 docs/research.md"

## 你的任务
{self.context.initial_task}
"""

    async def execute_task(self, task: str | None = None) -> Message:
        """Execute a task and return the result message.

        Args:
            task: Optional task override, otherwise uses initial task

        Returns:
            Message with agent's response
        """
        self._set_status(AgentStatus.WORKING, "开始执行任务...")

        prompt = self._build_system_context()
        if task:
            prompt += f"\n\n## 新任务\n{task}"

        try:
            result_text = ""
            last_progress_text = ""
            message_count = 0

            # Stream execution to show progress
            async for msg in self.cli.execute(prompt=prompt):
                message_count += 1

                # Extract progress text from various message types
                progress_text = self._extract_progress_text(msg.content)

                # Show progress for any message with meaningful content
                if progress_text and progress_text != last_progress_text:
                    # Throttle: show every 5th message or if content changed significantly
                    if message_count % 5 == 1 or len(progress_text) - len(last_progress_text) > 50:
                        progress_msg = Message(
                            project_id=self.context.project_id,
                            from_id=self.id,
                            from_name=f"{self.display_name} 💭",
                            content=progress_text[:200] + ("..." if len(progress_text) > 200 else ""),
                            mentions=[],
                        )
                        if self.on_message:
                            self.on_message(progress_msg)
                        last_progress_text = progress_text

                if msg.type == "result":
                    result_text = msg.content.get("result", "")

            if not result_text:
                result_text = "任务执行完成，但未返回具体结果。"

            # Parse mentions from result
            mentions = self._extract_mentions(result_text)

            # Return to IDLE so agent can respond to future messages
            self._set_status(AgentStatus.IDLE, "任务完成")

            message = Message(
                project_id=self.context.project_id,
                from_id=self.id,
                from_name=self.display_name,
                content=result_text,
                mentions=mentions,
            )

            if self.on_message:
                self.on_message(message)

            return message

        except Exception as e:
            self._set_status(AgentStatus.IDLE, f"执行出错: {e}")

            error_message = Message(
                project_id=self.context.project_id,
                from_id=self.id,
                from_name=self.display_name,
                content=f"执行任务时出错: {e}",
            )

            if self.on_message:
                self.on_message(error_message)

            return error_message

    async def handle_message(self, message: Message) -> Message | None:
        """Handle a message directed at this agent.

        Args:
            message: The incoming message

        Returns:
            Response message if agent needs to respond
        """
        # Check if message mentions this agent (by role_id, role_name, or agent_id)
        role_id = self.role.id if self.role else None
        role_name = self.role.name if self.role else None

        is_mentioned = (
            (role_id and role_id in message.mentions) or
            (role_name and role_name in message.mentions) or
            self.id in message.mentions
        )

        if not is_mentioned:
            return None

        self._set_status(AgentStatus.WORKING, f"处理来自 {message.from_name} 的消息...")

        # Build context with the incoming message
        prompt = f"""{self._build_system_context()}

## 收到消息
来自: {message.from_name}
内容: {message.content}

请根据消息内容进行响应和处理。
"""

        try:
            result_text = ""
            last_progress = ""

            # Use streaming to show progress
            async for msg in self.cli.execute(prompt=prompt):
                # Show progress for tool usage and assistant messages
                if msg.type in ("assistant", "text", "tool_use"):
                    text = self._extract_progress_text(msg.content)
                    if text and text != last_progress:
                        progress_msg = Message(
                            project_id=self.context.project_id,
                            from_id=self.id,
                            from_name=f"{self.display_name} 💭",
                            content=text[:200] + ("..." if len(text) > 200 else ""),
                            mentions=[],
                        )
                        if self.on_message:
                            self.on_message(progress_msg)
                        last_progress = text

                elif msg.type == "result":
                    result_text = msg.content.get("result", "")

            if not result_text:
                result_text = "已收到，正在处理。"

            mentions = self._extract_mentions(result_text)

            self._set_status(AgentStatus.IDLE, "消息处理完成")

            response = Message(
                project_id=self.context.project_id,
                from_id=self.id,
                from_name=self.display_name,
                content=result_text,
                mentions=mentions,
            )

            if self.on_message:
                self.on_message(response)

            return response

        except Exception as e:
            self._set_status(AgentStatus.IDLE, f"处理出错: {e}")
            return None

    def _extract_progress_text(self, content: dict) -> str:
        """Extract displayable text from streaming message content.

        Claude CLI stream-json format:
        - {"type":"assistant","message":{"content":[{"type":"text","text":"..."}]}}
        - {"type":"assistant","message":{"content":[{"type":"tool_use","name":"Read","input":{...}}]}}
        """
        msg_type = content.get("type", "")
        text = ""

        # Handle assistant message
        if msg_type == "assistant":
            message = content.get("message", {})
            blocks = message.get("content", [])
            if isinstance(blocks, list):
                for block in blocks:
                    if isinstance(block, dict):
                        block_type = block.get("type", "")
                        if block_type == "text":
                            text = block.get("text", "")
                            if text:
                                break
                        elif block_type == "tool_use":
                            tool_name = block.get("name", "")
                            tool_input = block.get("input", {})
                            text = self._format_tool_usage(tool_name, tool_input)
                            break

        return text if isinstance(text, str) else ""

    def _format_tool_usage(self, tool_name: str, tool_input: dict) -> str:
        """Format tool usage into readable progress text."""
        tool_descriptions = {
            "Read": "📖 读取文件",
            "Write": "📝 写入文件",
            "Edit": "✏️ 编辑文件",
            "Bash": "💻 执行命令",
            "Glob": "🔍 搜索文件",
            "Grep": "🔎 搜索内容",
            "WebFetch": "🌐 获取网页",
            "WebSearch": "🔍 搜索网络",
            "Task": "🤖 启动子任务",
        }

        base_desc = tool_descriptions.get(tool_name, f"🔧 使用 {tool_name}")

        # Add context from input
        if tool_name == "Read" and "file_path" in tool_input:
            path = tool_input["file_path"]
            filename = path.split("/")[-1] if "/" in path else path
            return f"{base_desc}: {filename}"
        elif tool_name == "Write" and "file_path" in tool_input:
            path = tool_input["file_path"]
            filename = path.split("/")[-1] if "/" in path else path
            return f"{base_desc}: {filename}"
        elif tool_name == "Bash" and "command" in tool_input:
            cmd = tool_input["command"][:50]
            return f"{base_desc}: {cmd}"
        elif tool_name == "WebSearch" and "query" in tool_input:
            query = tool_input["query"][:30]
            return f"{base_desc}: {query}"
        elif tool_name == "Glob" and "pattern" in tool_input:
            pattern = tool_input["pattern"]
            return f"{base_desc}: {pattern}"

        return base_desc

    def _extract_mentions(self, text: str) -> list[str]:
        """Extract @mentions from text (deduplicated).

        Handles @mentions with or without emojis:
        - @撰稿人
        - @✍️ 撰稿人
        - @✍️撰稿人
        """
        import re

        # Pattern: @ followed by optional emojis/spaces, then role name
        # This captures: @撰稿人, @✍️ 撰稿人, @✍️撰稿人
        # Emoji range covers most common emojis
        pattern = r'@[\U0001F300-\U0001F9FF\s]*([\w\u4e00-\u9fff]+)'
        matches = re.findall(pattern, text)

        # Deduplicate while preserving order
        seen = set()
        unique = []
        for m in matches:
            if m not in seen:
                seen.add(m)
                unique.append(m)
        return unique

    def is_mentioned_in(self, message: Message) -> bool:
        """Check if this agent is mentioned in a message."""
        if self.role:
            if self.role.id in message.mentions:
                return True
            if self.role.name in message.mentions:
                return True
        if self.id in message.mentions:
            return True
        return False

    async def cleanup(self) -> None:
        """Cleanup agent resources (terminate any running CLI processes)."""
        await self.cli.cleanup()