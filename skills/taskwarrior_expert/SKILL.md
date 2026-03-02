---
name: taskwarrior-expert
description: Expert system for managing session plans, tasks, and context using Taskwarrior. Use this when managing tasks, creating plans, tracking progress, or storing session context.
license: MIT
---

# Instructions

# Taskwarrior Integration Protocol

## 🏗️ Per-Project Database Architecture (v1.4.0)

Taskwarrior uses **isolated databases per project** for isolation and performance.

### PROJECT_ID Variable
The `PROJECT_ID` environment variable is automatically set by the bootstrap script:
```bash
PROJECT_ID="${PARENT_DIR}_${CURRENT_DIR}"
```

### Database Structure
Each project has its own database at `~/.jacazul-ai/.task/$PROJECT_ID/`.

### Project-Aware Tools
Three main tools automatically detect and use the correct project database:
1. **taskp**: Project-aware wrapper (auto-detects via PROJECT_ID).
2. **tw-flow**: Workflow management with TASKDATA support.
3. **ponder**: Dashboard with per-project views.

All tools set `TASKDATA=~/.jacazul-ai/.task/$PROJECT_ID` automatically.

## 🔑 UUID Display Protocol

**CRITICAL: ALWAYS use short UUIDs (8 chars) when referring to tasks to users.**
- **NEVER** show numeric task IDs to users.
- **ALWAYS** display short UUIDs (first 8 characters).
- Display format: `fa145ef2 - Task description [urgency]`

## 🌐 Language Protocol (Data Consistency)

**Response Language:** Match user's language.
**Data Language:** ALL data stored in English (Task descriptions, Annotations, Tags, Commits).

## 🚦 Interaction Modes

Modes define the **Agent's Behavior** for a given task. Prefix tasks with the mode to enforce behavior.

| Mode | Behavior | Autonomy | Output |
| :--- | :--- | :--- | :--- |
| **`[DESIGN]`** | Requirements analysis & breakdown. | Low | A structured plan. |
| **`[INVESTIGATE]`** | Codebase diving & de-risking. | High (Read-only) | Findings & Context. |
| **`[GUIDE]`** | Navigator. Instructions & diffs only. | **Zero** | Step-by-step guide. |
| **`[EXECUTE]`** | Builder. Implementing changes. | High | Modified files. |
| **`[TEST]`** | Verification & QA. | High | Test results. |
| **`[DEBUG]`** | Root cause analysis. | High (Read-only) | Diagnosis & fix proposal. |
| **`[REVIEW]`** | Code audit & feedback. | Read-only | Suggestions/Critique. |

## 💡 Best Practices

1. **Simple Descriptions:** Use clear descriptions like "Implement user auth" instead of prefixing with project names.
2. **Isolated Silos:** Tasks from different projects NEVER mix. Trust the silo isolation.
3. **Outcome First:** Never close a task without an `OUTCOME` annotation for context propagation.

---

## 🛠️ Core Tools Reference

- **`ponder`**: High-fidelity project dashboard.
- **`tw-flow`**: Standardized task management with context propagation.
- **`taskp`**: **CRITICAL** Project-Aware Taskwarrior Wrapper. Always use `taskp` instead of raw `task`.

## 🚀 Quick Start Guide

### 1. Create an Initiative
```bash
tw-flow initiative feature-x \
  "DESIGN|Design schema|research|today" \
  "EXECUTE|Implement POST|implementation|tomorrow"
```

### 2. Work on a Task
```bash
tw-flow execute <uuid>
tw-flow note <uuid> decision "Using library Y."
tw-flow outcome <uuid> "Result achieved."
tw-flow done <uuid>
```

### 3. Check Status
```bash
ponder          # Horizon View (Global)
tw-flow status  # Hands-on View (Focused)
```
