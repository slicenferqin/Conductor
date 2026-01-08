# Conductor Feature Roadmap

## v2.1 - Multi-Agent Enhancement (Next Milestone)

### 1. Git Worktree Isolation (Priority: High)
**Description:** Each Agent works in an isolated git worktree to enable true parallel development without file conflicts.

**Benefits:**
- True parallel execution (3 tasks in parallel = 3x faster)
- No file conflicts between agents
- Each agent works on separate branch
- Clean git history for code review
- Easy merge/rebase workflow

**Implementation:**
```bash
# Create worktree for each agent
git worktree add ./agent-researcher -b feature/research
git worktree add ./agent-frontend -b feature/frontend
git worktree add ./agent-backend -b feature/backend
```

**Tasks:**
- [ ] Modify `Agent` class to create git worktree on init
- [ ] Update `Orchestrator` to manage worktrees
- [ ] Implement automatic PR creation on task completion
- [ ] Add one-click merge/rebase in UI

---

### 2. Kanban View (Priority: Medium)
**Description:** Add a visual Kanban board view for task management alongside the chat view.

**Features:**
- Columns: Backlog → In Progress → Review → Done
- Drag-and-drop task prioritization
- Visual agent status indicators
- Task dependency visualization

**Tasks:**
- [ ] Create `KanbanBoard` component
- [ ] Add task model with status field
- [ ] Implement drag-and-drop with `@dnd-kit/core`
- [ ] Add view toggle (Chat / Kanban) in header

---

### 3. Multi-Agent Backend Support (Priority: Medium)
**Description:** Support multiple AI coding agents beyond Claude CLI.

**Supported Agents:**
- [x] Claude Code (current)
- [ ] Gemini CLI
- [ ] OpenAI Codex
- [ ] Cursor CLI
- [ ] Local models (Ollama)

**Implementation:**
- Create `AgentBackend` interface
- Implement adapters for each agent type
- Add agent selection in project settings

---

### 4. VS Code Extension (Priority: Low)
**Description:** Bring Conductor into the IDE with a VS Code extension.

**Features:**
- View agent status in sidebar
- Quick task creation
- Real-time message notifications
- Jump to file from chat messages

---

## v2.2 - Persistence & Reliability

### 5. Database Persistence
**Description:** Move from in-memory storage to persistent database.

**Tasks:**
- [ ] Add SQLite/PostgreSQL support
- [ ] Persist projects, messages, team configs
- [ ] Implement message pagination
- [ ] Add project history/archive

### 6. Session Recovery
**Description:** Allow resuming paused projects by restoring agent sessions.

**Tasks:**
- [ ] Save agent session_id to persistent storage
- [ ] Implement `--resume` flag usage for Claude CLI
- [ ] Track task execution progress
- [ ] Add checkpoint/restore mechanism

---

## v2.3 - Collaboration & Sharing

### 7. GitHub Integration
- Auto-create PRs on task completion
- Link commits to agent messages
- PR review workflow in UI

### 8. Team Collaboration
- Multiple users per project
- Role-based access control
- Real-time collaboration

---

## References

- [Vibe Kanban](https://github.com/BloopAI/vibe-kanban) - Inspiration for git worktree isolation
- [Claude Agent SDK](https://github.com/anthropics/claude-code) - Agent framework
