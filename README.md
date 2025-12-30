# Conductor

> Submit requirements, go grab a coffee, come back to working code.

Conductor transforms AI-assisted development from **synchronous interaction** to **asynchronous delegation**. Stop babysitting your AI coding assistant.

## The Problem

Using AI to build projects today is exhausting:

| Pain Point | What Happens |
|------------|--------------|
| Waiting | AI is working, you're staring at the terminal |
| Interaction | "Continue?" "Yes." "How about this?" "Sure." |
| Tracking | Where is it? What stage? What's the status? |
| Testing | "Done!" ...but you have to test it manually |
| Feedback | Found a bug? Tell it. Another bug? Tell it again. |
| Leave = Stop | Close your laptop = progress halts |

**The core issue**: AI development is synchronous and blocking. You have to be there.

## The Solution

```
$ conductor submit "Build a todo app with user auth and CRUD operations"

📋 Task submitted: task-20241230-001
📱 Plan will be sent to your WeChat for confirmation

# Go walk your dog, grab coffee, do literally anything else...

# 15 minutes later, your phone buzzes:
🎉 Task completed!
   - Backend: 8 API endpoints ✅
   - Frontend: 5 pages ✅
   - Tests: 23/23 passing ✅
   - Run: docker-compose up
```

## How It Works

```
┌─────────────────────────────────────────────────────┐
│                  Conductor Server                    │
│                  (runs 24/7)                         │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Submit → Plan Review → Auto Execute → Notify       │
│             ↑                                       │
│        [Human confirms]                             │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │         Autonomous Loop                      │   │
│  │   Generate → Test → Fix → Test → Fix → Done  │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Key Checkpoints

| Stage | Mode | Why |
|-------|------|-----|
| **Plan** | Human confirms | Direction matters, avoid wasted effort |
| **Design** | Auto | Plan is confirmed, execute it |
| **Development** | Auto + self-healing | Test → Fix → Repeat |
| **Delivery** | Human accepts | Final quality gate |

## Installation

```bash
# Clone the repo
git clone https://github.com/slicenferqin/Conductor.git
cd Conductor

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install dependencies
pip install -e ".[dev]"
```

## Quick Start

```bash
# Start the server (daemon mode)
conductor server --daemon

# Submit a task
conductor submit "Create a blog with posts and comments"

# Check status
conductor status task-xxx

# Pull completed project
conductor pull task-xxx --output ./my-blog
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `conductor submit <requirement>` | Submit a new development task |
| `conductor status <task-id>` | Check task status |
| `conductor list` | List all tasks |
| `conductor pull <task-id>` | Download completed project |
| `conductor server` | Start the Conductor server |

## Configuration

Create `.conductor.yaml` in your home directory:

```yaml
# Notification settings
notifications:
  default: wechat  # or: feishu, email, terminal
  wechat:
    webhook_url: "https://..."
  feishu:
    webhook_url: "https://..."

# Execution settings
execution:
  max_fix_attempts: 3      # Auto-fix attempts before asking for help
  checkpoint_timeout: 30m  # Timeout for human confirmation

# Tech stack (fixed for MVP)
tech_stack:
  backend: fastapi
  frontend: react
  database: postgresql
```

## Project Structure

```
conductor/
├── conductor/
│   ├── cli/                 # CLI client
│   │   └── main.py
│   ├── server/              # Backend service
│   │   └── main.py
│   ├── core/                # Core logic
│   │   ├── task_queue.py    # Task management
│   │   ├── executor.py      # Task execution
│   │   └── decomposer.py    # Requirement analysis
│   ├── integrations/        # External tools
│   │   └── claude_cli.py    # Claude Code integration
│   ├── notifications/       # Notification channels
│   │   └── base.py
│   └── roles/               # AI agent roles
│       └── base.py
├── tests/
├── docs/
│   ├── PRODUCT_SPEC.md      # Product specification
│   └── LESSONS_LEARNED.md   # Claude Code usage notes
└── pyproject.toml
```

## Roadmap

### Phase 1: Core (Current)
- [x] Project structure
- [ ] Task queue and executor
- [ ] Claude Code integration
- [ ] Basic CLI
- [ ] Terminal notifications

### Phase 2: Autonomous Loop
- [ ] Auto-test execution
- [ ] Auto-fix loop
- [ ] WeChat/Feishu notifications
- [ ] Daemon mode

### Phase 3: Polish
- [ ] Web UI for progress
- [ ] Cost estimation
- [ ] Multiple tech stacks

## Tech Stack

- **Backend**: Python 3.11+, FastAPI
- **CLI**: Typer + Rich
- **AI Engine**: Claude Code CLI
- **Generated Projects**: FastAPI + React + PostgreSQL + Docker

## Related Projects

Conductor builds on top of these excellent tools:

- [Claude Code](https://claude.ai/code) - AI coding assistant
- [Beads](https://github.com/steveyegge/beads) - Agent memory system
- [OpenSkills](https://github.com/numman-ali/openskills) - Universal skills loader

## Contributing

Contributions are welcome! Please read our contributing guidelines first.

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**Stop babysitting. Start delegating.**