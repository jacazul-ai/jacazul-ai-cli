# 🐊 tw-flow session

Agent session management — restore context, not conversation.

> For operational plans and tasks, see [tw-flow.md](tw-flow.md).
> For the roadmap ledger, see [tw-flow-roadmap.md](tw-flow-roadmap.md).

---

## The Problem

AI agents have a fundamental asymmetry: their **working memory**
(context window) degrades continuously, while the **project state**
(Taskwarrior tasks, decisions, outcomes) is deterministic and permanent.

As a session runs longer, the agent loses track of earlier decisions,
forgets why a particular approach was chosen, and starts making
inconsistent moves. The conversation history is not a reliable anchor —
it is noisy, compresses poorly, and is agent-specific (Claude history
does not transfer to Gemini).

The Jacazul state is different. Every decision, research finding, and
outcome is stored as a structured annotation in Taskwarrior — not in the
conversation. This means the **mission state is always recoverable**,
independent of how degraded the current context window is.

`tw-flow session` operationalizes this: it provides the tools to capture
what the agent knows at peak clarity, and inject it deterministically on
the next startup — giving a cold agent the exact situational awareness
it needs to continue without interruption.

---

## Concepts

### Jacazul Session vs CLI Session

| | Jacazul Session | CLI Session |
|---|---|---|
| **Stored in** | `focus-{SESSION_ID}.json` | CLI-specific (e.g. Claude `--resume`) |
| **Contains** | Task focus, plan anchor, task track | Conversation history |
| **Reliability** | Deterministic — always recoverable | Degrades over time |
| **Scope** | Any agent (Claude, Gemini, Copilot) | Agent-specific |

The CLI `--resume` flag is for conversation continuity. The Jacazul
session is for **mission continuity** — independent of which agent or
conversation picks it up.

### Session File

Each independent session creates `focus-{SESSION_ID}.json` in
`$JACAZUL_HOME/.task/{PROJECT_ID}/`. The file stores:

- `focused_plan` — active plan name
- `focused_task_uuid` — anchored task
- `task_track` — navigation history

A session file only exists when `tw-flow focus ind` is used. The global
`focus.json` is used by default and is never listed or purged.

---

## Commands

```bash
tw-flow session list                    # List all independent sessions
tw-flow session dump                    # Generate introspective handoff note
tw-flow session purge                   # Remove orphan session files
```

---

## tw-flow session list

Shows all `focus-*.json` files with live status.

```
SESSION ID   PLAN               TASK       AGE    STATUS
7533158a  *  roadmap-engine     28714fce   12m    active
eb417008     roadmap-engine     b113d535   1d     idle
651c3b75     arnalbam           c4db7db2   4d     orphan
```

`*` marks the current session (`$JACAZUL_SESSION_ID`).

### Heartbeat (mtime-based)

Session liveness is tracked via file modification time —
`os.path.getmtime()`. Cross-platform: works on Windows PowerShell,
Linux, and macOS without PID or daemon dependencies.

Every `tw-flow` command touches the active session file via
`os.utime(focus_file, None)` to keep mtime fresh.

| Age | Status |
|---|---|
| < 2h | `active` |
| 2h – 8h | `idle` |
| > 8h | `orphan` |

---

## tw-flow session dump

Generates a structured handoff note for the current session.

```bash
tw-flow session dump
# → writes session-note-{SESSION_ID}.md
```

### What it captures

The core signal is the **gap** between what was planned and what is
actually happening. This gap is what context degradation erases — and
what no task annotation fully captures.

A task can say `[EXECUTE] Implement roadmap init guard`. It cannot say
"we got halfway through, the tricky part is that `taskp done` is
intercepted by the workflow enforcement and needs `tw-flow outcome`
first, and we haven't run the tests yet." That knowledge only exists
in the agent's active context. `session dump` extracts it before it
disappears.

**Collected automatically from Taskwarrior + git:**
- Current focus (plan + task UUID)
- Full inherited context: all `DECISION`, `OUTCOME`, `RESEARCH`
  annotations from the task lineage
- `git diff --stat` of uncommitted files
- Pending tasks in the active plan with their urgency

**Filled in by the agent** via a prompt template (introspective layer):
1. Exactly where execution stopped — the last concrete action taken
2. What is not obvious from the code or task annotations
3. Known gotchas, blockers, or partial states left in the codebase
4. The single next concrete action to take on resume

### On next session startup

If `session-note-{SESSION_ID}.md` exists, the bootstrap injects it as
a system prompt **once**, then archives it to `session-notes/`. It is
never printed twice.

---

## tw-flow session purge

Removes session files with `orphan` status (mtime > 8h).

```bash
tw-flow session purge           # Preview orphans
tw-flow session purge --confirm # Actually delete
```

The global `focus.json` is never purged.

---

## Resume a Session

When a session exits, the wrapper prints:

```
╭─ 🐊 Jacazul Session ───────────────────────────────────────╮
│  To resume: jacazul-claude --jacazul-session 7533158a      │
╰────────────────────────────────────────────────────────────╯
```

On the next launch with `--jacazul-session <id>`, the bootstrap sets
`JACAZUL_SESSION_ID=<id>` and `tw-flow` automatically picks up
`focus-{id}.json` — restoring the exact mission state without any
manual `tw-flow focus ind`.

### How it works

The wrapper scripts (`jacazul-claude`, `jacazul-gemini`, etc.) use a
regular process call instead of `exec`, keeping the shell alive after
the CLI exits to run the exit banner.

```bash
# Launch CLI (no exec — shell stays alive)
"$CLAUDE_BIN" --append-system-prompt "$ONBOARD_PROMPT" "$@"

# Exit banner
echo "╭─ 🐊 Jacazul Session ───────────────────────────────────────╮"
echo "│  To resume: jacazul-claude --jacazul-session $JACAZUL_SESSION_ID  │"
echo "╰────────────────────────────────────────────────────────────╯"
```

---

## Autonomous Orchestration (Future Direction)

`tw-flow session dump` is designed as a building block for autonomous
multi-agent orchestration — not just a manual developer tool.

An agent running in a long session can detect its own context
degradation (reasoning quality drop, inconsistent decisions, increasing
uncertainty) and trigger a handoff **without human intervention**:

```
Agent detects degradation
        ↓
tw-flow session dump   ← introspection + gap captured at peak clarity
        ↓
MCP / API call → Orchestrator
        ↓
New agent instance launched with --jacazul-session <id>
        ↓
Bootstrap injects session-note once
        ↓
Mission continues from exact state
```

The orchestrator is stateless — it only moves the session pointer. All
mission state lives in Taskwarrior and the session note. The incoming
agent gets the same situational awareness the previous agent had at its
clearest moment, not at its most degraded.

This is a **self-healing context loop**: the system compensates for the
fundamental limitation of finite context windows without requiring a
human to notice the degradation and intervene.

The MCP/API interface for the orchestrator call is out of scope for the
current `session-resume` plan — tracked as a future initiative.

---

**Status:** Design in progress — `session-resume` plan
**Last Updated:** 2026-04-04
