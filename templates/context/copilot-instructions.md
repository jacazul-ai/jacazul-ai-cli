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

## Git
- Commit messages must follow the Conventional Commits specification
  (https://www.conventionalcommits.org/), using types like feat, fix, chore,
  build, docs, etc.
- The commit message title must be up to 50 characters, and the body lines must
  be wrapped at 72 characters.

# Taskwarrior Integration Protocol

**Always use Taskwarrior for session plans and task breakdowns. Do not create or persist plans in files unless absolutely necessary.**

## Purpose
Use Taskwarrior as a context cache for plans, tasks, research findings, and lessons learned. This ensures continuity and progress tracking between sessions.

## Naming Convention
Tasks follow the pattern: `project_id:plan_id:task_name`
- **project_id**: Identifies the broader project or session
- **plan_id**: Identifies the specific plan or feature being worked on
- **task_name**: Short description of the specific task

Example: `copilot-session:auth-system:implement-login`

## Core Workflow

### 1. Task Creation
When starting work on a plan or feature:
```bash
task add project:project_id:plan_id "task_name" tags:copilot
```
- Use custom numerical urgencies (e.g., 7.9, 5.1, 2.7) to precisely weight and sequence tasks
- Adjust urgencies dynamically based on conversation - if user says "task 1 is more important", increase its urgency value
- Add relevant tags for filtering (copilot, research, implementation, bug, etc.)
- Set dependencies with `depends:task_id` to block tasks

### 2. Adding Context with Annotations
When research is done, context is gathered, or lessons learned:
```bash
task <id> annotate "Research findings: ..."
task <id> annotate "Lesson learned: ..."
task <id> annotate "Acceptance criteria: ..."
```
Annotations are timestamped and append to the task, building a context history.

### 3. Task Organization
- **Urgency**: Use numerical values (7.9, 5.1, 2.7, etc.) for fine-grained control - adjust dynamically based on user feedback
- **Dependencies**: Block tasks with `task <id> modify depends:<other_id>`
- **Tags**: Organize by type (research, implementation, review, testing)
- **Status**: Mark tasks as started (`task <id> start`), done (`task <id> done`), or deleted (`task <id> delete`)

### 4. Session Management
**Task Listing Protocol:**
- Show tasks grouped by plan (`project:plan_id`) when listing tasks.
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
- Show started tasks: `task +ACTIVE`

**Focusing on a specific plan:**
When user says "let's work on plan X", filter all subsequent task operations to that plan's project namespace

### 5. Retrieving Context
View all tasks for current work:
```bash
task project:project_id:plan_id status:pending
task <id> info  # View full task details including annotations
```

### 6. Task Updates
- Mark progress: `task <id> start` (sets start time)
- Complete: `task <id> done` (marks as completed)
- Modify: `task <id> modify urgency:7.9` (change attributes)
- Add subtasks: Create new tasks with dependencies

## Practical Examples

**Starting a new plan:**
```bash
task add project:copilot-session:refactor-auth "Design new auth flow" tags:copilot,research
task modify 1 priority:15
task add project:copilot-session:refactor-auth "Implement JWT tokens" tags:copilot,implementation depends:1
task modify 2 priority:10
```

**Adding research context:**
```bash
task 1 annotate "Found library: passport.js - supports multiple strategies"
task 1 annotate "Security consideration: token expiry should be 15 min for access, 7 days for refresh"
```

**Checking what's next:**
```bash
task project:copilot-session:refactor-auth status:pending ready
```

## Session Start
- On session start or when 'onboard' is entered, determine the project id by reading README.md or context/PROJECT.md.
- The project id should be set to the identified project name, normalized (e.g., spaces replaced with underscores, lowercase).
- Print: Project: <resolved_project_id> to confirm the project in use.
- This project id will be used for all Taskwarrior operations.
- User identification is handled separately after project id is set.

## Integration Rules
1. **Default to Taskwarrior**: Use tasks instead of creating plan files
2. **Context is additive**: Always use annotations to add context, never replace
3. **Dynamic prioritization**: Adjust task priorities (numerical values) based on user feedback during conversation
4. **Session awareness**: When starting or asked "what are we working on?", list all plans and started tasks
5. **Plan focus**: When user says "let's work on plan X", focus all task operations on that plan
6. **User requests context storage**: When user says "add this to the task" or "save this context", use annotations
7. **Review before work**: Always check `task project:... status:pending` before starting to see current state
