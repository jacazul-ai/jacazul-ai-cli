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


## 🚨 Taskwarrior Scripts

All taskwarrior-expert scripts are located at: `~/.copilot/skills/taskwarrior_expert/scripts/`

Main tools: **tw-flow** (workflow), **taskp** (project-aware wrapper), **ponder** (dashboard)

**ALWAYS use full absolute paths** when invoking scripts. For complete documentation, see the taskwarrior-expert skill.
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

Each project has its own isolated Taskwarrior database:

```
~/.task/
  ├── piraz_ai_cli_sandboxed/     # Database for piraz_ai_cli_sandboxed project
  │   ├── pending.data
  │   ├── completed.data

## Per-Project Taskwarrior Integration

**Database Isolation:** Each project uses an isolated Taskwarrior database at `~/.task/$PROJECT_ID/`

**PROJECT_ID:** Auto-set by copilot script as `${PARENT_DIR}_${CURRENT_DIR}`. Tools (tw-flow, taskp, ponder) automatically detect and route to correct database.

**Task Organization:** Tasks within each database use simple descriptions. Database isolation keeps projects separate—no prefixes needed.

**For complete details:** See taskwarrior-expert skill documentation and `/project/docs/per-project-taskwarrior.md`
- Show tasks grouped by plan (`PROJECT_ID:plan_id`) when listing tasks.
- If a plan is selected, show only tasks for that plan.
- If no plan is selected, show tasks grouped by plan.
- When listing all plans, display each plan with its urgencies and task numbers, ordered by urgency.
- When creating tasks for a plan, assign higher urgency values to earlier steps (e.g., step 1 gets a higher value than step 2) to maintain correct ordering.
- When displaying tasks for a plan, show task numbers on the left, UUIDs in parentheses, and urgency values on the right (e.g., `1. (UUID: fa145ef2) Task description [7.9]`).
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
6. **Status command behavior**: When user asks for status or "what are we doing", use `tw-flow status [initiative]` for focused view (not ponder). Use ponder only for onboard (full project view)
7. **Plan focus**: When user says "let's work on plan X", focus all task operations on that plan
8. **User requests context storage**: When user says "add this to the task" or "save this context", use annotations
9. **Review before work**: Always check `~/.copilot/skills/taskwarrior_expert/scripts/ponder PROJECT_ID` before starting to see current state
10. **Database isolation**: Each project has its own database - tasks are automatically isolated by PROJECT_ID

## Reference Documentation
- **Per-Project Architecture**: See `/project/docs/per-project-taskwarrior.md` for detailed documentation on the database architecture, migration process, and troubleshooting
- **Complete skill guide**: See `/project/docs/taskwarrior-expert.md` for full workflow documentation, interaction modes, and examples
- **Script locations reminder**: See `/project/templates/context/taskwarrior-expert-paths.md` for quick reference on script paths
