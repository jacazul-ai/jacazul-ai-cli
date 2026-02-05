# Taskwarrior Hierarchy Best Practices

## 1. Project Naming
Use hierarchical naming to segregate context and allow for broad or narrow filtering.
- **Pattern**: `project[.subproject][.feature]`
- **Example**: `vi-gemini-sandboxed.infra.taskwarrior`

## 2. Task Descriptions
Descriptions should be actionable and concise. Use annotations for decisions or extended context.
- **Pattern**: `[Action Verb] [Object] [Optional Context]`
- **Example**: `Add volume mount for Taskwarrior persistence`

## 3. Dependencies
Use `depends:<id>` to model workflows where one task logically follows another. This keeps the `next` list focused on what is actually actionable.

## 4. Priority Levels
- **H (High)**: Current focus. Immediate action required.
- **M (Medium)**: Standard operational tasks.
- **L (Low)**: Backlog or "nice to have".

## 5. Annotations
Use annotations to record:
- Decisions made during implementation.
- Goals and desired outcomes.
- "Breadcrumbs" for future sessions.
