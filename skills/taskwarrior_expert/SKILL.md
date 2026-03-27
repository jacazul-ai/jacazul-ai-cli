---
name: taskwarrior-expert
description: Expert system for managing session plans, tasks, and context using Taskwarrior. Use this when managing tasks, creating plans, tracking progress, or storing session context.
license: MIT
---

# Instructions

# Taskwarrior Integration Protocol

## 🏗️ Per-Project Database Architecture (v1.6.0)

Taskwarrior uses **isolated databases per project** for isolation and performance.

### PROJECT_ID Variable
The `PROJECT_ID` environment variable is automatically set by the bootstrap script:
```bash
PROJECT_ID="${PARENT_DIR}_${CURRENT_DIR}"
```

### Database Structure
Each project has its own database at `~/.jacazul-ai/.task/$PROJECT_ID/`.

### Project-Aware Tools
Main tools automatically detect and use the correct project database:
1. **taskp**: Project-aware wrapper.
2. **tw-flow**: Workflow management with TASKDATA support.
3. **tw-flow ponder**: Dashboard with per-project views.
   - *Note: The standalone "ponder" command is deprecated and will be removed in a future release.*
4. **jacazul-hatch**: JIT Prompt Forge engine.
5. **jacazul-persona**: Persona switching manager.

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

- **`tw-flow ponder`**: High-fidelity project dashboard.
   - *Note: The standalone "ponder" command is deprecated and will be removed in a future release.*
- **`tw-flow`**: Standardized task management with context propagation.
- **`taskp`**: **CRITICAL** Project-Aware Taskwarrior Wrapper. Always use `taskp` instead of raw `task`.

## 🎯 Independent Focus Mode

Sessions can be isolated from the global `focus.json` using `JACAZUL_SESSION_ID`.

**Commands:**
```bash
tw-flow focus ind plan <name>       # Anchor to plan in independent session
tw-flow focus ind task <uuid>       # Anchor to task in independent session
tw-flow focus ind <plan-name>       # Smart focus in independent mode
tw-flow focus back                  # Exit independent mode, return to global focus
```

**Bootstrap pre-seed (via env vars):**
```bash
JACAZUL_FOCUS_PLAN=my-plan JACAZUL_FOCUS_TASK=<uuid> jacazul-claude
```
The taskwarrior bootstrap will create `focus-{SESSION_ID}.json` automatically.

**Rule:** If `JACAZUL_SESSION_ID` is set, ALL focus reads/writes go to `focus-{SESSION_ID}.json`. The global `focus.json` is never touched by an independent session.

---

## 🚀 Quick Start Guide

### 1. Create a Plan
```bash
tw-flow plan feature-x \
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
tw-flow ponder          # Horizon View (Global)
tw-flow status          # Hands-on View (Focused)
```
