# Jacazul AI CLI — Technical Architecture

This document provides a deep dive into the internal structure, file layouts, and CLI entry points of the Jacazul AI CLI ecosystem.

## 🏗️ Project Architecture (Python Standard Package)

Jacazul AI CLI is structured as a standard Python package for maximum robustness and professional distribution.

### Core Structure
- **`jacazul/`**: Root Python package (Flat Layout).
  - `hatch/`: The **Incubator**. Contains the Prompt Forge engine and dynamic templates.
  - `taskwarrior/`: Specialized logic for per-project Taskwarrior databases.
  - `cli/`: Entry point implementations for all CLI tools.
- **`skills/`**: Expert capability modules (Markdown-based instructions).
  - `jacazul-engine/`: Core protocols (UUID, Language, Handoff, Output Caching).
  - `taskwarrior-expert/`: Workflow management and persistence.
  - `python-expert/`: PEP 8 compliance and automated linting.
  - `git-expert/`: Conventional commits and repository integrity.
- **`tests/`**: Consolidated smoke test suite.
- **`pyproject.toml`**: Centralized dependency and entry point configuration.

### CLI Tools (Entry Points)
The following commands are automatically installed into the environment:
- `tw-flow`: Main workflow manager (inis, execute, done, outcome, ticket, amend, reopen).
- `taskp`: Project-aware Taskwarrior wrapper.
- `ponder`: Tactical project dashboard.
- `jacazul-hatch`: JIT Prompt Forge manual trigger.
- `jacazul-persona`: Persona switching (Jacazul <-> Codana).
- `py-check`: PEP 8 quality gate and auto-beautifier.
- `jacazul-claude`: Claude CLI (Native) integration.

## 🧩 Prompt Generation Ownership

Prompt generation has one neutral core and target-specific adapters:

- `jacazul/hatch/templates/gemini_full.md` is the canonical shared engine
  template.
- `jacazul/hatch/templates/agent_master.md` is rendered only for targets with
  a native agent format, currently Copilot and Opencode.
- `jacazul-hatch --target pi` and `--target openai` generate the shared engine
  without inventing client-specific agent files.
- `jacazul-hatch --target all` expands the supported target allowlist, writes
  the shared engine once, and then renders eligible adapters.
- `scripts/bootstrap/hatch` selects the runtime target from its argument or
  `JACAZUL_HARNESS`; client bootstraps remain responsible for linking and
  runtime configuration.

The `--client` option remains a compatibility alias for `--target`. Provider
names such as OpenAI are treated as prompt consumers, not launcher-specific
filesystem layouts.

## 🔒 Security & Isolation

- **Per-project task databases**: Taskwarrior data is stored in isolated directories per `PROJECT_ID`.
- **Credential Protection**: Handled via `jacazul-broker` and hierarchical vault resolution.
- **Environment Modes**:
    - **CAGED**: High-isolation Docker/Podman containers.
    - **COUNSELOR**: High-performance native host execution.

## 🚀 Versioning & Parity

The project maintains strict version parity across all components (`tw-flow`, `hatch`, `skills`) to ensure instruction-engine alignment.
