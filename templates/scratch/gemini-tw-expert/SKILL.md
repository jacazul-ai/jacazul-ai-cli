---
name: taskwarrior-expert
description: Expert system for managing session plans, tasks, and context using Taskwarrior. Use this when managing tasks, creating plans, tracking progress, or storing session context.
license: MIT
---

# Taskwarrior Integration Protocol

## 🌟 Philosophy

**"Plan effectively, execute efficiently, and never lose context."**

## 🚦 Interaction Modes

Modes define the **Agent's Behavior** for a given task. Explicitly setting a mode controls the level of autonomy and the type of output.

| Mode | Behavior | Autonomy | Output |
| :--- | :--- | :--- | :--- |
| **`[DESIGN]`** | Requirements analysis & breakdown. | Low | A structured plan (Task list). |
| **`[INVESTIGATE]`** | Codebase diving & de-risking. | High (Read-only) | Findings & Context. |
| **`[GUIDE]`** | Navigator. Instructions & diffs only. | **Zero** (Write) | Step-by-step guide. |
| **`[EXECUTE]`** | Builder. Implementing changes. | High (Write) | Modified files. |
| **`[TEST]`** | Verification & QA. | High | Test results. |
| **`[DEBUG]`** | Root cause analysis. | High (Read-only) | Diagnosis & fix proposal. |
| **`[REVIEW]`** | Code audit & feedback. | Read-only | Suggestions/Critique. |
| **`[PR-REVIEW]`** | Prepare/Check PR or diffs. | Read-only | Summary & Readiness check. |

**Usage:** Prefix tasks with the mode to enforce behavior.
- `[GUIDE] Implement login` -> I tell you how.
- `[EXECUTE] Implement login` -> I do it.

---

## 📋 The Workflow Loop

### Phase 0: Orient (History-First)
**CRITICAL:** Before touching the filesystem, you MUST understand the mission history.
1.  **Git Log**: Run `git log -n 5` to see recent tactical changes.
2.  **Task Context**: Run `tw-flow context <uuid>` to read previous outcomes and decisions.
3.  **Source of Truth**: If a task is marked `done` with an `OUTCOME`, trust that outcome. Do NOT re-investigate.
4.  **Search Throttling**: Broad searches (recursive greps) are forbidden unless the agent has already read specific files mentioned in history.

### Phase 1: Orient (Ponder)
Before acting, understand the state of the world.
```bash
ponder [project_id]
```
This shows your active, ready, and blocked tasks.

### Phase 2: Create Initiative (Sub-Project)
Break down a goal into a dependency chain.
```bash
tw-flow initiative feature-x \
  "DESIGN|Design API schema|research|today" \
  "PLAN|Break down endpoints|implementation|tomorrow" \
  "EXECUTE|Implement logic|implementation|tomorrow"
```

### Phase 3: Execute (Act)
Pick the top task and work.
```bash
tw-flow execute <id>
```
**CRITICAL:** This command triggers the **Context Briefing**. You MUST read and acknowledge any `══ INHERITED CONTEXT ══` displayed.

### Phase 4: Context (Record)
Document your work as you go. Use `tw-flow note` for mid-task decisions and `tw-flow outcome` for final results.
```bash
tw-flow note <id> decision "Using library Y."
```

### Phase 5: Review (Verify)
**CRITICAL:** Never close a task silently.
1.  Summarize the work.
2.  Show the result (code, file, output).
3.  Ask: "Shall I close this?"

### Phase 6: Outcome (Capture)
Upon user approval ("looks good", "yes"), you **MUST** record the final result. This is the source for **Inherited Context Propagation**.
```bash
tw-flow outcome <id> "Created file X and updated Y."
```

### Phase 7: Close (Finalize)
Only after recording the outcome.
```bash
tw-flow done <id>
```

## 🧠 Context Propagation (The "Briefing")

The system automatically carries intelligence across dependencies.
1.  **Parent Outcomes:** `tw-flow execute` fetches `OUTCOME`, `DECISION`, and `LESSON` notes from all parent tasks.
2.  **Handoffs:** `tw-flow handoff <id> "msg"` bridges the current outcome into the next task's context.

## 🤝 Session Handoff

To ensure continuity between sessions (or agents), use this protocol when wrapping up:

1.  **Close:** Ensure the current task is `done` with a clear outcome.
2.  **Anchor:** Explicitly `execute` the *next* logical task.
3.  **Bridge:** Use `tw-flow handoff <next_id> "..."` to link them.

---

### 🛡 Safety & Archiving

#### 🗑 Soft Delete (Discard)
**NEVER** use `taskp delete`. It is permanent and destroys history.
Use `tw-flow discard <id>` to move tasks to a `:trash` project.

#### 🗄 Archiving Unplanned Tasks
Move legacy/unscoped tasks to the `_archive` project.
```bash
taskp <id> modify $PROJECT_ID:_archive
```

The `ponder` dashboard automatically ignores any project ending in `_archive` or `_trash`.

## 💡 Best Practices

1.  **Bare Identifiers:** Always use the bare `$PROJECT_ID` (no `project:` prefix) when querying or modifying tasks within the established project hierarchy.
2.  **Initiative Names:** Initiatives (sub-projects) MUST use bare names (e.g., `feature-x` instead of `silo:feature-x`). The silo isolation is already handled by the environment.
3.  **Stay in the Lane:** Filter by `$PROJECT_ID` via `taskp` or trust the silo.

---

## 🛠 Core Tools

- **`ponder`**: High-fidelity project dashboard.
- **`tw-flow`**: Standardized task management with context propagation.
- **`taskp`**: **CRITICAL** Project-Aware Taskwarrior Wrapper. Always use `taskp` instead of raw `task` for any command not covered by `tw-flow` to ensure Silo Isolation via `$PROJECT_ID`.
