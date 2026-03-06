# Jacazul AI CLI (Monstro do Lago)

This project provides a powerful, dual-mode environment for running AI-powered command line interface (CLI) tools (Gemini, Opencode, Copilot) within Docker/Podman containers (**CAGED**) or directly on your host (**COUNSELOR**).

## ✨ Features

- **JIT Prompt Forge** - Just-in-Time generation of session-aware instructions.
- **Dual-Mode Execution** - Choose between isolated containers (**CAGED**) or high-performance native execution (**COUNSELOR**).
- **Jacazul AI Ecosystem** - Optimized for Gemini CLI, Opencode, and Copilot tools.
- **Per-project task databases** - Isolated Taskwarrior databases for each project.
- **Structured 7-Phase Workflow** - Robust task management with interaction modes.
- **Context Delegation** - Intelligent Lazy Loading to minimize context window bloat.

## 🏗️ Project Architecture (Python Standard Package)

Jacazul AI CLI is structured as a standard Python package for maximum robustness and professional distribution.

### Core Structure
- **`jacazul/`**: Root Python package (Flat Layout).
  - `hatch/`: The **Incubator**. Contains the Prompt Forge engine and dynamic templates.
  - `taskwarrior/`: Specialized logic for per-project Taskwarrior databases.
  - `cli/`: Entry point implementations for all CLI tools.
- **`skills/`**: Expert capability modules (Markdown-based instructions).
  - `jacazul-engine/`: Core protocols (UUID, Language, Handoff).
  - `taskwarrior-expert/`, `python-expert/`, `git-expert/`.
- **`tests/`**: Consolidated smoke test suite.
- **`pyproject.toml`**: Centralized dependency and entry point configuration.

### CLI Tools (Entry Points)
The following commands are automatically installed into the environment:
- `tw-flow`: Main workflow manager (inis, execute, done, outcome, ticket, amend, reopen).
- `taskp`: Project-aware Taskwarrior wrapper.
- `ponder`: Tactical project dashboard.
- `jacazul-hatch`: JIT Prompt Forge manual trigger.
- `jacazul-persona`: Persona switching (Jacazul <-> Cortana).
- `py-check`: PEP 8 quality gate and auto-beautifier.

## 🚀 Quick Start (COUNSELOR Mode)

### 1. Configure the Environment
```bash
make configure
```
*This initializes the virtual environment and installs the Jacazul package in editable mode.*

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

# Create an initiative (ini)
tw-flow ini my-feature \
  "DESIGN|Design system|research|today" \
  "EXECUTE|Build logic|implementation|tomorrow"

# Start working
tw-flow execute <uuid>
```

## 🛠️ Expert Skills

- **Taskwarrior Expert:** Workflow management and persistence.
- **Python Expert:** PEP 8 compliance and automated linting.
- **Git Expert:** Conventional commits and repository integrity.
- **Commit Expert:** Standardized commit message generation.

## 📝 License

MIT

---

**Philosophy:** "Plan effectively, execute efficiently, and never lose context."
