# AI CLI Sandboxed

This project provides a containerized environment for running AI-powered command line interface (CLI) tools within Docker or Podman containers on Linux. It offers a flexible, isolated, and reproducible environment for experimenting with and deploying AI CLI agents.

## ✨ Features

- **Containerized CLI environment** - Isolated and reproducible
- **Supports Docker and Podman** - Use your preferred container runtime
- **Per-project task databases** - Isolated Taskwarrior databases for each project
- **Pre-configured workflows** - Taskwarrior integration with structured 7-phase workflow
- **Skill-based system** - Modular capabilities for different tasks
- **Session persistence** - Maintain context across sessions
- **Optimized for Linux** - Designed for Linux container environments

## 🚀 Quick Start

### Build the Container
```bash
# Using Docker
docker build -f Dockerfile.copilot -t ai-cli-copilot .

# Using Podman
podman build -f Dockerfile.copilot -t ai-cli-copilot .
```

### Run the Container
```bash
# Docker
docker run -it --rm ai-cli-copilot

# Podman
podman run -it --rm ai-cli-copilot
```

### Try Taskwarrior Workflow
```bash
# Check current state (auto-detects project)
ponder piraz_ai_cli_sandboxed

# Create a plan (uses per-project database)
tw-flow plan piraz_ai_cli_sandboxed:my-feature \
  "Design API|research|today" \
  "Build API|implementation|tomorrow"

# Start working
tw-flow execute <task_id>

# Use taskp for direct task management
taskp list                    # Lists tasks in project database
taskp add "New task"          # Adds to project database
```

## 📚 Documentation

- **[Getting Started](docs/getting-started.md)** - Setup and first steps
- **[Taskwarrior Expert](docs/taskwarrior-expert.md)** - Complete workflow guide
- **[Per-Project Databases](docs/per-project-taskwarrior.md)** - Database architecture and usage
- **[Skills Overview](docs/skills/README.md)** - Available skills

## 🛠 Available Skills

### Taskwarrior Expert (v1.3.0)
Structured workflow management with 7 phases, interaction modes, and per-project database isolation.

**Features:**
- **Per-project databases** - Isolated task storage for each project
- **Project-aware wrapper** (`taskp`) - Auto-detects current project
- Dashboard visualization (`ponder`) - Project-specific views
- Task management (`tw-flow` v1.3.0) - Enhanced with TASKDATA support
- Session continuity and handoffs
- 18+ comprehensive tests

**New in v1.3.0:**
- Automatic project detection via `PROJECT_ID`
- Per-project database isolation (`~/.task/$PROJECT_ID/`)
- Backward compatible with central database

[→ Complete Guide](docs/taskwarrior-expert.md) | [→ Architecture](docs/per-project-taskwarrior.md)

## 📁 Project Structure

```
/project/
├── docs/              # Documentation
├── templates/         # Agent configurations
│   ├── skills/       # Available skills
│   └── context/      # Agent instructions
├── scripts/          # CLI wrappers
├── sandbox/          # Sandboxed environments
└── Dockerfile.*      # Container definitions
```

## 🔧 Development

### Adding a New Skill
1. Create skill directory in `templates/skills/`
2. Add SKILL.md documentation
3. Create helper scripts in `scripts/`
4. Add tests
5. Update documentation

### Running Tests
```bash
# Taskwarrior skill tests
./templates/skills/taskwarrior_expert/scripts/test-tw-flow.sh
```

## 🤝 Contributing

Contributions welcome! Please ensure:
- Documentation is updated
- Tests pass
- Follows existing patterns
- Uses Conventional Commits

## 📝 License

MIT

## 🔗 Resources

- [Taskwarrior Documentation](https://taskwarrior.org/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [Podman Documentation](https://podman.io/)

## 🐊 Jacazul Agent - Quick Context

**Jacazul** (Jacaré Azul / Blue Alligator) is your AI workflow navigator — get instant project orientation with one command.

### Get Started
```bash
# In any Copilot CLI session:
onboard
```

Jacazul will:
1. ✅ Activate taskwarrior-expert skill
2. ✅ Display your environment (git user, PROJECT_ID, paths)
3. ✅ Show project dashboard (pending, active, overdue tasks)
4. ✅ Present actionable next steps
5. ✅ Wait for your direction

### Commands
- **`onboard`** — Initialize session context
- **`ponder`** — Refresh status dashboard
- **`planos`** — List all project plans
- **`trabalhar em [plan]`** — Focus on specific plan

**📖 Full documentation:** `docs/agents/jacazul.md`

---

