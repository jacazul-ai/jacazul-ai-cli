# Taskwarrior Expert Skill

Complete guide for the taskwarrior-expert skill - a structured workflow system for managing tasks, initiatives, and session context using Taskwarrior.

## 📍 Script Locations (IMPORTANT)

**When this skill is activated in UNHINGED mode, scripts are located at:**

```
~/.gemini/skills/taskwarrior_expert/scripts/
```

**Available scripts:**
- `~/.gemini/skills/taskwarrior_expert/scripts/tw-flow` - Main workflow tool (v1.4.0)
- `~/.gemini/skills/taskwarrior_expert/scripts/taskp` - Project-aware wrapper
- `~/.gemini/skills/taskwarrior_expert/scripts/ponder` - Dashboard visualization (v1.4.0)

**How to use them:**

```bash
# Option 1: Direct path (always works)
~/.gemini/skills/taskwarrior_expert/scripts/tw-flow initiative my-feature "task|tag|due"

# Option 2: If scripts are in PATH (after configure-direct)
tw-flow initiative my-feature "task|tag|due"
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
ponder
```
Shows initiative landscape, active tasks, and tactical readout.

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
Types: `research` (r), `decision` (d), `blocked` (b), `lesson` (l), `ac` (a), `note` (n), `link`.

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
Shows initiative status with a **split view**:
- **PENDING:** Tasks remaining in the initiative.
- **COMPLETED:** History of what has already been done.
*Auto-detects active initiative if no argument provided.*

### tw-flow tree
Visualizes dependencies in an ASCII tree:
```
 Initiative: my-feature ══
 ✓ (ae749be5) | Design phase
   ├── ⚡ (4facb768) | Implementation
   └── 🔒 (0e7ab763) | Testing (Blocked)
```

### tw-flow discard
Soft delete a task by moving it to an `_archive` project and marking it done.

---

## 💡 Best Practices

1. **Use UUIDs:** Always refer to tasks by their 8-character UUID.
2. **One Active Task:** Avoid having multiple active tasks in the same initiative to maintain focus and urgency accuracy.
3. **Structured Notes:** Use prefixes (`RESEARCH:`, `DECISION:`) to make context retrieval easy for future agents.
4. **Never Bypass Abstractions:** Bypassing `taskp` to use `task` directly breaks project isolation and data integrity.

---

**Version:** 1.4.0  
**Last Updated:** 2026-02-21
