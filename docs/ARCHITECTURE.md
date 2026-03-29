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

## 🔒 Security & Isolation

- **Per-project task databases**: Taskwarrior data is stored in isolated directories per `PROJECT_ID`.
- **Credential Protection**: Handled via `jacazul-broker` and hierarchical vault resolution.
- **Environment Modes**:
    - **CAGED**: High-isolation Docker/Podman containers.
    - **COUNSELOR**: High-performance native host execution.

## 🚀 Versioning & Parity

The project maintains strict version parity across all components (`tw-flow`, `hatch`, `skills`) to ensure instruction-engine alignment.
