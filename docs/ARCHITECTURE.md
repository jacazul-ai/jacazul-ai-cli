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

## 🧭 Agent Config Anchorage

Every supported coding agent keeps its own state directory — settings, skills,
extensions, sessions and credentials. By default each CLI resolves that
directory under `$HOME`, which leaves Jacazul-managed state scattered across
unrelated locations and invisible to the project.

Jacazul anchors that state under `$JACAZUL_HOME/agents/<agent>` instead. The
contract is identical for every agent:

| Agent | Variable | Anchored default | Legacy location |
|---|---|---|---|
| pi | `PI_CODING_AGENT_DIR` | `$JACAZUL_HOME/agents/pi` | `~/.pi/agent` |
| Claude | `CLAUDE_CONFIG_DIR` | `$JACAZUL_HOME/agents/claude` | `~/.claude` |

**Why the variable name matters.** The anchorage variable must be the one the
agent's own CLI reads. An internal bootstrap variable only controls where the
bootstrap writes; the CLI keeps using its own default, and the two silently
diverge. `CLAUDE_CONFIG_DIR` is the variable the Claude CLI honors, which is
why the earlier bootstrap-local `CLAUDE_DIR` was retired.

**Resolution order**, highest priority first:

1. An explicit `PI_CODING_AGENT_DIR` / `CLAUDE_CONFIG_DIR` exported by the
   user — always wins.
2. The Jacazul default under `$JACAZUL_HOME/agents/`.

The launcher exports the variable *before* sourcing the agent bootstrap, and
the bootstrap re-applies the same default so it stays correct when sourced
directly.

### Legacy migration

A pre-anchorage tree is moved into the anchored location exactly once, gated
on three conditions: the anchored path differs from the legacy one, the legacy
tree exists as a real directory, and the anchored target does not exist yet.
Existing anchored state is never merged into.

The tree is **moved, never copied**. These directories hold live credentials,
and a copy would leave a second readable secret on disk while splitting state
across two locations.

Claude adds one precondition with no pi equivalent: it writes `history.jsonl`,
`sessions/` and a daemon lock continuously. If another Claude session is
running, the migration refuses and prints the required action instead of
moving the tree out from under it.

### Accepted constraint

After migration, `~/.claude` no longer exists. The `claude` binary invoked
directly — outside `jacazul-claude` — resolves its own default, finds nothing,
and starts unauthenticated with no history. This is accepted by design: a
compatibility symlink was rejected in favour of a single unambiguous state
location. **Always launch through `jacazul-claude`.**

## 🚀 Versioning & Parity

The project maintains strict version parity across all components (`tw-flow`, `hatch`, `skills`) to ensure instruction-engine alignment.
