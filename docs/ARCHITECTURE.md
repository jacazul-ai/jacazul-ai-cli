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
  - `git-expert/`: Commit standards, workflow modes (`git-mode`), commit census (`git-census`), playbook and review scenarios.
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
  template. It renders a hub of always-on rules only; the triggered
  protocols (onboard and status, session handoff, GUIDE detail, language
  detection, glossary) render from `templates/references/` into
  `skills/jacazul-engine/references/`, and the hub's reference router names
  the trigger for each. The hatch deletes any reference the templates no
  longer produce.
- Persona context has three layers. The hub carries a persona-neutral
  protocol and a roster (name, signature, handoff triggers, voice
  reference). The launcher injects only the active voice, read from
  `JACAZUL_PERSONA_SPEC_FILE` as resolved by `scripts/bootstrap/persona`.
  The other voices stay in `references/personas/<id>.md` until a handoff
  reads one. Loading every voice at once made weaker models blend them.
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
| OpenCode | `XDG_CONFIG_HOME` | `$JACAZUL_HOME/agents/opencode` | `~/.config/opencode` |

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

### Legacy trees: the two agents differ deliberately

| Agent | Pre-existing tree | Behaviour |
|---|---|---|
| pi | `~/.pi/agent` | moved into the anchored dir once |
| Claude | `~/.claude` | left untouched; the anchor starts clean |
| OpenCode | `~/.config/opencode` | moved into the anchored dir once |

pi migrates because its agent directory holds configuration and extensions, and
nothing writes to it continuously.

Claude does not migrate. Its directory holds live credentials alongside
`history.jsonl`, `sessions/` and a daemon that write continuously, so a move
can only be attempted while no session is open. A migration that is refused
halfway — because a session still holds the tree — leaves state split across
two locations, which is worse than starting clean. Carrying anything across is
therefore a deliberate manual step, not something the bootstrap decides.

OpenCode migrates its legacy global directory once when the anchored destination
is absent. An explicit `XDG_CONFIG_HOME` remains authoritative, so users can
select another configuration root without the launcher overriding it.

The practical consequence: the first Claude session under a new anchor
authenticates again and starts with no prior conversation history. What the
bootstrap does provide there is everything Jacazul owns — `settings.json`
seeded from the project template, project skills symlinked into `skills/`, and
project extensions symlinked into `extensions/`.

### Rollback

Because the legacy Claude tree is never touched, reverting costs nothing:

```bash
export CLAUDE_CONFIG_DIR="$HOME/.claude"
```

The previous state — credentials, history and per-project memory — is still
there, and the bootstrap links the Jacazul-owned artifacts into it just the
same.

## 🌊 Embedded Workflow Engine (`jacazul flow`)

The workflow engine (developed today as `jacazul-ai/jaflow`) is moving into the
Go `jacazul` CLI as an **embedded library**, not as an installed component.
`jacazul` imports the engine and compiles it in. There is no separate engine
binary to install, update, version-handshake, or discover on `PATH`: one
`jacazul` release carries exactly one engine version, pinned by `jacazul`'s
`go.mod`.

**Status:** the names, paths and public boundary below are decided. The engine
side (module rename, `flow.Run` extraction, schema guard) is not published
yet, so the `jacazul` side is designed and tested against a fake runner until
the engine tags a release with package `flow`.

### Names

| Item | Value |
|---|---|
| Go module | `github.com/jacazul-ai/flow` (repository renamed from `jaflow`) |
| Public package | `flow`, at the module root |
| User-facing command | `jacazul flow ...` |
| Standalone engine binary | `jczl-flow`, built in the engine repository for tests and independent distribution; `jacazul` does not use it |

### Runtime paths and environment

- Database: `$JACAZUL_HOME/flow/<PROJECT_ID>/flow.sqlite3`.
- Override: `JACAZUL_FLOW_DATABASE_PATH` (replaces `JAFLOW_DATABASE_PATH`).
- Context variables stay: `JACAZUL_HOME`, `JACAZUL_SESSION_ID`, `PROJECT_ID`.

### Public boundary

```go
import "github.com/jacazul-ai/flow"

func Run(ctx context.Context, args []string, env flow.Env, streams flow.Streams) int

type Env struct {
	ProjectID    string
	SessionID    string
	DatabasePath string
	Home         string
}

type Streams struct {
	Stdin  io.Reader
	Stdout io.Writer
	Stderr io.Writer
}

func EnvFromOS() Env // standalone mains only; jacazul must not use it
```

`Run` never calls `os.Exit`, never reads the process environment or `os.Args`,
and never writes to the process stdout on its own. Everything it needs arrives
through its arguments.

### Rules for the `jacazul` side

1. **Build `flow.Env` explicitly.** Resolve project and session once, through
   the existing bootstrap and worktree anchor logic, and always set `Home`.
   The engine falls back to the user home directory when `JACAZUL_HOME` is
   unset, which would put the database under `~/flow/...`.
2. **Thin adapter.** `jacazul flow <args...>` strips `flow` and passes the
   rest as `args`, the process stdio as `Streams`, and the command context as
   `ctx`.
3. **Exit with the returned code.** The adapter exits with the `int` returned
   by `Run`.
4. **Concrete function, not an interface.** A test seam lives in `jacazul`'s
   own package, for example
   `type flowRunner func(context.Context, []string, flow.Env, flow.Streams) int`
   with `flow.Run` as the production value, and tests assert the `Env` and
   `args` passed to it.
5. **No reach into internals.** Never import
   `github.com/jacazul-ai/flow/internal/...` (the compiler forbids it) and do
   not depend on the engine's go-flags setup or domain types. When `jacazul`
   needs data back, such as a structured onboard snapshot, the engine exposes
   a new narrow exported function.
6. **Schema guard is final.** The engine refuses to open a database whose
   schema is newer than it supports, for example after a `jacazul` rollback,
   and prints `ACTION:` guidance. `jacazul` surfaces that error as is; it does
   not retry or bypass it.

Any need the boundary does not cover (extra `Env` fields, returned data,
cancellation behavior) goes back to the engine as a request instead of being
worked around in `jacazul`.

### Impact on the Go code

- The `tw-flow-to-go` bootstrap stub (`cmd/tw-flow`, `internal/cli/app.go`) is
  replaced by the `jacazul flow` adapter over `flow.Run`. A second workflow
  engine does not grow there.
- The engine module requires `go 1.25`; `jacazul`'s `go` directive rises from
  1.24 when the dependency is added. Both sides already use
  `github.com/jessevdk/go-flags v1.6.1`.
- Until the engine publishes its tag, the current `jaflow` binary is not
  copied, vendored, or shelled out to as a stopgap.

### Open questions

- Whether the engine moves a legacy `$JACAZUL_HOME/jaflow/<PROJECT_ID>/`
  database on first open. No real user data exists there today.
- The first engine version `jacazul` pins.

## 🚀 Versioning & Parity

The project maintains strict version parity across all components (`tw-flow`, `hatch`, `skills`) to ensure instruction-engine alignment.
