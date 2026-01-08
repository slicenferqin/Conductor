"""Orchestrator - Runs the full multi-agent collaboration flow."""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from conductor.core.agent import Agent, AgentContext
from conductor.core.message_bus import MessageBus
from conductor.core.models import (
    AgentStatus,
    Message,
    Project,
    ProjectStatus,
    TeamConfig,
    TeamMember,
)
from conductor.core.secretary import Secretary


@dataclass
class OrchestratorConfig:
    """Configuration for the orchestrator."""
    base_workspace: str = "./projects"
    parallel_execution: bool = False  # Whether to run agents in parallel


class Orchestrator:
    """Orchestrates the full multi-agent collaboration flow.

    Flow:
    1. User submits requirement
    2. Secretary analyzes requirement and forms team
    3. Agents are created with their roles
    4. Tasks are executed (sequentially or in parallel)
    5. Agents communicate via message bus
    6. Project completes with deliverables
    """

    def __init__(
        self,
        config: OrchestratorConfig | None = None,
        on_message: Callable[[Message], None] | None = None,
        on_progress: Callable[[str], None] | None = None,
        on_agent_status_change: Callable[[str, AgentStatus, str | None], None] | None = None,
    ):
        """Initialize orchestrator.

        Args:
            config: Orchestrator configuration
            on_message: Callback for new messages
            on_progress: Callback for progress updates
            on_agent_status_change: Callback for agent status changes (agent_id, status, current_action)
        """
        self.config = config or OrchestratorConfig()
        self.on_message = on_message
        self.on_progress = on_progress
        self.on_agent_status_change = on_agent_status_change
        self.secretary = Secretary(base_workspace=self.config.base_workspace)
        self.message_bus: MessageBus | None = None
        self.agents: dict[str, Agent] = {}
        self.project: Project | None = None
        self._failed_agents: set[str] = set()  # Track agents that have failed
        self._triggered_agents: set[str] = set()  # Track agents already triggered in this round

    def _log(self, message: str) -> None:
        """Log progress message."""
        if self.on_progress:
            self.on_progress(message)
        print(message)

    def _handle_agent_message(self, message: Message) -> None:
        """Handle message from an agent."""
        if self.message_bus:
            # Use sync publish since we're in a callback
            self.message_bus.publish_sync(message)
        if self.on_message:
            self.on_message(message)

    async def run(self, requirement: str) -> Project:
        """Run the full collaboration flow.

        Args:
            requirement: User's requirement

        Returns:
            Completed project
        """
        try:
            self._log("🚀 开始处理需求...")

            # Phase 1: Secretary analyzes requirement and forms team
            self._log("📋 秘书正在分析需求并组建团队...")
            project, team_config = await self.secretary.handle_requirement(requirement)
            self.project = project

            # Initialize message bus with workspace
            self.message_bus = MessageBus(workspace=project.workspace)

            # Add secretary messages to bus
            for msg in project.messages:
                self.message_bus.publish_sync(msg)
                if self.on_message:
                    self.on_message(msg)

            self._log(f"✅ 团队组建完成: {', '.join(m.role.name for m in project.team)}")

            # Phase 2: Create agents for each team member
            self._log("🤖 创建 Agent 实例...")
            await self._create_agents(project, team_config)

            # Phase 3: Execute tasks
            self._log("⚙️ 开始执行任务...")
            await self._execute_tasks(project, team_config)

            # Phase 4: Completion
            project.status = ProjectStatus.COMPLETED
            self._log("🎉 项目完成!")

            # Final summary message
            summary = self._generate_summary(project)
            summary_msg = Message(
                project_id=project.id,
                from_id="secretary",
                from_name=f"{self.secretary.EMOJI} {self.secretary.NAME}",
                content=summary,
            )
            project.add_message(summary_msg)
            self.message_bus.publish_sync(summary_msg)
            if self.on_message:
                self.on_message(summary_msg)

            return project

        except Exception as e:
            self._log(f"❌ 项目执行出错: {e}")
            raise
        finally:
            # Cleanup: terminate all agent processes
            await self._cleanup_agents()

    async def _create_agents(
        self,
        project: Project,
        team_config: TeamConfig,
    ) -> None:
        """Create agent instances for all team members."""
        # Build team info string with clear @mention format
        members_list = "\n".join(
            f"- {m.role.name}: {m.role.description}"
            for m in project.team
        )
        mention_list = ", ".join(f"@{m.role.name}" for m in project.team)
        team_info = f"""{members_list}

可用的 @mention: {mention_list}"""

        for member in project.team:
            if not member.role:
                continue

            # Get initial task for this role
            initial_task = team_config.tasks.get(
                member.role.id,
                f"根据你的角色职责完成相关工作"
            )

            context = AgentContext(
                project_id=project.id,
                workspace=project.workspace,
                requirement=project.requirement,
                team_info=team_info,
                initial_task=initial_task,
            )

            agent = Agent(
                member=member,
                context=context,
                on_message=self._handle_agent_message,
                on_status_change=self.on_agent_status_change,
            )

            self.agents[member.id] = agent

            # Subscribe agent to message bus for @mentions
            self.message_bus.subscribe(
                subscriber_id=member.id,
                callback=lambda msg, a=agent: asyncio.create_task(a.handle_message(msg)),
                filter_mentions=True,
            )

    async def _execute_tasks(
        self,
        project: Project,
        team_config: TeamConfig,
    ) -> None:
        """Execute tasks using message-driven collaboration.

        All agents listen for messages. When @mentioned, they respond.
        The flow is driven by agents mentioning each other, not by
        a central orchestrator.
        """
        # Start all agents listening in parallel
        self._log("🎬 所有 Agent 已就位，开始协作...")

        # Kick off: find the first role to start
        first_role = self._get_first_role(team_config)
        first_agent = self._get_agent_by_role(first_role)

        if first_agent:
            # Start the first agent with heartbeat
            self._log(f"  {first_agent.display_name} 开始工作...")

            heartbeat_task = asyncio.create_task(
                self._heartbeat(first_agent, project)
            )

            try:
                first_message = await first_agent.execute_task()
            finally:
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass
                self._log(f"  ✅ {first_agent.display_name} 完成")

            project.add_message(first_message)

            # Process any @mentions in the response
            await self._process_mentions(project, first_message)

            # After all work is done, trigger reviewer if present and not already triggered
            await self._trigger_final_review(project)

    def _get_first_role(self, team_config: TeamConfig) -> str:
        """Determine which role should start first."""
        # Priority order for starting
        priority = ["pm", "architect", "researcher", "analyst", "writer", "backend", "frontend", "tester"]
        for role in priority:
            if role in team_config.roles:
                return role
        return team_config.roles[0] if team_config.roles else "researcher"

    def _get_agent_by_role(self, role_id: str) -> Agent | None:
        """Get agent by role ID."""
        for agent in self.agents.values():
            if agent.role and agent.role.id == role_id:
                return agent
        return None

    async def _process_mentions(self, project: Project, message: Message) -> None:
        """Process @mentions in a message and trigger mentioned agents.

        This creates a cascading effect where agents respond to mentions,
        which may trigger more agents, until no more mentions need processing.
        """
        if not message.mentions:
            return

        # Find agents that were mentioned and haven't completed yet
        pending_tasks = []
        mentioned_agents = []

        for mention in message.mentions:
            # Try to find agent by role ID or role name
            agent = self._get_agent_by_role(mention.lower())
            if not agent:
                # Try by Chinese name mapping
                name_to_role = {
                    "后端开发": "backend",
                    "前端开发": "frontend",
                    "测试工程师": "tester",
                    "产品经理": "pm",
                    "架构师": "architect",
                    "调研员": "researcher",
                    "分析师": "analyst",
                    "撰稿人": "writer",
                    "验收员": "reviewer",
                }
                role_id = name_to_role.get(mention)
                if role_id:
                    agent = self._get_agent_by_role(role_id)

            # Skip if agent is working, failed, or already triggered
            if agent and agent.member.status != AgentStatus.WORKING:
                if agent.id not in self._failed_agents:
                    mentioned_agents.append(agent)

        if not mentioned_agents:
            return

        # Execute all mentioned agents in parallel
        self._log(f"  📢 触发 {len(mentioned_agents)} 个 Agent: {', '.join(a.display_name for a in mentioned_agents)}")

        for agent in mentioned_agents:
            self._log(f"  {agent.display_name} 开始工作...")
            pending_tasks.append(self._agent_respond_to_message(agent, message, project))

        # Wait for all mentioned agents to complete
        responses = await asyncio.gather(*pending_tasks, return_exceptions=True)

        # Collect all responses first (skip error messages)
        new_messages = []
        for i, response in enumerate(responses):
            if isinstance(response, Message):
                project.add_message(response)
                # Check if this is an error message
                if "执行任务时出错" in response.content:
                    # Mark agent as failed to prevent infinite loop
                    if i < len(mentioned_agents):
                        failed_agent = mentioned_agents[i]
                        self._failed_agents.add(failed_agent.id)
                        self._log(f"  ⚠️ {failed_agent.display_name} 执行失败，已标记跳过")
                else:
                    new_messages.append(response)
            elif isinstance(response, Exception):
                # Mark agent as failed
                if i < len(mentioned_agents):
                    failed_agent = mentioned_agents[i]
                    self._failed_agents.add(failed_agent.id)
                    self._log(f"  ⚠️ {failed_agent.display_name} 执行异常，已标记跳过")
                self._log(f"  ⚠️ Agent 执行出错: {response}")

        # After all parallel tasks complete, process any new @mentions
        # This ensures agents that were WORKING are now available
        for msg in new_messages:
            await self._process_mentions(project, msg)

    async def _agent_respond_to_message(
        self,
        agent: Agent,
        trigger_message: Message,
        project: Project,
    ) -> Message:
        """Have an agent respond to a message that mentioned them."""
        # Start heartbeat task to show agent is working
        heartbeat_task = asyncio.create_task(
            self._heartbeat(agent, project)
        )

        try:
            response = await agent.handle_message(trigger_message)
            if response:
                return response
            else:
                # If handle_message returned None, execute their initial task
                result = await agent.execute_task()
                return result
        finally:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
            self._log(f"  ✅ {agent.display_name} 完成")

    async def _heartbeat(self, agent: Agent, project: Project) -> None:
        """Send periodic heartbeat messages while agent is working.

        This is a fallback - real progress updates come from streaming.
        Only shows if no streaming updates received for a while.
        """
        await asyncio.sleep(15)  # Wait 15 seconds before first heartbeat

        while True:
            # Simple heartbeat just to show it's still alive
            msg = Message(
                project_id=project.id,
                from_id=agent.id,
                from_name=f"{agent.display_name} 💭",
                content="仍在工作中...",
                mentions=[],
            )
            if self.on_message:
                self.on_message(msg)
            await asyncio.sleep(30)  # Less frequent - every 30 seconds

    async def _trigger_final_review(self, project: Project) -> None:
        """Trigger reviewer for final acceptance check."""
        reviewer = self._get_agent_by_role("reviewer")
        if not reviewer:
            return

        # Check if reviewer was already triggered
        if reviewer.id in self._failed_agents:
            self._log("  ⚠️ 验收员之前执行失败，跳过最终验收")
            return

        # Check if reviewer already worked (has sent a message)
        for msg in project.messages:
            if msg.from_id == reviewer.id:
                self._log("  ℹ️ 验收员已完成工作")
                return

        # Trigger final review
        self._log("  🔍 触发验收员进行最终验收...")

        # Create a trigger message from secretary
        trigger_msg = Message(
            project_id=project.id,
            from_id="secretary",
            from_name=f"{self.secretary.EMOJI} {self.secretary.NAME}",
            content="所有工作已完成，请 @验收员 进行最终验收，检查所有产出物是否可用。",
            mentions=["验收员"],
        )
        project.add_message(trigger_msg)
        if self.on_message:
            self.on_message(trigger_msg)

        # Execute reviewer
        self._log(f"  {reviewer.display_name} 开始工作...")

        heartbeat_task = asyncio.create_task(
            self._heartbeat(reviewer, project)
        )

        try:
            response = await reviewer.execute_task()
            project.add_message(response)

            # Process any @mentions from reviewer (e.g., asking for fixes)
            if response.mentions:
                await self._process_mentions(project, response)
        finally:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
            self._log(f"  ✅ {reviewer.display_name} 完成")

    async def _cleanup_agents(self) -> None:
        """Cleanup all agent processes."""
        self._log("🧹 清理 Agent 进程...")
        for agent in self.agents.values():
            try:
                await agent.cleanup()
            except Exception as e:
                self._log(f"  ⚠️ 清理 {agent.display_name} 时出错: {e}")
        self.agents.clear()

    def _generate_summary(self, project: Project) -> str:
        """Generate project completion summary."""
        # List files created
        workspace = Path(project.workspace)
        files = []
        for f in workspace.rglob("*"):
            if f.is_file() and ".conductor" not in str(f):
                rel_path = f.relative_to(workspace)
                files.append(str(rel_path))

        files_list = "\n".join(f"  • {f}" for f in sorted(files)[:20])
        if len(files) > 20:
            files_list += f"\n  ... 还有 {len(files) - 20} 个文件"

        return f"""🎉 项目完成！

📋 项目: {project.name}
📁 目录: {project.workspace}

👥 团队成员:
{chr(10).join(f"  {m.role.emoji} {m.role.name}" for m in project.team)}

📦 产出文件:
{files_list if files else "  (暂无文件)"}
"""


async def run_project(requirement: str) -> Project:
    """Convenience function to run a project.

    Args:
        requirement: User's requirement

    Returns:
        Completed project
    """
    orchestrator = Orchestrator(
        on_progress=lambda msg: print(msg),
    )
    return await orchestrator.run(requirement)