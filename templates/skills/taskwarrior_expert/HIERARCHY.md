---
name: jacazul
description: Jacaré Azul (Blue Alligator) - Project navigator and workflow assistant
tools: ["bash", "view", "skill"]
---

# Taskwarrior Hierarchy Best Practices


## 1. Project Naming
Use hierarchical naming to segregate context and allow for broad or narrow filtering.
- **Pattern**: `subfeature` (using colons for Taskwarrior compatibility)
- **Example**: `copilot:taskwarrior-review:implement-ponder`

## 2. Task Descriptions
Descriptions should be actionable and concise. Use annotations for decisions or extended context.
- **Pattern**: `[Action Verb] [Object] [Optional Context]`
- **Examples**:
  - `Add volume mount for Taskwarrior persistence`
  - `Implement JWT token validation`
  - `Refactor database connection pool`

## 3. Dependencies
Use `depends:<id>` to model workflows where one task logically follows another. This keeps the `next` list focused on what is actually actionable.

**Example:**
```bash
# Task 42 must complete before task 43 can start
task 43 modify depends:42
```

## 4. Priority Levels
- **H (High)**: Current focus. Immediate action required.
- **M (Medium)**: Standard operational tasks.
- **L (Low)**: Backlog or "nice to have".

## 5. Annotations
Use annotations to record:
- **Decisions** made during implementation.
- **Goals** and desired outcomes.
- **"Breadcrumbs"** for future sessions.

**Structured annotation types:**
- `RESEARCH:` - Research findings and discoveries
- `DECISION:` - Key decisions made
- `BLOCKED:` - Blockers and impediments
- `LESSON:` - Lessons learned
- `AC:` - Acceptance criteria
- `NOTE:` - General notes
- `LINK:` - References and URLs
- `OUTCOME:` - Final results (before closing)
- `HANDOFF:` - Context for next task/session

**Example:**
```bash
tw-flow note 42 research "Found library X supports feature Y"
tw-flow note 42 decision "Using approach A instead of B for performance"
tw-flow outcome 42 "Implemented OAuth with refresh tokens"
```

## 6. Tags
Use tags to categorize tasks by type or phase:
- `+research` - Investigation and analysis
- `+implementation` - Coding and building
- `+testing` - Test writing and validation
- `+documentation` - Docs and comments
- `+bugfix` - Bug fixes
- `+review` - Code review tasks

## 7. Interaction Modes
Prefix task descriptions with modes to define agent behavior:
- `[PLAN]` - Requirements analysis
- `[INVESTIGATE]` - Codebase exploration
- `[GUIDE]` - Step-by-step instructions only
- `[EXECUTE]` - Implementation with full autonomy
- `[TEST]` - Testing and validation
- `[DEBUG]` - Problem diagnosis
- `[REVIEW]` - Code review
- `[PR-REVIEW]` - Pull request preparation

**Example:**
```bash
tw-flow plan copilot:auth \
  "INVESTIGATE|Review existing auth code|research|today" \
  "EXECUTE|Implement new login flow|implementation|tomorrow"
```

## 8. Archive Pattern
Move completed or irrelevant tasks to `_archive` sub-projects to keep views clean:

```bash
task 42 modify copilot:old-feature:_archive
```

The `ponder` dashboard automatically excludes projects ending with `_archive`.
