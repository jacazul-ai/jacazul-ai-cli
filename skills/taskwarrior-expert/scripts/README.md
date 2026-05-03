# Taskwarrior Expert Scripts

Imperative helper scripts that simplify Taskwarrior usage for AI agents following a structured 7-phase workflow.

## 📦 Scripts Overview

### ponder
High-level dashboard for project overview (Orient phase).
```bash
ponder [project_root]
```

### tw-flow
Simplified task management - Version 1.2.0
```bash
tw-flow <command> [options]
```

### run_smoke.py
Hardened modular smoke test suite (24 logical cases).
```bash
./run_smoke.py
```

---

## 🚀 Quick Reference

### Core Commands

```bash
# Dashboard
ponder copilot

# Planning with modes
tw-flow plan feature "MODE|task|tag|due" ...

# Execution
tw-flow execute <id>
tw-flow outcome <id> "result"          # NEW in 1.2.0
tw-flow done <id>
tw-flow handoff <id> "context"         # NEW in 1.2.0

# Context
tw-flow note <id> <type> "message"

# Viewing
tw-flow plans
tw-flow status [project]
tw-flow next [project]
```

---

## 📋 7-Phase Workflow

```bash
# 1. Orient - Check state
ponder copilot

# 2. Plan - Break down goal
tw-flow plan copilot:feature \
  "PLAN|Design|research|today" \
  "EXECUTE|Build|implementation|tomorrow"

# 3. Execute - Start work
tw-flow execute 42

# 4. Context - Document
tw-flow note 42 decision "Using approach X"

# 5. Review - (Manual) Show work, get approval

# 6. Outcome - Record result
tw-flow outcome 42 "Implemented X with Y"

# 7. Close - Complete
tw-flow done 42
```

---

## 🎯 Interaction Modes

| Mode | Behavior | Autonomy |
|------|----------|----------|
| `[PLAN]` | Analysis | Low |
| `[INVESTIGATE]` | Explore code | High (Read) |
| `[GUIDE]` | Instructions only | Zero (Write) |
| `[EXECUTE]` | Implementation | High (Write) |
| `[TEST]` | Validation | High |

```bash
tw-flow plan copilot:refactor \
  "INVESTIGATE|Review code|research|today" \
  "EXECUTE|Apply changes|implementation|tomorrow"
```

---

## 📝 Note Types

Structured annotations with uppercase prefixes:

```bash
tw-flow note 42 research "Finding X"    # RESEARCH:
tw-flow note 42 decision "Using Y"      # DECISION:
tw-flow note 42 blocked "Needs Z"       # BLOCKED:
tw-flow note 42 lesson "Learned W"      # LESSON:
```

---

## ✅ Testing

All 24 logical cases passing:

```bash
./run_smoke.py
# ✓ Core scripts are executable
# ✓ Help command returns valid usage
# ✓ Initiative workflow (7 phases)
# ✓ UUID Standardization
# ✓ Security Vaccination
# ✓ Anchor system (heap)
# + 18 more...
```

---

## 📚 Dependencies

- bash 4.0+
- taskwarrior 2.6.0+
- jq
- bc

---

## 🎉 Version 1.2.0 (2026-01-31)

**New:**
- `ponder` dashboard
- `outcome` command
- `handoff` command
- Mode support in plans
- 18 tests (was 14)

---

See `../HIERARCHY.md` and `../SKILL.md` for full documentation.

**License:** MIT
