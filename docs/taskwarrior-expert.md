# Taskwarrior Expert Skill

Complete guide for the taskwarrior-expert skill - a structured workflow system for managing tasks, plans, and session context using Taskwarrior.

## 🎯 Overview

The taskwarrior-expert skill transforms Taskwarrior into a powerful workflow engine with:
- **7-phase structured workflow** for consistent task execution
- **8 interaction modes** controlling agent autonomy levels
- **Dashboard visualization** for quick state assessment
- **Session continuity** through handoff protocols
- **Context preservation** via structured annotations

## 🚀 Quick Start

### 1. Check Current State
```bash
ponder copilot
```
Shows pulse summary, active task, upcoming work, and blockers.

### 2. Create a Plan
```bash
tw-flow plan copilot:my-feature \
  "PLAN|Design API schema|research|today" \
  "EXECUTE|Implement endpoints|implementation|tomorrow" \
  "TEST|Write tests|testing|2days"
```

### 3. Execute Tasks
```bash
# Start work
tw-flow execute 42

# Add context
tw-flow note 42 research "Found library X supports feature Y"
tw-flow note 42 decision "Using approach A for performance"

# Record outcome and complete
tw-flow outcome 42 "Implemented OAuth flow with JWT tokens"
tw-flow done 42

# Handoff to next
tw-flow handoff 43 "Continue here. See task 42 for design decisions."
```

---

## 📋 The 7-Phase Workflow

### Phase 1: Orient (Ponder)
**Purpose:** Understand the current state before acting.

```bash
ponder [project_root]
```

**Shows:**
- Pulse summary (pending, completed today, overdue, active)
- Current focus (active task)
- Up next (top 3 ready tasks)
- Blocked/waiting tasks

**When to use:** Start of session, before planning, when context switching.

---

### Phase 2: Plan (Decide)
**Purpose:** Break down goals into actionable dependency chains.

```bash
tw-flow plan <project:feature> <tasks...>
```

**Task format:** `"MODE|description|tag|due_offset"`

**Example:**
```bash
tw-flow plan copilot:auth \
  "INVESTIGATE|Review existing auth code|research|today" \
  "PLAN|Design new auth flow|research|today" \
  "EXECUTE|Implement JWT tokens|implementation|tomorrow" \
  "TEST|Write integration tests|testing|2days" \
  "REVIEW|Code review checklist|review|3days"
```

**Best practices:**
- Start with investigation/planning tasks
- Order tasks by logical dependencies (auto-created)
- Use appropriate modes for each task
- Set realistic due dates

---

### Phase 3: Execute (Act)
**Purpose:** Start working on the highest priority ready task.

```bash
tw-flow execute <id>
```

**What happens:**
- Task marked as active (+ACTIVE)
- Start time recorded
- Task details displayed

**Check what's ready:**
```bash
tw-flow next [project:feature]
```

---

### Phase 4: Context (Record)
**Purpose:** Document work as you go for future reference.

```bash
tw-flow note <id> <type> <message>
```

**Note types:**
- `research` - Findings and discoveries
- `decision` - Key decisions made
- `blocked` - Blockers and impediments
- `lesson` - Lessons learned
- `ac` - Acceptance criteria
- `note` - General notes
- `link` - References and URLs

**Example:**
```bash
tw-flow note 42 research "Passport.js supports 500+ authentication strategies"
tw-flow note 42 decision "Using JWT with 15min access tokens, 7d refresh"
tw-flow note 42 link "https://github.com/jaredhanson/passport"
```

---

### Phase 5: Review (Verify)
**Purpose:** NEVER close a task silently. Always show and verify results.

**Protocol:**
1. Summarize what was accomplished
2. Show the result (code, file, output, test results)
3. Ask user: "Shall I close this task?"
4. Wait for approval

**Critical:** Do NOT proceed to Phase 6 without user confirmation.

---

### Phase 6: Outcome (Capture)
**Purpose:** Record final results BEFORE closing for permanent history.

```bash
tw-flow outcome <id> <message>
```

**Example:**
```bash
tw-flow outcome 42 "Implemented OAuth2 login flow with Google/GitHub providers. JWT tokens with 15min expiry."
```

**Best practices:**
- Be specific about what was delivered
- Include key technical details
- Reference created files or endpoints
- Note any important decisions

**Why important:**
- Creates permanent searchable record
- Enables session handoff
- Provides context for future tasks
- Helps in retrospectives

---

### Phase 7: Close (Finalize)
**Purpose:** Mark task complete and check for unblocked work.

```bash
tw-flow done <id> [optional_note]
```

**What happens:**
- Task marked complete
- Dependent tasks unblocked
- Project completion % updated
- Shows newly ready tasks

**Alternative - Handoff to next:**
```bash
tw-flow handoff <next_id> "Pick up here. See task 42 for implementation details."
```

Combines execute + context note for seamless transition.

---

## 🚦 Interaction Modes

Modes define agent behavior and autonomy level. Prefix task descriptions with `[MODE]`.

| Mode | Behavior | Autonomy | Output | Use When |
|------|----------|----------|--------|----------|
| **[PLAN]** | Requirements analysis & breakdown | Low | Structured plan | Need to understand requirements |
| **[INVESTIGATE]** | Codebase diving & de-risking | High (Read-only) | Findings & context | Need to explore unfamiliar code |
| **[GUIDE]** | Navigator - instructions only | **Zero** (Write) | Step-by-step guide | Want manual control |
| **[EXECUTE]** | Builder - implementing changes | High (Write) | Modified files | Ready for implementation |
| **[TEST]** | Verification & QA | High | Test results | Need validation |
| **[DEBUG]** | Root cause analysis | High (Read-only) | Diagnosis & fix | Something broken |
| **[REVIEW]** | Code audit & feedback | Read-only | Suggestions | Need quality check |
| **[PR-REVIEW]** | Prepare/check PR or diffs | Read-only | Summary & readiness | Before merging |

**Examples:**
```bash
# Investigation before implementation
tw-flow plan copilot:refactor \
  "INVESTIGATE|Review current architecture|research|today" \
  "PLAN|Design refactoring approach|research|today" \
  "GUIDE|Create step-by-step plan|documentation|tomorrow" \
  "EXECUTE|Apply refactoring|implementation|2days"

# Debug then fix
tw-flow plan copilot:bug-fix \
  "DEBUG|Diagnose auth failure|research|today" \
  "EXECUTE|Fix identified issue|implementation|today" \
  "TEST|Verify fix with tests|testing|tomorrow"
```

**Choosing the right mode:**
- Unknown codebase? → `[INVESTIGATE]`
- Clear requirements? → `[EXECUTE]`
- Want review first? → `[GUIDE]`
- Need validation? → `[TEST]`
- Something broke? → `[DEBUG]`

---

## 🛠 Tools Reference

### ponder - Dashboard

**Usage:**
```bash
ponder [project_root]
```

**Features:**
- **Pulse Summary:** Pending, completed today, overdue, active counts
- **Current Focus:** Shows active task with mode highlighting
- **Up Next:** Top 3 ready tasks (no blockers)
- **Blocked/Waiting:** Top 3 blocked tasks with dependencies

**Automatically excludes:**
- Projects ending in `_archive`
- Completed tasks
- Waiting tasks (unless in blocked section)

**Color coding:**
- CYAN: Project name, pending count
- GREEN: Completed, up next section
- YELLOW: Modes like [GUIDE], [PLAN]
- BLUE: Active count
- RED: Overdue, blocked section

**When to use:**
- Start of work session
- Before creating new plans
- After completing major tasks
- When context switching between projects

---

### tw-flow - Workflow Commands

Version 1.2.0

#### Planning Commands

**plan** - Create plan with tasks
```bash
tw-flow plan <project:feature> "task1" "task2" ...
```
Format: `"MODE|description|tag|due_offset"`

**plans** - List all active plans
```bash
tw-flow plans
```

**status** - Show plan overview
```bash
tw-flow status [project:feature]
```

#### Execution Commands

**next** - Show ready tasks
```bash
tw-flow next [project:feature]
```

**execute** - Start task
```bash
tw-flow execute <id>
```

**done** - Complete task
```bash
tw-flow done <id> [note]
```

**outcome** - Record result (NEW in 1.2.0)
```bash
tw-flow outcome <id> "What was achieved"
```

**handoff** - Start next with context (NEW in 1.2.0)
```bash
tw-flow handoff <id> "Context for next person/session"
```

**pause** - Pause task
```bash
tw-flow pause <id>
```

#### Context Commands

**note** - Add structured annotation
```bash
tw-flow note <id> <type> "message"
```
Types: research, decision, blocked, lesson, ac, note, link

**context** - Show full task details
```bash
tw-flow context <id>
```

#### Viewing Commands

**active** - Show active tasks
```bash
tw-flow active
```

**blocked** - Show blocked tasks
```bash
tw-flow blocked
```

**overdue** - Show overdue tasks
```bash
tw-flow overdue
```

#### Modification Commands

**urgent** - Mark as urgent
```bash
tw-flow urgent <id> [urgency_value]
```

**block** - Add dependency
```bash
tw-flow block <id> <depends_on_id>
```

**unblock** - Remove dependency
```bash
tw-flow unblock <id> <depends_on_id>
```

**wait** - Put on hold
```bash
tw-flow wait <id> <date>
```

---

## 💡 Best Practices

### Project Naming
Use hierarchical naming with colons:
```
project:subproject:feature
```

Examples:
- `copilot:auth:oauth`
- `copilot:api:endpoints`
- `copilot:docs:taskwarrior`

### Task Descriptions
Format: `[Verb] [Object] [Optional Context]`

Examples:
- `Implement JWT token validation`
- `Refactor database connection pool`
- `Add unit tests for auth module`

### Dependencies
Let `plan` command create dependencies automatically by task order, or add manually:
```bash
tw-flow block 43 42  # Task 43 depends on 42
```

### Priorities
- **H (High):** Current focus, immediate action
- **M (Medium):** Standard operational tasks
- **L (Low):** Backlog, nice-to-have

### Archive Pattern
Hide completed or irrelevant work:
```bash
task 42 modify project:copilot:old-feature:_archive
```

The `ponder` dashboard automatically excludes `_archive` projects.

### Session Handoff Protocol

**When ending a session:**
1. Complete current task with outcome
2. Execute the next logical task
3. Add handoff note with context

```bash
tw-flow outcome 42 "OAuth implementation complete with Google/GitHub"
tw-flow done 42
tw-flow handoff 43 "Implement token refresh. See task 42 for JWT config."
```

**Next session starts with:**
```bash
ponder copilot
tw-flow context 43  # See handoff note
```

---

## 📖 Complete Example

### Scenario: Implement User Authentication

```bash
# 1. Orient - Check state
ponder copilot

# 2. Plan - Break down goal
tw-flow plan copilot:auth \
  "INVESTIGATE|Review current codebase|research|today" \
  "PLAN|Design auth architecture|research|today" \
  "EXECUTE|Implement JWT middleware|implementation|tomorrow" \
  "EXECUTE|Add login/logout endpoints|implementation|tomorrow" \
  "EXECUTE|Implement token refresh|implementation|2days" \
  "TEST|Write integration tests|testing|3days" \
  "REVIEW|Security review checklist|review|4days"

# Plan created: tasks 50-56

# 3. Execute - Start first task
tw-flow execute 50

# 4. Context - Document findings
tw-flow note 50 research "Current auth is basic, no session management"
tw-flow note 50 research "Using Express.js 4.x, no existing auth middleware"
tw-flow note 50 link "https://jwt.io/introduction"

# 5. Review - (Manual) Show findings to user
# User approves moving to design

# 6. Outcome - Record completion
tw-flow outcome 50 "Investigated codebase - no existing auth, Express 4.x ready for middleware"

# 7. Close - Complete and move forward
tw-flow done 50

# Handoff to next task
tw-flow execute 51
tw-flow note 51 decision "Using JWT with access (15min) + refresh (7d) tokens"
tw-flow note 51 decision "Storing refresh tokens in Redis"
tw-flow note 51 ac "Must support Google OAuth and email/password"

# Design complete
tw-flow outcome 51 "Designed JWT-based auth with OAuth2 support and Redis for refresh tokens"
tw-flow done 51

# Continue pattern for remaining tasks...

# Check progress anytime
ponder copilot
tw-flow status copilot:auth
```

---

## 🔧 Troubleshooting

### Task shows as BLOCKED
Check dependencies:
```bash
tw-flow context <id>
```
Complete blocking tasks or remove dependency:
```bash
tw-flow unblock <id> <blocking_id>
```

### Can't find task
List all tasks in project:
```bash
tw-flow status copilot:feature
```

### Task not showing in ponder
- Check if project is correct
- Verify task not in `_archive`
- Ensure task status is pending

### Wrong task order in plan
Dependencies created in sequence. To reorder:
```bash
tw-flow unblock <id> <old_dep>
tw-flow block <id> <new_dep>
```

---

## 📚 Additional Resources

- **Complete skill documentation:** `/project/templates/skills/taskwarrior_expert/SKILL.md`
- **Naming conventions:** `/project/templates/skills/taskwarrior_expert/HIERARCHY.md`
- **Scripts reference:** `/project/templates/skills/taskwarrior_expert/scripts/README.md`
- **Taskwarrior docs:** https://taskwarrior.org/docs/

---

## 🎓 Learning Path

1. **Beginner:** Use `ponder` and `tw-flow next/execute/done`
2. **Intermediate:** Add `outcome` and `note` for context
3. **Advanced:** Use modes, handoffs, and archive patterns
4. **Expert:** Custom workflows with dependencies and priorities

---

**Version:** 1.2.0  
**Last Updated:** 2026-01-31
