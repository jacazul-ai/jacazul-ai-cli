# Jacazul AI CLI (Monstro do Lago)

This project provides a powerful, dual-mode environment for running AI-powered command line interface (CLI) tools (Gemini, Opencode, Copilot) within Docker/Podman containers (**CAGED**) or directly on your host (**UNHINGED**).

## ✨ Features

- **Dual-Mode Execution** - Choose between isolated containers (**CAGED**) or high-performance native execution (**UNHINGED**)
- **Jacazul AI Ecosystem** - Optimized for the latest Gemini CLI, Opencode, and Copilot tools
- **Per-project task databases** - Isolated Taskwarrior databases for each project
- **Structured 7-Phase Workflow** - Robust task management with interaction modes
- **Dual-Persona Navigation** - Jacazul (PT-BR) and Cortana (EN) workflow assistants
- **Automated Bootstrap** - Instant environment preparation for each project

## 🚀 Quick Start (UNHINGED Mode)

### 1. Configure the Environment
```bash
./scripts/configure-direct
```

### 2. Run your preferred CLI
```bash
jacazul-gemini      # Gemini CLI (Native)
jacazul-opencode    # Opencode CLI (Native)
jacazul-copilot     # Copilot CLI (Native)
```

### 3. Try the Workflow
```bash
# Check current state
ponder

# Create an initiative
tw-flow initiative my-feature \
  "DESIGN|Design system|research|today" \
  "EXECUTE|Build logic|implementation|tomorrow"

# Start working
tw-flow execute <uuid>
```

## 📚 Documentation

- **[Getting Started](docs/getting-started.md)** - Setup and first steps
- **[Taskwarrior Expert](docs/taskwarrior-expert.md)** - Complete workflow guide
- **[Per-Project Databases](docs/per-project-taskwarrior.md)** - Database architecture and usage
- **[Skills Overview](docs/skills/README.md)** - Available skills
- **[Interaction Modes](docs/interaction-modes.md)** - Understanding PLAN, EXECUTE, GUIDE, etc.

## 🛠 Available Skills

### Taskwarrior Expert (v1.4.0)
Structured workflow management with 7 phases, interaction modes, and per-project database isolation.

**Features:**
- **Per-Project isolation** - Dedicated database at `~/.jacazul-ai/.task/$PROJECT_ID/`
- **Absolute Reliability** - Uses `taskp` and `tw-flow` v1.4.0 with JSON-based status
- **Transparent Feedback** - Split view for PENDING and COMPLETED tasks
- **Ghost-Output Protection** - Optimized command execution and output capture

[→ Complete Guide](docs/taskwarrior-expert.md) | [→ Architecture](docs/per-project-taskwarrior.md)

## 📁 Project Structure

```
/project/
├── docs/              # Documentation
├── scripts/           # Entry points & Bootstraps
│   ├── bootstrap/     # Environment preparation scripts
│   ├── jacazul-*      # CLI wrappers (unhinged/sandboxed)
├── templates/         # Agent & Skill definitions
│   ├── agents/        # Jacazul & Cortana persona files
│   ├── skills/        # Taskwarrior & Jacazul skills
└── sandbox/           # Persistent data directories
```

## 🔧 Development

### Running the Smoke Tests
```bash
./templates/skills/taskwarrior_expert/scripts/run_smoke.py
```

## 📝 License

MIT

## 🐊 Jacazul Agent

**Jacazul** is your AI workflow navigator. He speaks PT-BR, knows the mission, and keeps you in the flow.

### Commands
- **`onboard`** — Initialize session context
- **`ponder`** — Refresh status dashboard
- **`tw-flow status`** — Focused initiative view
- **`tw-flow initiatives`** — List all active initiatives

**📖 Full documentation:** `docs/agents/jacazul.md`

---
