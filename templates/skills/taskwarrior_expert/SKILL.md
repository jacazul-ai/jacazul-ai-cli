---
name: taskwarrior-expert
description: Expert system for managing session plans, tasks, and context using Taskwarrior. Use this when managing tasks, creating plans, tracking progress, or storing session context.
license: MIT
---

# Instructions

# Taskwarrior Integration Protocol

## Environment Configuration

### Per-Project Database Architecture (v1.4.0)

**NEW:** Taskwarrior now uses **isolated databases per project** for better organization, performance, and isolation.

### PROJECT_ID Variable
The `PROJECT_ID` environment variable is automatically set by the copilot script:

```bash
PROJECT_ID="${PARENT_DIR}_${CURRENT_DIR}"
```

Example: Running from `/home/user/ai_cli_sandboxed/` → `PROJECT_ID=user_ai_cli_sandboxed`

### Database Structure

Each project has its own Taskwarrior database:

```
~/.task/
  ├── piraz_ai_cli_sandboxed/    # Project-specific database
  │   ├── pending.data
  │   ├── completed.data
  │   └── backlog.data
  └── other_project/              # Another project
      └── ...
```

### Project-Aware Tools

Three main tools automatically detect and use the correct project database:

1. **taskp** - Project-aware wrapper (auto-detects via PROJECT_ID)
2. **tw-flow** (v1.4.0) - Workflow management with TASKDATA support
3. **ponder** - Dashboard with per-project views

All automatically set `TASKDATA=~/.task/$PROJECT_ID` when PROJECT_ID is available.

### Task Organization Pattern

Within each project database, organize work by **initiatives** using simple task descriptions:

**Key Concept:** Tasks are isolated by **separate databases** (`TASKDATA`). Each project has its own database, so no prefixes or special attributes needed.

```bash
# ✅ CORRECT - Simple descriptions, database handles isolation
taskp add "Implement user auth" urgency:9.0
taskp add "Design API endpoint" urgency:8.5
taskp add "Write tests for auth flow" urgency:7.2

# ✅ View all tasks (automatically filtered by PROJECT_ID via TASKDATA)
taskp list
taskp status:pending

# ✅ Using tw-flow for multi-task planning
tw-flow plan "login-feature" \
  "Design auth flow|research|today" \
  "Implement JWT tokens|code|tomorrow"
```

**Why this works:**
- `taskp` automatically uses `TASKDATA=~/.task/$PROJECT_ID`
- Each project has its own isolated database
- Tasks from different projects NEVER mix
- Use simple, clear descriptions - the database keeps everything separate

**What NOT to do:**
- ❌ Don't use `project:` attribute (unnecessary, causes confusion)
- ❌ Don't prefix with `$PROJECT_ID:` (database isolation handles this)
- ❌ Don't overthink it - just add tasks with clear descriptions

**Migration Note:** If you see old examples with `$PROJECT_ID:initiative` or `project:` patterns, ignore them - that was before per-project databases (pre-v1.4.0).
## 🔑 UUID Display Protocol

**CRITICAL: Always use short UUIDs (8 chars) when referring to tasks to users.**

- **NEVER** show numeric task IDs to users
- **ALWAYS** display short UUIDs (first 8 characters)
- Both `ponder` and `tw-flow status` already show UUIDs correctly
- When using `taskp` output, extract UUID with: `taskp <ID> | grep UUID | awk '{print substr($2,1,8)}'`

**Display format:** `fa145ef2 - Task description [urgency]`

**Why UUIDs?**
- IDs are session-specific and change across database rebuilds
- UUIDs are permanent and globally unique
- Better for documentation, handoffs, and long-term tracking

## 🌐 Language Protocol (CRITICAL for Agents)

**Response Language:** Match user's language exactly
- User speaks Portuguese → Respond in Portuguese
- User speaks English → Respond in English
- User code-switches → Match their switching pattern

**Data Language:** ALL data stored in English
- Task descriptions: English only
- Annotations: English only
- Tags: English only
- Commits: English only
- Everything persisted in data → English

**Examples:**
```
User (PT-BR): "segura aí, que coisa é essa em enforce-outcome?"
Your response: Portuguese explanation + data shown in English
Task annotation: "Reviewed enforce-outcome requirement - needs outcome validation"

User (EN): "What's blocking the auth-system initiative?"
Your response: English explanation
Task annotation: "Blocking issue identified - dependency on crypto-lib v3.2"
```

**Jacazul Example:**
- User: "meu quiridu, faz isso aí" (Portuguese)
- Jacazul: Responds in Portuguese, creates task in English


## 🌟 Philosophy

**"Plan effectively, execute efficiently, and never lose context."**

## 🚦 Interaction Modes

Modes define the **Agent's Behavior** for a given task. Explicitly setting a mode controls the level of autonomy and the type of output.

| Mode | Behavior | Autonomy | Output |
| :--- | :--- | :--- | :--- |
| **`[PLAN]`** | Requirements analysis & breakdown. | Low | A structured plan (Task list). |
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

### Phase 1: Orient (Ponder)
Before acting, understand the state of the world.
```bash
# With PROJECT_ID - shows project-specific database
PROJECT_ID=your_project ponder "$PROJECT_ID"

# Or using the default global database
ponder
```

This shows your active, ready, and blocked tasks, excluding `_archive` projects.

**Key:** Ponder now respects `PROJECT_ID` environment variable for multi-project isolation via the taskp wrapper.

### Phase 2: Plan (Decide)
Break down a goal into a dependency chain.
```bash
tw-flow plan my-feature-x \
  "PLAN|Design API schema|research|today" \
  "EXECUTE|Implement endpoints|implementation|tomorrow"
```

### Phase 3: Execute (Act)
Pick the top task and work.
```bash
tw-flow execute <id>
```

### Phase 4: Context (Record)
Document your work as you go.
```bash
tw-flow note <id> decision "Using library Y."
```

### Phase 5: Review (Verify)
**CRITICAL:** Never close a task silently.
1.  Summarize the work.
2.  Show the result (code, file, output).
3.  Ask: "Shall I close this?"

### Phase 6: Outcome (Capture)
Upon user approval ("looks good", "yes"), you **MUST** record the final result.
```bash
tw-flow outcome <id> "Created file X and updated Y."
```
This ensures the `task log` contains a permanent record of *what* was achieved.

### Phase 7: Close (Finalize)
Only after recording the outcome.
```bash
tw-flow done <id>
```

## 🤝 Session Handoff

To ensure continuity between sessions (or agents), use this protocol when wrapping up:

1.  **Close:** Ensure the current task is `done` with a clear outcome.
2.  **Anchor:** Explicitly `execute` the *next* logical task.
3.  **Bridge:** Add a specific note to the *newly started* task pointing to the context.

```bash
tw-flow handoff <next_id> "Pick up here. See Task <prev_id> for investigation details."
```

---

## 🗄 Archiving Unplanned Tasks

Sometimes, you'll find legacy tasks that don't fit the current plan. These are "unplanned" or "unscoped".

**Protocol:** Move them to the `_archive` project to hide them from the main view.

```bash
# Example
task <legacy_id> modify <current_project>:_archive
```

The `ponder` dashboard is configured to automatically ignore any project ending in `_archive`, keeping your view clean and focused.

---

## 🛠 Core Tools

- **`ponder`**: High-level project dashboard with PROJECT_ID isolation support
- **`tw-flow`**: Simplified task management workflow

Refer to the script headers for detailed usage.

---

**Always use Taskwarrior for session plans and task breakdowns. Do not create or persist plans in files unless absolutely necessary.**

## Purpose
Use Taskwarrior as a context cache for plans, tasks, research findings, and lessons learned. This ensures continuity and progress tracking between sessions.

## Naming Convention
Tasks follow the pattern: `project_id:initiative_id:task_name`
- **project_id**: Identifies the broader project or session
- **initiative_id**: Identifies the specific plan or feature being worked on
- **task_name**: Short description of the specific task

Example: `copilot-session:auth-system:implement-login`

## 🚀 Quick Start Guide (For Simple Models)

### Step 1: Create a Plan with Tasks

**ALWAYS follow this pattern when creating a new plan:**

```bash
# Step 1: Add first task (highest urgency + earliest due date)
task add copilot:PLAN_NAME "First task to do" due:today urgency:9.0 +research

# Step 2: Add second task (depends on first, due tomorrow)
task add copilot:PLAN_NAME "Second task to do" due:tomorrow depends:FIRST_UUID urgency:7.0 +implementation

# Step 3: Add third task (depends on second, due in 2 days)
task add copilot:PLAN_NAME "Third task to do" due:2days depends:SECOND_UUID urgency:5.0 +testing
```

**Real Example:**
```bash
# Creating a login feature plan
task add copilot:login-feature "Design authentication flow" due:today urgency:9.0 +research
# Returns: Created task fa145ef2

task add copilot:login-feature "Implement JWT tokens" due:tomorrow depends:fa145ef2 urgency:7.0 +implementation
# Returns: Created task 8db30af7

task add copilot:login-feature "Write integration tests" due:2days depends:8db30af7 urgency:5.0 +testing
# Returns: Created task b3c7d891
```

### Step 2: See What to Work On

```bash
# Show all tasks ready to work (no blockers)
task status:pending ready

# Show tasks for specific plan
task copilot:login-feature status:pending

# Show what you're currently working on
task +ACTIVE
```

### Step 3: Start Working on a Task

```bash
# When you start working, use 'start' command
taskp fa145ef2 start

# This tracks time and increases urgency automatically
```

### Step 4: Add Context/Notes to Task

```bash
# Use annotations with prefixes for organized context
taskp fa145ef2 annotate "RESEARCH: Found passport.js library - supports OAuth"
taskp fa145ef2 annotate "DECISION: Using JWT with 15min expiry for access tokens"
taskp fa145ef2 annotate "LINK: https://github.com/jaredhanson/passport"
```

### Step 5: Complete a Task

```bash
# When task is done
taskp fa145ef2 done

# This automatically unblocks the next task!
# Task 43 will lose the BLOCKED status and become ready to work
```

### Step 6: Check Progress

```bash
# See what's completed today
task end:today status:completed

# See what's overdue (needs attention!)
task due.before:today status:pending

# See all blocked tasks
task +BLOCKED
```

## Core Workflow

### 1. Task Creation - DETAILED

When starting work on a plan or feature, **ALWAYS use this formula:**

```bash
task add PROJECT:PLAN "Description" due:DATE urgency:NUMBER +tag depends:UUID
```

**Each part explained:**
- `PROJECT:PLAN` - Groups tasks together (e.g., copilot:auth-feature)
- `"Description"` - What to do (start with verb: Design, Implement, Test, etc.)
- `due:DATE` - Deadline (today, tomorrow, friday, eow, 3days, etc.)
- `urgency:NUMBER` - Manual priority (9.0 = highest, 1.0 = lowest)
- `+tag` - Category (+research, +implementation, +testing, +documentation)
- `depends:UUID` - Blocks this task until task ID is done

**Priority System (USE THIS):**
- First task in plan: `urgency:9.0 due:today` (work on this NOW)
- Second task: `urgency:7.0 due:tomorrow depends:FIRST_UUID` (blocked until first is done)
- Third task: `urgency:5.0 due:2days depends:SECOND_UUID` (blocked until second is done)
- Fourth task: `urgency:3.0 due:3days depends:THIRD_UUID` (blocked until third is done)

**Due Date System:**
- Use natural language: `today`, `tomorrow`, `friday`, `eow` (end of week), `eom` (end of month)
- Or relative: `2days`, `3days`, `1week`, `2weeks`
- Tasks due sooner automatically get higher urgency

**Dependencies System:**
- `depends:UUID` makes current task BLOCKED until task ID is completed
- When you do `task ID done`, ALL tasks depending on it become UNBLOCKED automatically
- Use dependencies for tasks that CANNOT start before another finishes

**Example with ALL elements:**
```bash
# Plan: Build API endpoint
task add copilot:api-endpoint "Design API schema" due:today urgency:9.0 +research
# Created task c9e2f4a3

task add copilot:api-endpoint "Implement POST endpoint" due:tomorrow urgency:7.0 +implementation depends:c9e2f4a3
# Created task 7dc51db6 (BLOCKED until 10 is done)

task add copilot:api-endpoint "Add validation middleware" due:2days urgency:5.0 +implementation depends:7dc51db6
# Created task f29672dd (BLOCKED until 11 is done)

task add copilot:api-endpoint "Write unit tests" due:3days urgency:3.0 +testing depends:f29672dd
# Created task a4b8e1c5 (BLOCKED until 12 is done)
```

**Tags to use:**
- Use custom numerical urgencies (e.g., 9.0, 7.0, 5.0, 3.0, 1.0) to precisely weight and sequence tasks
- Adjust urgencies dynamically based on conversation - if user says "taskp c9e2f4a3 is more important", increase its urgency value
- Add relevant tags for filtering: +research, +implementation, +testing, +review, +documentation, +bug, +urgent, +blocked, +waiting
- Set dependencies with `depends:UUID` to block tasks until prerequisites are done

### 2. Adding Context with Annotations - DETAILED

**ALWAYS use prefixes** to organize annotations by type:

```bash
# Research findings (what you discovered)
taskp fa145ef2 annotate "RESEARCH: Found X library that does Y"

# Decisions made (why you chose something)
taskp fa145ef2 annotate "DECISION: Chose approach A over B because of performance"

# Blockers (what's stopping progress)
taskp fa145ef2 annotate "BLOCKED: Waiting for PR #123 to merge"

# Lessons learned (gotchas, tips)
taskp fa145ef2 annotate "LESSON: Always test edge cases early"

# Acceptance criteria (what "done" means)
taskp fa145ef2 annotate "AC: Must handle 1000+ concurrent users"

# Notes (general observations)
taskp fa145ef2 annotate "NOTE: Customer prefers dark mode"

# Links (references)
taskp fa145ef2 annotate "LINK: https://docs.example.com/api"
```

**Example - Complete research task with annotations:**
```bash
taskp fa145ef2 start
taskp fa145ef2 annotate "RESEARCH: Evaluated 3 auth libraries: passport.js, jsonwebtoken, auth0"
taskp fa145ef2 annotate "DECISION: Using passport.js - most flexible for multi-strategy"
taskp fa145ef2 annotate "LINK: https://github.com/jaredhanson/passport"
taskp fa145ef2 annotate "AC: Must support OAuth, SAML, and local authentication"
taskp fa145ef2 done
```

Annotations are timestamped and append to the task, building a context history.

### 3. Task Organization - DETAILED

**Urgency (Priority Ordering):**
- Use numerical values for fine-grained control: 9.0 (highest) to 1.0 (lowest)
- First task in plan gets 9.0, second gets 7.0, third gets 5.0, etc.
- Adjust dynamically based on user feedback: if user says "task X is more important", increase its urgency

```bash
# Make task highest priority
taskp fa145ef2 modify urgency:10.0

# Lower priority
taskp fa145ef2 modify urgency:2.0

# Remove manual urgency (use automatic calculation)
taskp fa145ef2 modify urgency:
```

**Dependencies (Task Blocking):**
- Use `depends:UUID` to block a task until another is completed
- When prerequisite is done, dependent task automatically becomes UNBLOCKED

```bash
# Task 2 cannot start until taskp c9e2f4a3 is done
taskp 7dc51db6 modify depends:1

# Task 3 depends on both 1 and 2
taskp f29672dd modify depends:c9e2f4a3,7dc51db6

# Remove dependency
taskp 7dc51db6 modify depends:
```

**Tags (Categorization):**
- Organize by type and status for easy filtering

```bash
# Type tags
+research          # Research/investigation work
+implementation    # Coding/building
+testing           # Writing tests
+review            # Code review
+documentation     # Docs writing
+bug               # Bug fixes

# Status tags
+urgent            # Needs immediate attention
+blocked           # Cannot proceed (external blocker)
+waiting           # Waiting for something
+next              # Should do next

# Add/remove tags
taskp fa145ef2 modify +urgent +blocked
taskp fa145ef2 modify -blocked
```

**Status (Task Lifecycle):**
```bash
# Start working (tracks time, increases urgency)
taskp fa145ef2 start

# Stop tracking time
taskp fa145ef2 stop

# Mark complete (unblocks dependent tasks!)
taskp fa145ef2 done

# Delete task (removes from plan)
taskp fa145ef2 delete

# Put task on hold until specific date
taskp fa145ef2 modify wait:friday
```

### 4. Session Management - DETAILED

**Viewing Tasks:**

```bash
# Show all pending tasks for a plan (most common)
task copilot:PLAN_NAME status:pending

# Show tasks ready to work (no blockers, highest urgency first)
task status:pending ready

# Show tasks ready for specific plan
task copilot:PLAN_NAME status:pending ready

# Show what you're actively working on
task +ACTIVE

# Show blocked tasks (waiting on dependencies)
task +BLOCKED

# Show completed tasks today
task end:today status:completed

# Show overdue tasks (needs attention!)
task due.before:today status:pending

# Get full details of a specific task (shows annotations, dependencies, etc.)
taskp fa145ef2 info
```

**Task Listing Protocol:**
When listing tasks for user, **ALWAYS show in this format:**

```
Plan: copilot:feature-name
1. fa145ef2 - Design API schema [9.0] 🟢 ACTIVE
2. b3c7d891 - Implement endpoints [7.0] 🔒 BLOCKED (depends: 42)
3. c9e2f4a3 - Write tests [5.0] 🔒 BLOCKED (depends: 43)
```

Format explanation:
- Task number (1, 2, 3...) - Sequential order
- Short UUID (8 chars) - Unique task identifier for commands
- Description - What to do
- [Urgency] - Priority score in brackets
- Status indicators:
  - 🟢 ACTIVE - Currently being worked on
  - 🔒 BLOCKED - Waiting on dependency
  - ⏸️ WAITING - Waiting for external event
  - ✅ READY - Can start now

**When to update urgencies:**
- When a task is completed, the next task automatically becomes highest priority (due to dependencies)
- If user says "task X is more important", increase its urgency: `task X modify urgency:10.0`
- Always ensure task numbers and urgencies reflect the intended execution order

**Focusing on a specific plan:**
When user says "let's work on plan X", filter all subsequent task operations to that plan:

```bash
# User: "Let's work on the auth feature"
# You should use: task copilot:auth-feature status:pending

# All subsequent commands focus on that plan
task copilot:auth-feature +ACTIVE
task copilot:auth-feature +BLOCKED
```

### 5. Retrieving Context - DETAILED

**View tasks for current work:**

```bash
# See all pending tasks in a plan
task copilot:PLAN_NAME status:pending

# Get FULL details of a specific task (annotations, dependencies, dates, etc.)
taskp fa145ef2 info

# This shows:
# - Description
# - Project
# - Status
# - Dependencies (what it's blocked by)
# - Due date
# - Urgency score
# - All annotations with timestamps
# - When it was created, started, completed
```

**Example output of `taskp fa145ef2 info`:**
```
Name          Design authentication flow
ID            42
Project       copilot:login-feature
Status        Completed
Entered       2026-01-27 10:00:00 (1 hour)
Start         2026-01-27 10:30:00 (30 mins)
End           2026-01-27 11:00:00 (now)
Due           2026-01-27
Urgency       9.0

Annotations:
  2026-01-27 RESEARCH: Found passport.js library - supports OAuth
  2026-01-27 DECISION: Using JWT with 15min expiry for access tokens
  2026-01-27 LINK: https://github.com/jaredhanson/passport
```

### 6. Task Updates - DETAILED

**Complete workflow example:**

```bash
# 1. Check what's ready to work on
task status:pending ready
# Shows: Task 42 "Design API schema"

# 2. Start working (tracks time)
taskp fa145ef2 start
# Task is now marked as ACTIVE

# 3. Add context while working
taskp fa145ef2 annotate "RESEARCH: Evaluated 3 options: REST, GraphQL, gRPC"
taskp fa145ef2 annotate "DECISION: Using REST for simplicity"

# 4. Complete the task
taskp fa145ef2 done
# Task 43 (which depends on 42) is now UNBLOCKED automatically!

# 5. Check what's next
task status:pending ready
# Shows: Task 43 "Implement endpoints" (no longer blocked!)
```

**Common operations:**

```bash
# Mark progress - start tracking time
taskp fa145ef2 start

# Stop tracking time (task remains pending)
taskp fa145ef2 stop

# Complete task (unblocks dependent tasks!)
taskp fa145ef2 done

# Change urgency (make more/less important)
taskp fa145ef2 modify urgency:10.0

# Add dependency (block this task)
taskp fa145ef2 modify depends:2a9f7e3b

# Remove dependency (unblock this task)
taskp fa145ef2 modify depends:

# Change due date
taskp fa145ef2 modify due:tomorrow

# Add tag
taskp fa145ef2 modify +urgent

# Put on hold until date
taskp fa145ef2 modify wait:friday
```

**Adding subtasks:**
If you need to break a task into smaller pieces:

```bash
# Original task
taskp fa145ef2 "Implement API endpoints"

# Break it down
task add copilot:api "Implement POST /users" depends:2a9f7e3b urgency:6.5 +implementation
task add copilot:api "Implement GET /users/:id" depends:2a9f7e3b urgency:6.3 +implementation
task add copilot:api "Implement PUT /users/:id" depends:2a9f7e3b urgency:6.1 +implementation

# These all depend on task 2a9f7e3b (design) and must be done before task 8db30af7 (tests)
task 8db30af7 modify depends:fa145ef2,6c3e9a1d,8f1d4b7e,4b9e2a5c
```

## Practical Examples - COMPLETE WORKFLOWS

### Example 1: Simple 3-Task Plan

**Scenario:** User wants to implement a login feature

```bash
# Step 1: Create the plan with 3 tasks
task add copilot:login "Design authentication flow" due:today urgency:9.0 +research
# Created task c9e2f4a3

task add copilot:login "Implement JWT authentication" due:tomorrow urgency:7.0 +implementation depends:c9e2f4a3
# Created task 7dc51db6 (BLOCKED by task 10)

task add copilot:login "Write integration tests" due:2days urgency:5.0 +testing depends:7dc51db6
# Created task f29672dd (BLOCKED by task 11)

# Step 2: Work on first task
task c9e2f4a3 start
task c9e2f4a3 annotate "RESEARCH: Comparing passport.js vs auth0"
task c9e2f4a3 annotate "DECISION: Using passport.js for flexibility"
task c9e2f4a3 annotate "AC: Must support OAuth and local auth"
task c9e2f4a3 done
# Task 11 is now UNBLOCKED!

# Step 3: Work on second task
task 7dc51db6 start
task 7dc51db6 annotate "IMPLEMENTATION: Using jsonwebtoken library"
task 7dc51db6 annotate "NOTE: Access tokens expire in 15 minutes"
task 7dc51db6 done
# Task 12 is now UNBLOCKED!

# Step 4: Work on third task
task f29672dd start
task f29672dd annotate "TESTING: Covering success and failure cases"
task f29672dd done
# Plan complete! ✅
```

### Example 2: Plan with Parallel Tasks

**Scenario:** Some tasks can be done in parallel

```bash
# Design must be done first
task add copilot:dashboard "Design dashboard layout" due:today urgency:9.0 +research
# Created task d1f3a7b2

# These 3 can be done in parallel (all depend only on design)
task add copilot:dashboard "Implement user stats widget" due:tomorrow urgency:7.0 +implementation depends:d1f3a7b2
# Created task e5c9f2a8

task add copilot:dashboard "Implement activity feed widget" due:tomorrow urgency:7.0 +implementation depends:d1f3a7b2
# Created task 6b4d8e1a

task add copilot:dashboard "Implement notifications widget" due:tomorrow urgency:7.0 +implementation depends:d1f3a7b2
# Created task 9a2c5f7b

# Integration depends on all 3 widgets
task add copilot:dashboard "Integrate all widgets" due:3days urgency:5.0 +implementation depends:e5c9f2a8,22,23
# Created task 1f8e4b3c (BLOCKED by 21, 22, AND 23)

# When task d1f3a7b2 is done, tasks 21, 22, 23 all become ready simultaneously!
task d1f3a7b2 done

# You can work on 21, 22, 23 in any order
# Task 24 only becomes ready when ALL THREE are done
```

### Example 3: Urgent Bug Fix

**Scenario:** Production bug interrupts current work

```bash
# Current plan tasks exist with urgency 9.0, 7.0, 5.0...

# Add urgent bug fix (higher urgency than everything else!)
task add copilot:hotfix "Fix login crash on Safari" due:today urgency:15.0 +bug +urgent priority:H
# Created task 3d7a9e2f

# This task now appears FIRST in ready list because urgency 15.0 > 9.0
task status:pending ready
# Shows task 3d7a9e2f at the top!

# Work on it immediately
task 3d7a9e2f start
task 3d7a9e2f annotate "BUG: Null pointer exception in auth middleware"
task 3d7a9e2f annotate "FIX: Added null check before token validation"
task 3d7a9e2f done

# Now back to regular plan tasks
```

### Example 4: Task Needs to Wait

**Scenario:** Task can't start until next week (waiting for external event)

```bash
# Add task but it can't start yet
task add copilot:deploy "Deploy to production" wait:friday urgency:8.0 +deployment
# Created task 5e1b8c4a

# Task 40 has status:waiting (won't show in pending list)
task status:pending
# Task 40 NOT shown

# On Friday, task automatically becomes status:pending
# Then it shows up in ready list
```

## Productivity Workflows

### Daily Standup
Generate a quick daily standup view:
```bash
# What did I complete yesterday?
task end.after:yesterday end.before:today

# What am I working on today?
task +ACTIVE

# What's due today?
task due:today status:pending

# What's overdue?
task due.before:today status:pending

# What's blocked?
task +BLOCKED
```

### Weekly Review
Comprehensive weekly review process:
```bash
# Completed this week
task end.after:sow status:completed

# Due this week
task due.after:sow due.before:eow status:pending

# New tasks this week
task entry.after:sow

# Tasks by project (JSON export)
task status:pending export | jq 'group_by(.project) | .[] | { .[0].project, count: length}'
```

### Progress Dashboard
Create a progress summary:
```bash
# Overall stats
echo "Pending: $(task status:pending count)"
echo "Completed today: $(task end:today count)"
echo "Completed this week: $(task end.after:sow count)"
echo "Overdue: $(task +OVERDUE count)"
echo "Active: $(task +ACTIVE count)"
echo "Blocked: $(task +BLOCKED count)"
```

### Plan Health Check
Check health of a specific plan:
```bash
# All tasks in plan
task copilot:plan-x status:pending

# Blocked tasks in plan
task copilot:plan-x +BLOCKED

# Tasks without dependencies
task copilot:plan-x depends: status:pending

# Tasks ready to work on (no blockers)
task copilot:plan-x status:pending ready

# Average urgency of plan tasks
task copilot:plan-x export | jq '[.[] | .urgency] | add/length'
```

## Best Practices

### Task Naming
- Use clear, actionable descriptions: "Implement user login" not "login stuff"
- Start with verbs: "Design", "Implement", "Test", "Review", "Document"
- Keep descriptions under 50 characters when possible
- Put details in annotations, not in the description

### Project Hierarchy
Use hierarchical project names for organization:
```bash
copilot:auth:login
copilot:auth:signup
copilot:api:endpoints
copilot:api:middleware
```

### Tag Strategy
Develop a consistent tag taxonomy:
- **Type tags**: +research, +implementation, +testing, +documentation, +review
- **Priority tags**: +urgent, +critical, +someday
- **Status tags**: +blocked, +waiting, +next
- **Context tags**: +computer, +online, +phone, +errands

### Annotation Structure
Use prefixes for better context organization:
- `RESEARCH:` - Research findings and discoveries
- `DECISION:` - Architecture and design decisions
- `BLOCKED:` - Blockers and dependencies
- `LESSON:` - Lessons learned and gotchas
- `AC:` - Acceptance criteria
- `NOTE:` - General notes and observations
- `LINK:` - Relevant links and references

### Urgency Tuning
Customize urgency calculation for your workflow:
```bash
# Make due dates more important
task config urgency.due.coefficient 15.0

# Reduce priority influence
task config urgency.priority.coefficient 3.0

# Boost active tasks
task config urgency.active.coefficient 8.0

# Penalize blocked tasks
task config urgency.blocked.coefficient -10.0
```

## Troubleshooting

### Task Not Showing Up
```bash
# Check if task is deleted or completed
taskp fa145ef2 info

# Check all statuses
task status:completed,deleted,waiting <filter>

# Check if task is waiting
task +WAITING
```

### Incorrect Task Order
```bash
# View urgency calculation
taskp fa145ef2 info

# Manually adjust urgency
taskp fa145ef2 modify urgency:9.5

# Reset urgency to auto-calculated
taskp fa145ef2 modify urgency:
```

### Lost Tasks
```bash
# View all tasks (including completed/deleted)
task all

# Search by description
task description.contains:"keyword"

# Search by date range
task entry.after:2026-01-01 entry.before:2026-01-31
```

### Performance Issues
```bash
# Check database status
task diagnostics

# Clean up old completed tasks
task status:completed end.before:6months delete

# Garbage collection
task gc
```

## 🤖 Imperative Script Commands (RECOMMENDED FOR AI AGENTS)

**USE THESE SIMPLIFIED COMMANDS INSTEAD OF RAW TASKWARRIOR!**

A helper script `tw-flow` is located in the skill's scripts directory.

### Location

```bash
# Script location (relative to skill directory)
./scripts/tw-flow

# Usage examples
./scripts/./scripts/tw-flow help
./scripts/./scripts/tw-flow plan copilot:feature "task1|tag|due"
```

### Core Commands

#### 1. Create a Plan

```bash
./scripts/tw-flow plan <plan> <task1> <task2> <task3>...

# Task format: "description|tag|due_offset"
# - description: What to do
# - tag: research, implementation, testing, documentation, review
# - due_offset: today, tomorrow, 2days, friday, eow, eom
```

**Example:**
```bash
./scripts/tw-flow plan copilot:login-feature \
  "Design auth flow|research|today" \
  "Implement JWT|implementation|tomorrow" \
  "Write tests|testing|2days"

# Output:
# ✓ Created task fa145ef2: Design auth flow [urgency: 9.0]
# ✓ Created task 8db30af7: Implement JWT [urgency: 7.0]
# ✓ Created task b3c7d891: Write tests [urgency: 5.0]
# ✓ Plan created with 3 tasks
```

#### 2. See What's Next

```bash
./scripts/tw-flow next [plan]

# Examples:
./scripts/tw-flow next                           # All ready tasks
./scripts/tw-flow next copilot:login-feature     # Ready tasks in specific plan
```

#### 3. Start Working

```bash
./scripts/tw-flow execute <task_id>

# Example:
./scripts/tw-flow execute 42
# ✓ Started working on task 42
```

#### 4. Add Notes/Context

```bash
./scripts/tw-flow note <task_id> <type> <message>

# Types: research, decision, blocked, lesson, ac, note, link
# Or short: r, d, b, l, a, n, link

# Examples:
./scripts/tw-flow note 42 research "Found passport.js library"
./scripts/tw-flow note 42 decision "Using JWT with 15min expiry"
./scripts/tw-flow note 42 link "https://github.com/jaredhanson/passport"
```

#### 5. Complete Task

```bash
./scripts/tw-flow done <task_id> [completion_note]

# Examples:
./scripts/tw-flow done 42
./scripts/tw-flow done 42 "Completed design phase"

# Automatically shows newly unblocked tasks!
```

#### 6. Check Status

```bash
./scripts/tw-flow status [plan]

# Examples:
./scripts/tw-flow status                         # All tasks
./scripts/tw-flow status copilot:login-feature   # Specific plan

# Output:
# ═══ Plan Status ═══
# Completed: 1
# Active: 1
# Blocked: 1
# Pending: 3
```

### Other Useful Commands

```bash
# Pause work on a task
./scripts/tw-flow pause <task_id>

# Show full task context
./scripts/tw-flow context <task_id>

# Show active tasks
./scripts/tw-flow active

# Show blocked tasks
./scripts/tw-flow blocked

# Show overdue tasks
./scripts/tw-flow overdue

# Make task urgent
./scripts/tw-flow urgent <task_id> [urgency]

# Add dependency
./scripts/tw-flow block <task_id> <depends_on_id>

# Remove dependency
./scripts/tw-flow unblock <task_id> <depends_on_id>

# Put task on hold
./scripts/tw-flow wait <task_id> <date>
```

### Complete Workflow Example

```bash
# 1. Create plan
./scripts/tw-flow plan copilot:api-endpoint \
  "Design schema|research|today" \
  "Implement POST|implementation|tomorrow" \
  "Add validation|implementation|2days" \
  "Write tests|testing|3days"

# Output shows task IDs: 10, 11, 12, 13

# 2. Work on first task
./scripts/tw-flow execute 10
./scripts/tw-flow note 10 research "REST API with JSON schema validation"
./scripts/tw-flow note 10 decision "Using express-validator middleware"
./scripts/tw-flow done 10 "Schema designed and documented"

# 3. Task 11 auto-unblocks, work on it
./scripts/tw-flow execute 11
./scripts/tw-flow note 11 implementation "Created /api/users POST endpoint"
./scripts/tw-flow done 11

# 4. Check status
./scripts/tw-flow status copilot:api-endpoint

# 5. Continue with next tasks
./scripts/tw-flow next copilot:api-endpoint
```

### Why Use ./scripts/tw-flow Instead of Raw Taskwarrior?

✅ **Simpler syntax** - No need to remember complex filters
✅ **Automatic dependencies** - `plan` command creates them automatically
✅ **Smart defaults** - Urgency and due dates calculated automatically
✅ **Better feedback** - Shows what got unblocked after completing tasks
✅ **Structured annotations** - Type shortcuts (r, d, b, l, a, n)
✅ **Error checking** - Prevents executing blocked tasks
✅ **Status overview** - Quick dashboard of plan progress

**FOR AI AGENTS: Use ./scripts/tw-flow commands instead of raw taskwarrior commands for simpler, more reliable task management!**

## 🎓 Cheat Sheet for Simple Models

### OPTION 1: Use ./scripts/tw-flow (RECOMMENDED)

```bash
# Create plan
./scripts/tw-flow plan copilot:PLAN "Task 1|research|today" "Task 2|implementation|tomorrow"

# Work on it
./scripts/tw-flow next copilot:PLAN
./scripts/tw-flow execute ID
./scripts/tw-flow note ID research "your note"
./scripts/tw-flow done ID

# Check status
./scripts/tw-flow status copilot:PLAN
```

### OPTION 2: Use Raw Taskwarrior (if ./scripts/tw-flow not available)

#### Creating Tasks - COPY THIS PATTERN

```bash
# First task (highest priority)
task add copilot:PLAN_NAME "Description" due:today urgency:9.0 +TAG

# Second task (depends on first)
task add copilot:PLAN_NAME "Description" due:tomorrow urgency:7.0 +TAG depends:FIRST_UUID

# Third task (depends on second)
task add copilot:PLAN_NAME "Description" due:2days urgency:5.0 +TAG depends:SECOND_UUID
```

### Common Commands - MEMORIZE THESE

```bash
# See what to work on
task status:pending ready

# Start working
task ID start

# Add note
task ID annotate "PREFIX: your note"

# Complete task
task ID done

# See task details
task ID info

# See plan tasks
task copilot:PLAN_NAME status:pending

# See what's overdue
task due.before:today status:pending

# See what's blocked
task +BLOCKED
```

### Urgency Numbers - USE THIS SCALE

```
15.0 = CRITICAL (production bugs)
10.0 = VERY URGENT (must do today)
9.0  = First task in plan
7.0  = Second task in plan
5.0  = Third task in plan
3.0  = Fourth task in plan
1.0  = Low priority (documentation, cleanup)
```

### Due Dates - COMMON VALUES

```
due:today       = Today
due:tomorrow    = Tomorrow
due:friday      = This Friday
due:2days       = In 2 days
due:eow         = End of week
due:eom         = End of month
```

### Tags - STANDARD SET

```
+research        = Research/investigation
+implementation  = Coding
+testing         = Writing tests
+documentation   = Writing docs
+review          = Code review
+bug             = Bug fix
+urgent          = High priority
+blocked         = External blocker
```

### Annotation Prefixes - ALWAYS USE

```
RESEARCH:   = What you found/learned
DECISION:   = Why you chose something
BLOCKED:    = What's stopping progress
LESSON:     = Gotchas/tips
AC:         = Acceptance criteria
NOTE:       = General observation
LINK:       = URL reference
```

### Complete Example - FOLLOW THIS

```bash
# 1. Create plan
task add copilot:feature-x "Design" due:today urgency:9.0 +research
task add copilot:feature-x "Build" due:tomorrow urgency:7.0 +implementation depends:1
task add copilot:feature-x "Test" due:2days urgency:5.0 +testing depends:2

# 2. Work on it
taskp c9e2f4a3 start
taskp c9e2f4a3 annotate "RESEARCH: Found library X"
taskp c9e2f4a3 done

# 3. Next task auto-unblocks
taskp 7dc51db6 start
taskp 7dc51db6 annotate "IMPLEMENTATION: Using approach Y"
taskp 7dc51db6 done

# 4. Final task
taskp f29672dd start
taskp f29672dd annotate "TESTING: All cases pass"
taskp f29672dd done
```

## Session Start
- On session start or when 'onboard' is entered, determine the project id by reading README.md or context/PROJECT.md.
- The project id should be set to the identified project name, normalized (e.g., spaces replaced with underscaces, lowercase).
- Print: Project: <resolved_project_id> to confirm the project in use.
- This project id will be used for all Taskwarrior operations.
- User identification is handled separately after project id is set.
- When starting, optionally show daily standup view to provide immediate context.

## Advanced Features

### Custom Reports
Create tailored views for different workflows:
```bash
# Weekly agenda - all tasks due this week
task due.after:sow due.before:eow status:pending

# Urgent items - high priority tasks
task priority:H status:pending

# Blocked tasks - waiting on dependencies
task +BLOCKED

# Active work - currently started tasks
task +ACTIVE
```

### Recurring Tasks
For repetitive maintenance or review tasks:
```bash
# Weekly code review
task add "Weekly code review" copilot:maintenance due:friday recur:weekly

# Monthly cleanup
task add "Archive old tasks" copilot:maintenance due:eom recur:monthly
```

### Urgency Coefficients
Fine-tune task ordering with custom urgency calculation:
```bash
# Make certain projects more urgent
task config urgency.user.project.copilot.coefficient 5.0

# Boost urgency of specific tags
task config urgency.user.tag.blocked.coefficient -10.0
task config urgency.user.tag.critical.coefficient 15.0
```

### JSON Export and Analysis
Export tasks for dashboards, reports, or integration:
```bash
# Export all pending tasks
task status:pending export

# Export specific plan
task copilot:feature-x export

# Use with jq for analysis
task export | jq '.[] | select(.priority=="H")'
task export | jq 'group_by(.project) | .[] | { .[0].project, count: length}'
```

### Time Tracking
Track time spent on tasks:
```bash
# Start working on a task (tracks start time)
taskp fa145ef2 start

# Stop tracking (records duration)
taskp fa145ef2 stop

# View active tasks with duration
task +ACTIVE
```

### Date Filters
Powerful date-based filtering:
```bash
# Tasks due today
task due:today

# Overdue tasks
task due.before:today status:pending

# Tasks due this week
task due.after:sow due.before:eow

# Tasks due in next 3 days
task due.after:today due.before:3days
```

### Bulk Operations
Modify multiple tasks at once:
```bash
# Add tag to all tasks in a plan
task copilot:plan-x modify +urgent

# Complete all tasks in a category
task +research status:pending done

# Change priority for filtered tasks
task copilot:plan-x priority: modify priority:H
```

### Context Annotations with Metadata
Structure annotations for better context retrieval:
```bash
# Research findings
taskp fa145ef2 annotate "RESEARCH: Found library X - supports feature Y"

# Decision records
taskp fa145ef2 annotate "DECISION: Chose approach A over B because of performance"

# Blockers
taskp fa145ef2 annotate "BLOCKED: Waiting on PR #123 merge"

# Lessons learned
taskp fa145ef2 annotate "LESSON: Testing edge cases earlier saves debugging time"

# Acceptance criteria
taskp fa145ef2 annotate "AC: Must handle 1000+ concurrent users"
```

## Integration Rules
1. **Default to Taskwarrior**: Use tasks instead of creating plan files
2. **Context is additive**: Always use annotations to add context, never replace
3. **Dynamic prioritization**: Adjust task priorities (numerical values) based on user feedback during conversation
4. **Session awareness**: When starting or asked "what are we working on?", list all plans and started tasks
5. **Plan focus**: When user says "let's work on plan X", focus all task operations on that plan
6. **User requests context storage**: When user says "add this to the task" or "save this context", use annotations
7. **Review before work**: Always check `task ... status:pending` before starting to see current state
8. **Use structured annotations**: Prefix annotations with type (RESEARCH, DECISION, BLOCKED, LESSON, AC) for better context retrieval
9. **Time tracking**: Use `start`/`stop` commands when actively working on tasks to track effort
10. **Leverage filters**: Use date filters, status filters, and tag combinations to create powerful views
11. **Export for analysis**: When asked for summaries or progress reports, use JSON export + jq for data extraction
