# Jacazul AI CLI (Monstro do Lago)

This project provides a powerful, dual-mode environment for running AI-powered command line interface (CLI) tools (Gemini, Opencode, Copilot) within Docker/Podman containers (**CAGED**) or directly on your host (**COMPANION**).

## ✨ Features

- **JIT Prompt Forge** - Just-in-Time generation of session-aware instructions.
- **Dual-Mode Execution** - Choose between isolated containers (**CAGED**) or high-performance native execution (**COMPANION**).
- **Jacazul AI Ecosystem** - Optimized for Gemini CLI, Opencode, and Copilot tools.
- **Per-project task databases** - Isolated Taskwarrior databases for each project.
- **Structured 7-Phase Workflow** - Robust task management with interaction modes.
- **Context Delegation** - Intelligent Lazy Loading to minimize context window bloat.

## 🏗️ Project Architecture (JIT Forge)

Jacazul AI CLI uses a dynamic factory to forge prompts during initialization.

### Core Structure
- **/agents/**: Generated persona files (Copilot/Opencode). These use **Context Delegation**.
- **/skills/**: Expert capability modules.
  - `jacazul-gemini/`: Full unified context for Gemini CLI.
  - `jacazul-partial/`: Core technical logic (UUID, Git, TW) for agent delegation.
  - `taskwarrior-expert/`, `python-expert/`, etc.
- **/scripts/jacazul/**: The **Incubator**. Contains the `hatch.py` engine and Tornado templates (`.tmpl`).
- **/build/**: Destination for tool-specific generated artifacts (git-ignored).

### Context Delegation (Lazy Loading)
To optimize the context window, Copilot and Opencode agents are generated with identity and voice only, delegating core technical mandates to the `jacazul-partial` skill. Gemini CLI receives a single, unified `jacazul-gemini` skill containing the full context.

## 🚀 Quick Start (COMPANION Mode)

### 1. Configure the Environment
```bash
make configure
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
