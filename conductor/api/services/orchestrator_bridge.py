"""Bridge between FastAPI and the Orchestrator."""

import asyncio
import logging
from datetime import datetime

from conductor.core import (
    Orchestrator,
    OrchestratorConfig,
    Project,
    Message,
    AgentStatus,
    ProjectStatus,
)
from ..schemas import (
    AgentStatusAPI,
    AgentRoleSchema,
    TeamMemberSchema,
    ProjectStatusAPI,
    ProjectResponse,
    MessageSchema,
    MessageType,
)
from ..websocket import connection_manager
from ..state import app_state

logger = logging.getLogger(__name__)


class OrchestratorBridge:
    """Bridge between FastAPI and the Orchestrator."""

    def __init__(self):
        self._running_orchestrators: dict[str, Orchestrator] = {}
        self._tasks: dict[str, asyncio.Task] = {}
        self._projects: dict[str, Project] = {}  # Store core Project objects

    def _map_agent_status(self, status: AgentStatus) -> AgentStatusAPI:
        """Map core AgentStatus to API AgentStatus."""
        mapping = {
            AgentStatus.IDLE: AgentStatusAPI.ONLINE,
            AgentStatus.WORKING: AgentStatusAPI.WORKING,
            AgentStatus.WAITING: AgentStatusAPI.WAITING,
            AgentStatus.DONE: AgentStatusAPI.OFFLINE,
        }
        return mapping.get(status, AgentStatusAPI.ONLINE)

    def _map_project_status(self, status: ProjectStatus) -> ProjectStatusAPI:
        """Map core ProjectStatus to API ProjectStatus."""
        mapping = {
            ProjectStatus.PLANNING: ProjectStatusAPI.PLANNING,
            ProjectStatus.FORMING: ProjectStatusAPI.FORMING,
            ProjectStatus.RUNNING: ProjectStatusAPI.RUNNING,
            ProjectStatus.PAUSED: ProjectStatusAPI.PAUSED,
            ProjectStatus.COMPLETED: ProjectStatusAPI.COMPLETED,
            ProjectStatus.FAILED: ProjectStatusAPI.FAILED,
        }
        return mapping.get(status, ProjectStatusAPI.PLANNING)

    def _member_to_schema(self, member) -> TeamMemberSchema:
        """Convert core TeamMember to API schema."""
        return TeamMemberSchema(
            id=member.id,
            role=AgentRoleSchema(
                id=member.role.id,
                name=member.role.name,
                emoji=member.role.emoji,
                description=member.role.description,
            ) if member.role else AgentRoleSchema(
                id="unknown",
                name="Unknown",
                emoji="?",
                description="Unknown role",
            ),
            status=self._map_agent_status(member.status),
            currentAction=None,
            progress=None,
            errorMessage=None,
        )

    def _project_to_response(self, project: Project) -> ProjectResponse:
        """Convert core Project to API ProjectResponse."""
        return ProjectResponse(
            id=project.id,
            name=project.name,
            requirement=project.requirement,
            workspace=project.workspace,
            status=self._map_project_status(project.status),
            team=[self._member_to_schema(m) for m in project.team],
            createdAt=project.created_at.isoformat(),
            lastUpdated=datetime.now().isoformat(),
            duration=None,
        )

    def _message_to_schema(self, msg: Message) -> MessageSchema:
        """Convert core Message to API MessageSchema."""
        # Determine message type
        if msg.from_id == "user":
            msg_type = MessageType.USER
        elif msg.from_id in ("secretary", "system"):
            msg_type = MessageType.SYSTEM
        elif "💭" in msg.from_name:
            msg_type = MessageType.PROGRESS
        else:
            msg_type = MessageType.AGENT

        return MessageSchema(
            id=msg.id,
            projectId=msg.project_id,
            fromId=msg.from_id,
            fromName=msg.from_name,
            content=msg.content,
            mentions=msg.mentions,
            attachments=msg.attachments,
            timestamp=msg.timestamp.isoformat(),
            type=msg_type,
        )

    async def _on_message(self, message: Message) -> None:
        """Callback when orchestrator emits a message."""
        schema = self._message_to_schema(message)

        # Store message in app state
        app_state.add_message(message.project_id, schema)

        # Broadcast via WebSocket
        await connection_manager.broadcast_to_project(
            message.project_id,
            {
                "type": "new_message",
                "payload": schema.model_dump(),
            }
        )

    def _on_progress(self, message: str) -> None:
        """Callback for progress updates (logging)."""
        logger.info(f"[Progress] {message}")

    async def _emit_project_status(
        self,
        project_id: str,
        status: str,
        error: str | None = None,
    ) -> None:
        """Emit project status change via WebSocket."""
        # Update app state
        app_state.update_project_status(project_id, status)

        await connection_manager.broadcast_to_project(
            project_id,
            {
                "type": "project_status_changed",
                "payload": {
                    "projectId": project_id,
                    "status": status,
                    "error": error,
                }
            }
        )

    async def start_project(self, requirement: str) -> ProjectResponse:
        """Start a new project with the orchestrator.

        Phase 1: Send initial messages immediately for instant feedback.
        Then process the rest in background.
        """
        import uuid
        from pathlib import Path
        from conductor.config import get_config

        config = get_config()

        # Create a placeholder project immediately
        project_id = str(uuid.uuid4())[:8]
        project_name = requirement[:30] + "..." if len(requirement) > 30 else requirement
        workspace_path = config.workspace / f"project-{project_id}"

        # Create workspace directory immediately so file browser works
        workspace_path.mkdir(parents=True, exist_ok=True)

        placeholder_response = ProjectResponse(
            id=project_id,
            name=project_name,
            requirement=requirement,
            workspace=str(workspace_path),
            status=ProjectStatusAPI.PLANNING,
            team=[],
            createdAt=datetime.now().isoformat(),
            lastUpdated=datetime.now().isoformat(),
            duration=None,
        )

        # Store placeholder in app state
        app_state.add_project(placeholder_response)

        # Emit project_created event immediately
        await connection_manager.broadcast({
            "type": "project_created",
            "payload": placeholder_response.model_dump(),
        })

        logger.info(f"Created placeholder project {project_id}")

        # Phase 1: Send initial messages immediately (before returning!)
        await self._send_initial_messages(project_id, requirement)

        logger.info(f"Sent initial messages, starting background processing...")

        # Start background processing for phases 2-5
        task = asyncio.create_task(
            self._process_project(project_id, requirement)
        )
        self._tasks[project_id] = task

        return placeholder_response

    async def _send_initial_messages(self, project_id: str, requirement: str) -> None:
        """Phase 1: Send immediate feedback messages.

        These messages are sent before API returns, ensuring instant feedback.
        """
        # First: Add secretary to team panel
        secretary_member = TeamMemberSchema(
            id="secretary",
            role=AgentRoleSchema(
                id="secretary",
                name="秘书",
                emoji="🤖",
                description="项目协调与需求分析",
            ),
            status=AgentStatusAPI.WORKING,
            currentAction="分析需求中...",
            progress=None,
            errorMessage=None,
        )

        # Update project team in app state
        project = app_state.get_project(project_id)
        if project:
            updated = ProjectResponse(
                id=project.id,
                name=project.name,
                requirement=project.requirement,
                workspace=project.workspace,
                status=project.status,
                team=[secretary_member],
                createdAt=project.createdAt,
                lastUpdated=datetime.now().isoformat(),
                duration=project.duration,
            )
            app_state.update_project(updated)

        # Broadcast secretary joining team panel
        await connection_manager.broadcast_to_project(
            project_id,
            {
                "type": "team_formed",
                "payload": {
                    "projectId": project_id,
                    "team": [secretary_member.model_dump()],
                }
            }
        )

        # Message 1: User's requirement
        user_msg = MessageSchema(
            id=f"msg-{project_id}-user",
            projectId=project_id,
            fromId="user",
            fromName="👤 用户",
            content=requirement,
            mentions=[],
            attachments=[],
            timestamp=datetime.now().isoformat(),
            type=MessageType.USER,
        )
        app_state.add_message(project_id, user_msg)
        await connection_manager.broadcast_to_project(
            project_id,
            {"type": "new_message", "payload": user_msg.model_dump()}
        )

        # Message 2: Secretary joins
        join_msg = MessageSchema(
            id=f"msg-{project_id}-join",
            projectId=project_id,
            fromId="system",
            fromName="系统",
            content="🤖 秘书 加入了群聊",
            mentions=[],
            attachments=[],
            timestamp=datetime.now().isoformat(),
            type=MessageType.SYSTEM,
        )
        app_state.add_message(project_id, join_msg)
        await connection_manager.broadcast_to_project(
            project_id,
            {"type": "new_message", "payload": join_msg.model_dump()}
        )

        # Message 3: Secretary's immediate response
        response_msg = MessageSchema(
            id=f"msg-{project_id}-response",
            projectId=project_id,
            fromId="secretary",
            fromName="🤖 秘书",
            content="好的，我来分析需求并组建团队...",
            mentions=[],
            attachments=[],
            timestamp=datetime.now().isoformat(),
            type=MessageType.AGENT,
        )
        app_state.add_message(project_id, response_msg)
        await connection_manager.broadcast_to_project(
            project_id,
            {"type": "new_message", "payload": response_msg.model_dump()}
        )

    async def _process_project(self, project_id: str, requirement: str) -> None:
        """Process project phases 2-5 in background.

        Phase 2: Analyze requirement
        Phase 3: Form team
        Phase 4: Assign tasks
        Phase 5: Start execution
        """
        try:
            # Create orchestrator with callbacks
            orchestrator = Orchestrator(
                config=OrchestratorConfig(base_workspace="./projects"),
                on_message=lambda msg: asyncio.create_task(self._on_message(msg)),
                on_progress=self._on_progress,
            )

            # Phase 2: Secretary analyzes requirement
            logger.info(f"Phase 2: Secretary analyzing requirement for project {project_id}...")

            project, team_config = await orchestrator.secretary.handle_requirement(requirement)

            # Update project ID to match our placeholder
            project.id = project_id

            # Store core project
            self._projects[project_id] = project

            # Send analysis result message
            await self._send_analysis_result(project_id, team_config)

            # Update requirements (group announcement)
            await self._update_requirements(project_id, requirement, team_config)

            # Phase 3: Form team - send team formed message + update panel
            logger.info(f"Phase 3: Forming team for project {project_id}...")
            await self._send_team_formed(project_id, project.team)

            # Update app state with full project
            response = self._project_to_response(project)
            app_state.update_project(response)

            # Phase 4: Send task assignment message
            logger.info(f"Phase 4: Assigning tasks for project {project_id}...")
            await self._send_task_assignment(project_id, project.team, team_config)

            # Update status to RUNNING
            await self._emit_project_status(project_id, "RUNNING")

            # Store orchestrator
            self._running_orchestrators[project_id] = orchestrator

            # Phase 5: Run orchestrator - execute tasks
            logger.info(f"Phase 5: Starting execution for project {project_id}...")
            await self._run_orchestrator(orchestrator, requirement, project_id, team_config)

        except Exception as e:
            logger.error(f"Project {project_id} processing failed: {e}")
            # Send error message
            error_msg = MessageSchema(
                id=f"msg-{project_id}-error",
                projectId=project_id,
                fromId="secretary",
                fromName="🤖 秘书",
                content=f"❌ 处理需求时出错：{str(e)}",
                mentions=[],
                attachments=[],
                timestamp=datetime.now().isoformat(),
                type=MessageType.SYSTEM,
            )
            app_state.add_message(project_id, error_msg)
            await connection_manager.broadcast_to_project(
                project_id,
                {"type": "new_message", "payload": error_msg.model_dump()}
            )
            await self._emit_project_status(project_id, "FAILED", error=str(e))

    async def _send_analysis_result(self, project_id: str, team_config) -> None:
        """Send the requirement analysis result message."""
        # Build task breakdown text
        task_lines = []
        for i, (role_id, task) in enumerate(team_config.tasks.items(), 1):
            # Get role name from predefined roles
            from conductor.core.models import PREDEFINED_ROLES
            role = PREDEFINED_ROLES.get(role_id)
            role_name = role.name if role else role_id
            task_lines.append(f"{i}. [{role_name}] {task}")

        tasks_text = "\n".join(task_lines)

        msg = MessageSchema(
            id=f"msg-{project_id}-analysis",
            projectId=project_id,
            fromId="secretary",
            fromName="🤖 秘书",
            content=f"需求分析完成！\n\n📋 任务拆解：\n{tasks_text}\n\n💡 原因：{team_config.reason}",
            mentions=[],
            attachments=[],
            timestamp=datetime.now().isoformat(),
            type=MessageType.AGENT,
        )
        app_state.add_message(project_id, msg)
        await connection_manager.broadcast_to_project(
            project_id,
            {"type": "new_message", "payload": msg.model_dump()}
        )

    async def _update_requirements(self, project_id: str, requirement: str, team_config) -> None:
        """Update the project requirements (group announcement)."""
        # Build formatted requirements with task breakdown
        task_lines = []
        for role_id, task in team_config.tasks.items():
            from conductor.core.models import PREDEFINED_ROLES
            role = PREDEFINED_ROLES.get(role_id)
            role_name = role.name if role else role_id
            task_lines.append(f"• {role_name}: {task}")

        formatted_req = f"{requirement}\n\n📋 任务分配：\n" + "\n".join(task_lines)

        # Update in app state
        project = app_state.get_project(project_id)
        if project:
            from ..schemas import ProjectResponse
            updated = ProjectResponse(
                id=project.id,
                name=project.name,
                requirement=formatted_req,
                workspace=project.workspace,
                status=project.status,
                team=project.team,
                createdAt=project.createdAt,
                lastUpdated=datetime.now().isoformat(),
                duration=project.duration,
            )
            app_state.update_project(updated)

        # Broadcast requirements update
        await connection_manager.broadcast_to_project(
            project_id,
            {
                "type": "requirements_updated",
                "payload": {
                    "projectId": project_id,
                    "requirements": formatted_req,
                }
            }
        )

    async def _send_team_formed(self, project_id: str, team: list) -> None:
        """Send team formation message and update team panel."""
        # Build team list text
        team_lines = []
        team_schemas = []
        for member in team:
            if member.role:
                team_lines.append(f"  {member.role.emoji} {member.role.name}")
                team_schemas.append(self._member_to_schema(member).model_dump())

        team_text = "\n".join(team_lines)

        # Send team formed message
        msg = MessageSchema(
            id=f"msg-{project_id}-team",
            projectId=project_id,
            fromId="system",
            fromName="系统",
            content=f"团队成员已就位：\n{team_text}",
            mentions=[],
            attachments=[],
            timestamp=datetime.now().isoformat(),
            type=MessageType.SYSTEM,
        )
        app_state.add_message(project_id, msg)
        await connection_manager.broadcast_to_project(
            project_id,
            {"type": "new_message", "payload": msg.model_dump()}
        )

        # Update team panel via team_formed event
        await connection_manager.broadcast_to_project(
            project_id,
            {
                "type": "team_formed",
                "payload": {
                    "projectId": project_id,
                    "team": team_schemas,
                }
            }
        )

    async def _send_task_assignment(self, project_id: str, team: list, team_config) -> None:
        """Send task assignment message with @mentions."""
        # Build assignment text with @mentions
        assignment_lines = []
        mentions = []

        for member in team:
            if member.role and member.role.id in team_config.tasks:
                role_name = member.role.name
                task = team_config.tasks[member.role.id]
                assignment_lines.append(f"@{role_name} {task}")
                mentions.append(role_name)

        assignment_text = "\n".join(assignment_lines)

        msg = MessageSchema(
            id=f"msg-{project_id}-assign",
            projectId=project_id,
            fromId="secretary",
            fromName="🤖 秘书",
            content=f"团队已组建完成！任务分配如下：\n\n{assignment_text}\n\n开始执行！",
            mentions=mentions,
            attachments=[],
            timestamp=datetime.now().isoformat(),
            type=MessageType.AGENT,
        )
        app_state.add_message(project_id, msg)
        await connection_manager.broadcast_to_project(
            project_id,
            {"type": "new_message", "payload": msg.model_dump()}
        )

    async def _on_agent_status_change(
        self,
        project_id: str,
        agent_id: str,
        status,
        current_action: str | None,
    ) -> None:
        """Callback when agent status changes."""
        api_status = self._map_agent_status(status)

        # Update app state
        app_state.update_agent_status(
            project_id,
            agent_id,
            api_status.value,
            current_action,
        )

        # Broadcast via WebSocket
        await connection_manager.broadcast_to_project(
            project_id,
            {
                "type": "agent_status_changed",
                "payload": {
                    "projectId": project_id,
                    "agentId": agent_id,
                    "status": api_status.value,
                    "currentAction": current_action,
                }
            }
        )

    async def _run_orchestrator(
        self,
        orchestrator: Orchestrator,
        requirement: str,
        project_id: str,
        team_config,
    ) -> None:
        """Run the orchestrator in background."""
        try:
            # Continue the orchestrator flow (it already has the project from handle_requirement)
            project = self._projects[project_id]
            orchestrator.project = project

            # Initialize message bus
            from conductor.core.message_bus import MessageBus
            orchestrator.message_bus = MessageBus(workspace=project.workspace)

            # Set agent status change callback
            orchestrator.on_agent_status_change = lambda aid, status, action: asyncio.create_task(
                self._on_agent_status_change(project_id, aid, status, action)
            )

            # Create agents
            await orchestrator._create_agents(project, team_config)

            # Execute tasks
            await orchestrator._execute_tasks(project, team_config)

            # Update final status
            await self._emit_project_status(project_id, "COMPLETED")

            logger.info(f"Project {project_id} completed successfully")

        except asyncio.CancelledError:
            logger.info(f"Project {project_id} was cancelled")
            await self._emit_project_status(project_id, "PAUSED")
        except Exception as e:
            logger.error(f"Project {project_id} failed: {e}")
            await self._emit_project_status(project_id, "FAILED", error=str(e))
        finally:
            # Cleanup
            await orchestrator._cleanup_agents()
            self._running_orchestrators.pop(project_id, None)
            self._tasks.pop(project_id, None)

    async def pause_project(self, project_id: str) -> bool:
        """Pause a running project."""
        if project_id in self._tasks:
            self._tasks[project_id].cancel()
            await self._emit_project_status(project_id, "PAUSED")
            return True
        return False

    async def resume_project(self, project_id: str) -> bool:
        """Resume a paused project."""
        # TODO: Implement resume logic
        # This would require state restoration
        logger.warning(f"Resume not implemented for project {project_id}")
        return False

    async def stop_project(self, project_id: str) -> bool:
        """Stop a running project with full cleanup and notifications."""
        # Get project info first
        project = app_state.get_project(project_id)
        if not project:
            return False

        # 1. Send stop notification message
        stop_msg = MessageSchema(
            id=f"msg-stop-{project_id}",
            projectId=project_id,
            fromId="secretary",
            fromName="🤖 秘书",
            content="⚠️ 项目已被用户手动停止。所有进行中的任务已终止。",
            mentions=[],
            attachments=[],
            timestamp=datetime.now().isoformat(),
            type=MessageType.SYSTEM,
        )
        app_state.add_message(project_id, stop_msg)
        await connection_manager.broadcast_to_project(
            project_id,
            {"type": "new_message", "payload": stop_msg.model_dump()}
        )

        # 2. Set all agents to OFFLINE status
        if project.team:
            for member in project.team:
                app_state.update_agent_status(project_id, member.id, "OFFLINE", None)
                await connection_manager.broadcast_to_project(
                    project_id,
                    {
                        "type": "agent_status_changed",
                        "payload": {
                            "projectId": project_id,
                            "agentId": member.id,
                            "status": "OFFLINE",
                            "currentAction": None,
                        }
                    }
                )

        # 3. Cancel background task if running
        if project_id in self._tasks:
            self._tasks[project_id].cancel()
            try:
                await self._tasks[project_id]
            except asyncio.CancelledError:
                pass

        # 4. Cleanup orchestrator and terminate Claude CLI processes
        if project_id in self._running_orchestrators:
            orchestrator = self._running_orchestrators[project_id]
            await orchestrator._cleanup_agents()
            self._running_orchestrators.pop(project_id, None)

        self._tasks.pop(project_id, None)
        self._projects.pop(project_id, None)

        # 5. Update project status
        await self._emit_project_status(project_id, "FAILED", error="Stopped by user")

        logger.info(f"Project {project_id} stopped by user, all agents terminated")
        return True

    async def inject_user_message(
        self,
        project_id: str,
        message: MessageSchema,
    ) -> None:
        """Inject a user message into the running orchestrator."""
        if project_id not in self._running_orchestrators:
            logger.warning(f"Cannot inject message - project {project_id} not running")
            return

        orchestrator = self._running_orchestrators[project_id]
        if orchestrator.message_bus:
            # Convert API message to core Message
            core_msg = Message(
                id=message.id,
                project_id=message.projectId,
                from_id=message.fromId,
                from_name=message.fromName,
                content=message.content,
                mentions=message.mentions,
                attachments=message.attachments,
            )
            orchestrator.message_bus.publish_sync(core_msg)
            logger.info(f"Injected user message into project {project_id}")


# Global singleton
orchestrator_bridge = OrchestratorBridge()
