# Taskwarrior Integration Protocol

## Purpose
Enable Copilot CLI to cache and persist task plans using Taskwarrior, ensuring continuity and progress tracking between sessions.

## Protocol Steps

1. **Task Creation**
   - Each plan or task is added to Taskwarrior as a new task.
   - Use hierarchical project names: `project_id:plan_id` (e.g., `copilot:auth-system`)
   - Add relevant tags: `copilot`, type tags (`research`, `implementation`, `testing`)
   - Task description: Clear, actionable summary (start with verb)
   - Use custom numerical urgency values (7.9, 5.1, 2.7) for precise sequencing

2. **Task Update**
   - Mark progress: `task <id> start` (tracks start time)
   - Complete: `task <id> done` (marks as completed)
   - Modify: `task <id> modify urgency:8.5` (adjust priority)
   - Add context: `task <id> annotate "RESEARCH: ..."`

3. **Task Retrieval**
   - List by plan: `task project:project_id:plan_id status:pending`
   - Get details: `task <id> info` (shows annotations and metadata)
   - View active work: `task +ACTIVE`
   - Check blockers: `task +BLOCKED`

4. **Task Organization**
   - Dependencies: `task <id> modify depends:<other_id>`
   - Tags for filtering: `+urgent`, `+blocked`, `+waiting`, `+next`
   - Date filters: `due:today`, `due.before:eow`, `due.after:today`
   - Priority levels: `priority:H` (High), `priority:M` (Medium), `priority:L` (Low)

## Advanced Features

### Context Annotations
Use structured annotations with prefixes:
```bash
task <id> annotate "RESEARCH: Found library X - supports feature Y"
task <id> annotate "DECISION: Chose approach A over B because performance"
task <id> annotate "BLOCKED: Waiting on PR #123 merge"
task <id> annotate "LESSON: Testing edge cases early saves debugging time"
task <id> annotate "AC: Must handle 1000+ concurrent users"
```

### Date Filters
```bash
# Due today
task due:today status:pending

# Overdue
task due.before:today status:pending

# Due this week
task due.after:sow due.before:eow

# Due in next 3 days
task due.after:today due.before:3days
```

### JSON Export for Analysis
```bash
# Export for dashboards
task status:pending export

# Group by project with jq
task export | jq 'group_by(.project) | .[] | {project: .[0].project, count: length}'

# Filter high priority with jq
task export | jq '.[] | select(.priority=="H")'
```

### Time Tracking
```bash
# Start tracking
task <id> start

# Stop tracking
task <id> stop

# View active with duration
task +ACTIVE
```

### Recurring Tasks
```bash
# Weekly maintenance
task add "Code review" project:copilot:maintenance due:friday recur:weekly

# Monthly cleanup
task add "Archive old tasks" project:copilot:maintenance due:eom recur:monthly
```

## Example Taskwarrior Commands

- Add a task with urgency:
  ```bash
  task add project:copilot:auth "Implement JWT tokens" +implementation urgency:7.9
  ```
- Add dependency:
  ```bash
  task <id> modify depends:<other_id>
  ```
- Structured annotation:
  ```bash
  task <id> annotate "DECISION: Using passport.js for multi-strategy auth"
  ```
- Complete task:
  ```bash
  task <id> done
  ```
- List plan tasks:
  ```bash
  task project:copilot:auth status:pending
  ```
- Check what's next:
  ```bash
  task project:copilot:auth status:pending ready
  ```

## Data Structure
- **Project:** Hierarchical `project_id:plan_id` (e.g., `copilot:auth-system`)
- **Tags:** `copilot`, type tags (`research`, `implementation`, `testing`, `review`)
- **Urgency:** Numerical values (7.9, 5.1, 2.7) for fine-grained sequencing
- **Description:** Clear, actionable task title (start with verb, under 50 chars)
- **Annotations:** Structured context with prefixes (RESEARCH, DECISION, BLOCKED, LESSON, AC)
- **Dependencies:** Use `depends:<id>` to block tasks
- **Due dates:** Use natural language (`today`, `tomorrow`, `eow`, `eom`)

## Usage
- Use this protocol for all session plans and task breakdowns to ensure persistence and retrievability via Taskwarrior.
- Always use structured annotations for context (prefix with RESEARCH, DECISION, BLOCKED, LESSON, AC).
- Use numerical urgency values for precise task sequencing.
- Leverage date filters and JSON export for analysis and dashboards.
- Track time with `start`/`stop` commands when actively working.
