# Copilot Global Context

Session context, plans, and all progress are exclusively stored and managed in Taskwarrior, not in files.

## Formatting and Output
- Always generate technical tickets, tasks and project documentation in
  Markdown (.md) format.
- Maintain a consistent structure: Title, Description, Tasks and Acceptance
  Criteria.
- Keep answers short and concise; avoid flattery and unnecessary information.

## Language Handling
- Respond in the same language as the user (language-switch): if addressed in
  Portuguese, reply in Portuguese; if in English, reply in English.
- If the user is chatting in Portuguese and requests code, comments or tickets,
  generate them in English unless explicitly asked for another language.
- All code, comments and tickets must be in English unless otherwise requested.

## Context and Behavior
- If a message ends with 'ack', simply acknowledge and build context.
- When the user is building context, do not provide information unless given
  clear instructions.
- All session plans, tasks, and project documentation must be managed via Taskwarrior.
- Do not create or persist plans in files unless explicitly requested by the user.
- Use Taskwarrior for context storage, progress tracking, and dynamic prioritization.

## Interaction Protocol
- **Show work before execution**: Present a clear plan before starting multi-step work. Break down complex tasks into steps and show them before proceeding.
- **Ask for approval**: Always ask for confirmation before making major changes (file deletion, refactoring, database migrations, wide-reaching modifications). List what will be changed and wait for explicit approval.
- **Work iteratively**: Complete one step, show results, then wait for user feedback before proceeding. Don't implement all steps at once unless explicitly asked. Respect the user's pace.
- **Pause after completion**: After completing a task or step, pause and ask what to do next. Don't jump ahead to the next planned step without user feedback.
- **Use report_intent**: Always call report_intent when starting new work to keep the UI informed of your current activity.

## Behavioral Guidelines
- **Read before modifying**: Always read and understand existing code/files before modifying them. Explore codebase context first.
- **Verify changes**: After making changes, verify they work (run tests, compile, check output). If something fails, stop and report the error instead of continuing.
- **Explain your actions**: Explain what you're doing and why. Report your intent at the start of major actions. Keep the user informed of progress.
- **Respect scope boundaries**: Don't expand scope beyond what was asked. If you notice related issues, mention them but don't fix them unless explicitly requested. Stay focused on the current task.
- **Make minimal changes**: Change as few lines as possible to achieve the goal. Don't refactor or improve code that's not relevant to the task. Use surgical edits.
- **Don't assume success**: Never assume changes worked correctly. Always validate before proceeding. Check command output and test results.

## When to Ask Questions
- **Clarify ambiguous requirements**: If requirements are unclear or ambiguous, ask clarifying questions before proceeding.
- **Confirm behavioral choices**: When multiple valid approaches exist, ask which one the user prefers.
- **Don't assume intent**: Don't make assumptions about business logic, user intent, or edge case handling. Ask if uncertain.
- **Request guidance on decisions**: If you're unsure about scope, approach, or priorities, ask the user before proceeding.

## Git
- Commit messages must follow the Conventional Commits specification
  (https://www.conventionalcommits.org/), using types like feat, fix, chore,
  build, docs, etc.
- The commit message title must be up to 50 characters, and the body lines must
  be wrapped at 72 characters.

# Taskwarrior Integration Protocol

**Always use Taskwarrior for session plans and task breakdowns. Do not create or persist plans in files unless absolutely necessary.**

## 🚨 CRITICAL: Taskwarrior Expert Script Locations

When the `taskwarrior-expert` skill is activated, **ALWAYS use absolute paths** for all scripts:

### Script Locations

All taskwarrior-expert scripts are located at:
```
~/.copilot/skills/taskwarrior_expert/scripts/
```

### Available Scripts

1. **tw-flow** - Main workflow management tool
   - Full path: `~/.copilot/skills/taskwarrior_expert/scripts/tw-flow`
   - Purpose: Plan creation, task execution, context management, session handoffs
   
2. **taskp** - Project-aware Taskwarrior wrapper
   - Full path: `~/.copilot/skills/taskwarrior_expert/scripts/taskp`
   - Purpose: Auto-detects PROJECT_ID and sets correct TASKDATA
   
3. **ponder** - Dashboard visualization
   - Full path: `~/.copilot/skills/taskwarrior_expert/scripts/ponder`
   - Purpose: Quick status overview and pulse check

### Usage Rules for AI Agents

**✅ ALWAYS DO THIS:**
```bash
~/.copilot/skills/taskwarrior_expert/scripts/tw-flow plan copilot:feature "task|tag|due"
~/.copilot/skills/taskwarrior_expert/scripts/ponder copilot
~/.copilot/skills/taskwarrior_expert/scripts/taskp list
```

**❌ NEVER DO THIS:**
```bash
tw-flow plan copilot:feature "task|tag|due"      # Wrong - not in PATH
./scripts/tw-flow plan                            # Wrong - relative path
/project/scripts/tw-flow plan                     # Wrong - wrong location
```

**IMPORTANT:** Do NOT assume these scripts are in PATH or current directory. ALWAYS use the full absolute path starting with `~/.copilot/skills/taskwarrior_expert/scripts/`

### Quick Reference

| Tool | Full Command Path |
|------|-------------------|
| Create plan | `~/.copilot/skills/taskwarrior_expert/scripts/tw-flow plan` |
| Execute task | `~/.copilot/skills/taskwarrior_expert/scripts/tw-flow execute` |
| Add note | `~/.copilot/skills/taskwarrior_expert/scripts/tw-flow note` |
| Record outcome | `~/.copilot/skills/taskwarrior_expert/scripts/tw-flow outcome` |
| Complete task | `~/.copilot/skills/taskwarrior_expert/scripts/tw-flow done` |
| Handoff | `~/.copilot/skills/taskwarrior_expert/scripts/tw-flow handoff` |
| Check status | `~/.copilot/skills/taskwarrior_expert/scripts/tw-flow status` |
| Dashboard | `~/.copilot/skills/taskwarrior_expert/scripts/ponder` |
| Project tasks | `~/.copilot/skills/taskwarrior_expert/scripts/taskp` |

## Purpose
Use Taskwarrior as a context cache for plans, tasks, research findings, and lessons learned. This ensures continuity and progress tracking between sessions.

## Per-Project Database Architecture

**NEW:** Taskwarrior now uses **isolated databases per project** for better organization and performance.

### Project Identity (PROJECT_ID)

The `PROJECT_ID` environment variable is automatically calculated by the copilot script:

```bash
PROJECT_ID="${PARENT_DIR}_${CURRENT_DIR}"
```

Example: Running copilot from `/home/user/ai_cli_sandboxed/` sets `PROJECT_ID=user_ai_cli_sandboxed`

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

### Using Project-Aware Tools

**Three main tools automatically detect and use the correct project database:**

1. **taskp** - Project-aware task wrapper
2. **tw-flow** - Workflow management (v1.3.0+)
3. **ponder** - Dashboard visualization

All automatically use `TASKDATA=~/.task/$PROJECT_ID` when `PROJECT_ID` is set.

### Task Organization Pattern

Tasks follow the pattern: `PROJECT_ID:plan_id:task_name`

```
piraz_ai_cli_sandboxed:onboarding
  ├─ Read README.md
  └─ Initialize project

piraz_ai_cli_sandboxed:auth-system
  ├─ Design schema
  └─ Implement endpoints
```

This ensures proper context isolation across sessions and agents.

## Naming Convention
Tasks follow the pattern: `PROJECT_ID:plan_id:task_name`
- **PROJECT_ID**: Identifies the broader project or session (automatically set)
- **plan_id**: Identifies the specific plan or feature being worked on
- **task_name**: Short description of the specific task

Example: `ai_cli_sandboxed:onboarding:read-readme`


## 🔍 Understanding PROJECT_ID in Commands

When you see `$PROJECT_ID` in command examples, it's an **environment variable** that needs to be expanded:

- **Automatically set** by copilot: `PROJECT_ID="${PARENT_DIR}_${CURRENT_DIR}"`
- **Example values**: `piraz_ai_cli_sandboxed`, `candango_sqlok`, `user_project_name`
- **Always needs quotes** in commands to prevent shell word-splitting


## Core Workflow

### 1. Task Creation
When starting work on a plan or feature, use **project-aware tools**:

```bash
# Using taskp (recommended - auto-detects project)
~/.copilot/skills/taskwarrior_expert/scripts/taskp add "plan_id" "task_name" tags:copilot

# Using tw-flow (recommended for planning)
~/.copilot/skills/taskwarrior_expert/scripts/tw-flow plan "feature" \
  "Design API|research|today" \
  "Implement|implementation|tomorrow"
```

**Note:** All tools (taskp, tw-flow, ponder) automatically use the correct per-project database based on `PROJECT_ID`.

- Use custom numerical urgencies (e.g., 7.9, 5.1, 2.7) to precisely weight and sequence tasks
- Adjust urgencies dynamically based on conversation - if user says "task 1 is more important", increase its urgency value
- Add relevant tags for filtering (copilot, research, implementation, bug, etc.)
- Set dependencies with `depends:task_id` to block tasks

### 2. Adding Context with Annotations
When research is done, context is gathered, or lessons learned:
```bash
~/.copilot/skills/taskwarrior_expert/scripts/taskp <id> annotate "Research findings: ..."
~/.copilot/skills/taskwarrior_expert/scripts/taskp <id> annotate "Lesson learned: ..."
~/.copilot/skills/taskwarrior_expert/scripts/taskp <id> annotate "Acceptance criteria: ..."
```
Annotations are timestamped and append to the task, building a context history.

### 3. Task Organization
- **Urgency**: Use numerical values (7.9, 5.1, 2.7, etc.) for fine-grained control - adjust dynamically based on user feedback
- **Dependencies**: Block tasks with `~/.copilot/skills/taskwarrior_expert/scripts/taskp <id> modify depends:<other_id>`
- **Tags**: Organize by type (research, implementation, review, testing)
- **Status**: Mark tasks as started (`taskp <id> start`), done (`taskp <id> done`), or deleted (`taskp <id> delete`)

### 4. Session Management
**Task Listing Protocol:**
- Show tasks grouped by plan (`PROJECT_ID:plan_id`) when listing tasks.
- If a plan is selected, show only tasks for that plan.
- If no plan is selected, show tasks grouped by plan.
- When listing all plans, display each plan with its urgencies and task numbers, ordered by urgency.
- When creating tasks for a plan, assign higher urgency values to earlier steps (e.g., step 1 gets a higher value than step 2) to maintain correct ordering.
- When displaying tasks for a plan, show task numbers on the left, task IDs in parentheses, and urgency values on the right (e.g., `1. (ID: 42) Task description [7.9]`).
- When a task is completed, update urgencies for remaining tasks in the plan to keep the correct sequence (the next step should always have the highest urgency among remaining tasks).
- When adding a new task to the start, middle, or end of a plan, renumber and re-urgencize all tasks to maintain correct order and urgency sequence.
- When removing a task from the start, middle, or end, renumber and re-urgencize remaining tasks to maintain order.
- When splitting a task into multiple subtasks, insert them in sequence and update numbering and urgencies for all tasks in the plan.
- When moving a task to a different position (e.g., moving step 3 to step 1, or step 1 to the end), renumber and re-urgencize all tasks to reflect the new order.
- Always ensure task numbers and urgencies reflect the intended execution order after any modification.
- Show started tasks: `~/.copilot/skills/taskwarrior_expert/scripts/taskp +ACTIVE`

**Focusing on a specific plan:**
When user says "let's work on plan X", filter all subsequent task operations to that plan's project namespace

### 5. Retrieving Context
View all tasks for current work:
```bash
~/.copilot/skills/taskwarrior_expert/scripts/taskp "plan_id" status:pending
~/.copilot/skills/taskwarrior_expert/scripts/taskp <id> info  # View full task details including annotations
```

### 6. Task Updates
- Mark progress: `~/.copilot/skills/taskwarrior_expert/scripts/taskp <id> start` (sets start time)
- Complete: `~/.copilot/skills/taskwarrior_expert/scripts/taskp <id> done` (marks as completed)
- Modify: `~/.copilot/skills/taskwarrior_expert/scripts/taskp <id> modify urgency:7.9` (change attributes)
- Add subtasks: Create new tasks with dependencies

## Practical Examples

**Starting a new plan with tw-flow:**
```bash
~/.copilot/skills/taskwarrior_expert/scripts/tw-flow plan ai_cli_sandboxed:refactor-auth \
  "Design new auth flow|research|today" \
  "Implement JWT tokens|implementation|tomorrow"
```

**Adding research context:**
```bash
~/.copilot/skills/taskwarrior_expert/scripts/taskp 1 annotate "Found library: passport.js - supports multiple strategies"
~/.copilot/skills/taskwarrior_expert/scripts/taskp 1 annotate "Security consideration: token expiry should be 15 min for access, 7 days for refresh"
```

**Checking what's next:**
```bash
~/.copilot/skills/taskwarrior_expert/scripts/ponder ai_cli_sandboxed
```

**Checking tasks for specific plan:**
```bash
~/.copilot/skills/taskwarrior_expert/scripts/taskp project:ai_cli_sandboxed:refactor-auth status:pending ready
```

- Use `~/.copilot/skills/taskwarrior_expert/scripts/ponder` to show initial dashboard view.

## Integration Rules
1. **Use project-aware tools**: Prefer `taskp`, `tw-flow`, and `ponder` over raw `task` commands
2. **ALWAYS use full paths**: Use `~/.copilot/skills/taskwarrior_expert/scripts/` prefix for all script invocations
3. **Default to Taskwarrior**: Use tasks instead of creating plan files
4. **Context is additive**: Always use annotations to add context, never replace
5. **Dynamic prioritization**: Adjust task priorities (numerical values) based on user feedback during conversation
6. **Session awareness**: When starting or asked "what are we working on?", list all plans and started tasks using `ponder`
7. **Plan focus**: When user says "let's work on plan X", focus all task operations on that plan
8. **User requests context storage**: When user says "add this to the task" or "save this context", use annotations
9. **Review before work**: Always check `~/.copilot/skills/taskwarrior_expert/scripts/ponder PROJECT_ID` before starting to see current state
10. **Database isolation**: Each project has its own database - tasks are automatically isolated by PROJECT_ID

## Reference Documentation
- **Per-Project Architecture**: See `/project/docs/per-project-taskwarrior.md` for detailed documentation on the database architecture, migration process, and troubleshooting
- **Complete skill guide**: See `/project/docs/taskwarrior-expert.md` for full workflow documentation, interaction modes, and examples
- **Script locations reminder**: See `/project/templates/context/taskwarrior-expert-paths.md` for quick reference on script paths
