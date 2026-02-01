# Taskwarrior Integration Protocol

## Purpose
Enable Copilot CLI to cache and persist task plans using Taskwarrior, ensuring continuity and progress tracking between sessions.

## Protocol Steps

1. **Task Creation**
   - Each plan or task is added to Taskwarrior as a new task.
   - Use a consistent project name (e.g., `copilot-session`) and tags (e.g., `copilot`, `plan`).
   - Task description includes the plan title and summary.
   - Optionally, store detailed plan content in Taskwarrior annotations.

2. **Task Update**
   - When a task is updated (e.g., completed, modified), update the corresponding Taskwarrior task status and annotations.

3. **Task Retrieval**
   - Retrieve all tasks for the current session/project using Taskwarrior filters (by project/tag).
   - Reconstruct the plan from task descriptions and annotations.

4. **Task Deletion**
   - Remove tasks from Taskwarrior when no longer relevant or upon explicit user request.

## Example Taskwarrior Commands

- Add a task:
  `task add project:copilot-session tag:copilot tag:plan "Implement login feature"`
- Annotate a task:
  `task <id> annotate "Acceptance Criteria: ..."`
- Complete a task:
  `task <id> done`
- List tasks:
  `task project:copilot-session status:pending`

## Data Structure
- **Project:** copilot-session
- **Tags:** copilot, plan
- **Description:** Task/plan title
- **Annotations:** Details, acceptance criteria, etc.

## Usage
- Use this protocol for all session plans and task breakdowns to ensure persistence and retrievability via Taskwarrior.
