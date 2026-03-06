# Taskwarrior Expert Skill

Complete guide for the taskwarrior-expert skill - a structured workflow system for managing tasks, initiatives, and session context using Taskwarrior.

## 📍 Script Locations (IMPORTANT)

**When this skill is activated in UNHINGED mode, scripts are located at:**

```
~/bin/  (Symlinked from /project/skills/taskwarrior_expert/scripts/)
```

**Available scripts:**
- `skills/taskwarrior_expert/scripts/tw-flow` - Main workflow tool (v1.7.0)
- `skills/taskwarrior_expert/scripts/taskp` - Project-aware wrapper
- `skills/taskwarrior_expert/scripts/ponder` - Dashboard visualization (v1.6.0)

**How to use them:**

```bash
# Option 1: Direct path
/project/skills/taskwarrior_expert/scripts/tw-flow status

# Option 2: If scripts are in PATH (after configure)
tw-flow status
```

**For AI Agents:** Always use `taskp` or `tw-flow`. NEVER invoke the raw `task` binary directly to maintain project isolation.

---

## 🎯 Overview

The taskwarrior-expert skill transforms Taskwarrior into a powerful workflow engine with:
- **7-phase structured workflow** for consistent task execution
- **8 interaction modes** controlling agent autonomy levels
- **Per-project isolation** via `PROJECT_ID` detection
- **Dashboard visualization** for quick state assessment
- **Context preservation** via structured annotations and inherited context

## 🚀 Quick Start

### 1. Check Current State
```bash
tw-flow ponder
```
*Pro-tip: You can also use the standalone `ponder` command, but `tw-flow ponder` is recommended for better workflow integration.*

### 2. Create an Initiative
```bash
tw-flow initiative my-feature \
  "DESIGN|Design API schema|research|today" \
  "EXECUTE|Implement endpoints|implementation|tomorrow" \
  "TEST|Write tests|testing|2days"
```

### 3. Execute Tasks
```bash
# Start work
tw-flow execute <uuid>

# Add context
tw-flow note <uuid> research "Found library X supports feature Y"
tw-flow note <uuid> decision "Using approach A for performance"

# Record outcome and complete
tw-flow outcome <uuid> "Implemented OAuth flow with JWT tokens"
tw-flow done <uuid>
```

---

## 📋 The 7-Phase Workflow

### Phase 1: Orient (Ponder)
**Purpose:** Understand the current state before acting.
```bash
ponder
```
**Tactical View (v1.4.0):**
- **Initiative Landscape:** Summary of active/ready tasks per initiative.
- **Tactical Readout:** Columnar table showing Status (⚡ ACTIVE, !! OVERDUE), UUID, Mode, and Urgency.

---

### Phase 2: Initiative (Decide)
**Purpose:** Break down goals into actionable dependency chains.
```bash
tw-flow initiative <feature> <tasks...>
```
**Task format:** `"MODE|description|tag|due_offset"`
*Note: The `plan` command is deprecated in favor of `initiative`.*

---

### Phase 3: Execute (Act)
**Purpose:** Start working on the highest priority ready task.
```bash
tw-flow execute <uuid>
```
**Context Propagation:** Displays inherited `OUTCOME`, `DECISION`, and `LESSON` notes from parent tasks automatically.

---

### Phase 4: Context (Record)
**Purpose:** Document work as you go for future reference.
```bash
tw-flow note <uuid> <type> <message>
```
Types: `research` (r), `decision` (d), `blocked` (b), `lesson` (l), `question` (q), `hypothesis` (y), `ac` (a), `note` (n), `link`.

---

### Phase 5: Review (Verify)
**Protocol:**
1. Summarize accomplishment.
2. Show results (code, output, tests).
3. Ask user: "Shall I close this task?"

---

### Phase 6: Outcome (Capture)
**Purpose:** Record final results BEFORE closing. **MANDATORY** for `tw-flow done`.
```bash
tw-flow outcome <uuid> "What was achieved"
```

---

### Phase 7: Close (Finalize)
```bash
tw-flow done <uuid> [optional_note]
```
Checks for newly unblocked tasks and updates initiative progress.

---

## 🚦 Interaction Modes

| Mode | Behavior | Autonomy | Use When |
|------|----------|----------|----------|
| **[PLAN]** | Analysis & breakdown | Low | Need requirements consensus |
| **[INVESTIGATE]** | Code exploration | High (Read) | Unknown codebase |
| **[GUIDE]** | Step-by-step instructions | Zero | User wants manual control |
| **[EXECUTE]** | Building/Coding | High | Approach is clear |
| **[TEST]** | QA & Verification | High | Need validation |
| **[DEBUG]** | Root cause analysis | High (Read) | Something is broken |
| **[REVIEW]** | Code audit | Read-only | Quality check needed |
| **[PR-REVIEW]** | Readiness check | Read-only | Before merging |

---

## 🛠 Advanced Commands (v1.4.0)

### tw-flow status
Shows initiative status with a **split view** (shows both PENDING and COMPLETED by default):
- **PENDING:** Tasks remaining in the initiative. Includes ticket display if available.
- **COMPLETED:** History of what has already been done.
- **Flag `--pending`**: Use to hide completed tasks and show only pending ones.
- **Flag `--table`**: Output status as a Markdown table (ideal for AI interfaces).
*Auto-detects active initiative if no argument provided.*

### tw-flow tree
Visualizes dependencies in an ASCII tree:
```
 Initiative: my-feature ══
 ✓ (ae749be5) | Design phase
   ├── ⚡ (4facb768) | Implementation
   └── 🔒 (0e7ab763) | Testing (Blocked)
```

### tw-flow ticket (UDA Integration)
Link a task to an external issue/ticket using the `externalid` UDA.
```bash
tw-flow ticket <uuid> "#JAC-013"
```

### tw-flow amend (Metadata Fix)
Update description or ticket for any task (pending or completed) without triggering workflow errors.
```bash
tw-flow amend <uuid> description="New desc" ticket="#JAC-456"
```

### tw-flow reopen
Revert a completed task back to the `pending` state for additional work.
```bash
tw-flow reopen <uuid>
```

### tw-flow discard
Soft delete a task by moving it to an `_archive` project and marking it done.

### tw-flow focus (Anchor System)
Manage session continuity by "locking" attention on specific initiatives or tasks.
- `tw-flow focus ini <name>`: Anchors the session to a specific initiative.
- `tw-flow focus task <uuid>`: Anchors to a task and pushes it to the focus stack.
- `tw-flow focus pop`: Reverts focus to the previous task in the stack.
- `tw-flow focus interest add <name>`: Adds an initiative to the "Signal over Noise" dashboard.
- `tw-flow focus clear`: Resets all session anchors.

### ponder --all
Bypass interest filters to see the full global project status.
- **Flag `--table`**: Output the tactical readout as a Markdown table.
*Note: A warning is shown when using standalone `ponder` instead of `tw-flow ponder`.*

---

## 🛡 Security & Process Enforcement (v1.4.0)

The v1.4.0 update introduces several measures to ensure data integrity and process compliance:

### 1. Mandatory OUTCOME Record
The `tw-flow done` command now **enforces** the presence of an `OUTCOME:` annotation.
- **Goal:** Prevent "ghost tasks" closed without documentation.
- **Behavior:** If no outcome is found, the command will block and provide instructional guidance on how to use `tw-flow outcome`.

### 2. Taskp Vaccination (Command Interception)
To prevent agents (or users) from bypassing the workflow, the `taskp` wrapper now intercepts specific commands:
- **Blocked:** `taskp <uuid> done` is restricted.
- **Blocked:** Manual addition of the `+DISCARDED` tag via `taskp modify`.
- **Reason:** These actions must go through `tw-flow` to ensure proper archiving and documentation.

### 3. Automatic Discard Audit
The `tw-flow discard` command has been enhanced to maintain a perfect audit trail:
- **Auto-Archive:** Moves tasks to a dedicated `: _archive` project.
- **Auto-Tag:** Adds the `+DISCARDED` tag.
- **Auto-Outcome:** Automatically annotates the task with `OUTCOME: Task discarded and moved to archive.`

### 4. Prompt Marketing & Workflow Awareness
The update introduces low-friction alerts within `tw-flow status` and `tw-flow focus`.
- **Behavior:** If a focused task has an `externalid` attached (directly or inherited from ancestors), a tactical alert is displayed.
- **Example:** `🐊 ALERT: Inherited ticket detected (#16). Git-expert will use this for automated commit referencing.`

### 5. Completed Task Protection
Commands that modify task state (`execute`, `done`, `note`, `ticket`, `outcome`, `handoff`) are blocked for COMPLETED tasks.
- **Guidance:** If a modification is attempted, the system provides an instructional error recommending `amend` for metadata fixes or `reopen` for additional work.

---

---

## 🔄 Taskwarrior Version Parity (v1.8.0)

To ensure data integrity between different host operating systems (e.g., Debian 12 with TW 2.6.2 and Fedora 43 with TW 3.4.1), the system implements an automatic version parity and migration logic.

### 1. Host Version Detection
The `scripts/bootstrap/environment` script automatically detects the host's Taskwarrior version or package manager (dnf/apt) to determine the target environment.
- **Taskwarrior 3 (Host):** Triggers `ai-sandbox-fedora` image selection (Fedora 43 based).
- **Taskwarrior 2 (Host):** Triggers `ai-sandbox` image selection (Ubuntu/Debian based).

### 2. Automatic SQLite Migration
When running in a Taskwarrior 3 environment (e.g., Fedora 43 container), the `scripts/bootstrap/taskwarrior` script detects legacy 2.x data (`.data` files) and performs an automatic migration to SQLite.
- **Backup:** A full backup of `.data` files is created at `~/.jacazul-ai/.task-backups/migration-TIMESTAMP/` before any changes.
- **Import:** Executes `task import-v2 rc.hooks=0` to convert the database to the new **Taskchampion** (SQLite) format.
- **Validation:** The migration is per-project (using `TASKDATA` isolation), ensuring that each initiative is converted safely and independently.

### 3. Cross-Version Commands
- **task import-v2**: Used ONLY in Taskwarrior 3 environments to import legacy data.
- **tw-flow status**: Automatically detects and handles both legacy and SQLite databases depending on the available binary version.

---

## 💡 Best Practices

1. **Use UUIDs:** Always refer to tasks by their 8-character UUID.
2. **One Active Task:** Avoid having multiple active tasks in the same initiative to maintain focus and urgency accuracy.
3. **Structured Notes:** Use prefixes (`RESEARCH:`, `DECISION:`) to make context retrieval easy for future agents.
4. **Never Bypass Abstractions:** Bypassing `taskp` to use `task` directly breaks project isolation and data integrity.

---

**Version:** 1.7.0  
**Last Updated:** 2026-03-03
