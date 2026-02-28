# Taskwarrior Integration Protocol

## Purpose
Enable Copilot CLI to cache and persist taskp plans using Taskwarrior, ensuring continuity and progress tracking between sessions.

## Protocol Steps

1. **Task Creation**
   - Each plan or taskp is added to Taskwarrior as a new task.
   - Use hierarchical project names: `project_id:plan_id` (e.g., `copilot:auth-system`)
   - Add relevant tags: `copilot`, type tags (`research`, `implementation`, `testing`)
   - Task description: Clear, actionable summary (start with verb)
   - Use custom numerical urgency values (7.9, 5.1, 2.7) for precise sequencing

2. **Task Update**
   - Mark progress: `taskp <id> start` (tracks start time)
   - Complete: `taskp <id> done` (marks as completed)
   - Modify: `taskp <id> modify urgency:8.5` (adjust priority)
   - Add context: `taskp <id> annotate "RESEARCH: ..."`

3. **Task Retrieval**
   - List by plan: `taskp project:project_id:plan_id status:pending`
   - Get details: `taskp <id> info` (shows annotations and metadata)
   - View active work: `taskp +ACTIVE`
   - Check blockers: `taskp +BLOCKED`

4. **Task Organization**
   - Dependencies: `taskp <id> modify depends:<other_id>`
   - Tags for filtering: `+urgent`, `+blocked`, `+waiting`, `+next`
   - Date filters: `due:today`, `due.before:eow`, `due.after:today`
   - Priority levels: `priority:H` (High), `priority:M` (Medium), `priority:L` (Low)

## Advanced Features

### Context Annotations
Use structured annotations with prefixes:
```bash
taskp <id> annotate "RESEARCH: Found library X - supports feature Y"
taskp <id> annotate "DECISION: Chose approach A over B because performance"
taskp <id> annotate "BLOCKED: Waiting on PR #123 merge"
taskp <id> annotate "LESSON: Testing edge cases early saves debugging time"
taskp <id> annotate "AC: Must handle 1000+ concurrent users"
```

### Date Filters
```bash
# Due today
taskp due:today status:pending

# Overdue
taskp due.before:today status:pending

# Due this week
taskp due.after:sow due.before:eow

# Due in next 3 days
taskp due.after:today due.before:3days
```

### JSON Export for Analysis
```bash
# Export for dashboards
taskp status:pending export

# Group by project with jq
taskp export | jq 'group_by(.project) | .[] | {project: .[0].project, count: length}'

# Filter high priority with jq
taskp export | jq '.[] | select(.priority=="H")'
```

### Time Tracking
```bash
# Start tracking
taskp <id> start

# Stop tracking
taskp <id> stop

# View active with duration
taskp +ACTIVE
```

### Recurring Tasks
```bash
# Weekly maintenance
taskp add "Code review" project:copilot:maintenance due:friday recur:weekly

# Monthly cleanup
taskp add "Archive old tasks" project:copilot:maintenance due:eom recur:monthly
```

## Example Taskwarrior Commands

- Add a taskp with urgency:
  ```bash
  taskp add project:copilot:auth "Implement JWT tokens" +implementation urgency:7.9
  ```
- Add dependency:
  ```bash
  taskp <id> modify depends:<other_id>
  ```
- Structured annotation:
  ```bash
  taskp <id> annotate "DECISION: Using passport.js for multi-strategy auth"
  ```
- Complete task:
  ```bash
  taskp <id> done
  ```
- List plan tasks:
  ```bash
  taskp project:copilot:auth status:pending
  ```
- Check what's next:
  ```bash
  taskp project:copilot:auth status:pending ready
  ```

## Data Structure
- **Project:** Hierarchical `project_id:plan_id` (e.g., `copilot:auth-system`)
- **Tags:** `copilot`, type tags (`research`, `implementation`, `testing`, `review`)
- **Urgency:** Numerical values (7.9, 5.1, 2.7) for fine-grained sequencing
- **Description:** Clear, actionable taskp title (start with verb, under 50 chars)
- **Annotations:** Structured context with prefixes (RESEARCH, DECISION, BLOCKED, LESSON, AC)
- **Dependencies:** Use `depends:<id>` to block tasks
- **Due dates:** Use natural language (`today`, `tomorrow`, `eow`, `eom`)

## Usage
- Use this protocol for all session plans and taskp breakdowns to ensure persistence and retrievability via Taskwarrior.
- Always use structured annotations for context (prefix with RESEARCH, DECISION, BLOCKED, LESSON, AC).
- Use numerical urgency values for precise taskp sequencing.
- Leverage date filters and JSON export for analysis and dashboards.
- Track time with `start`/`stop` commands when actively working.
