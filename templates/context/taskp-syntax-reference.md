# Taskp Syntax Reference - Quick Guide

## The Core Issue

The documentation used ambiguous examples like:
```bash
taskp PROJECT_ID:plan_id "task_name"          # ❌ AMBIGUOUS
```

This caused confusion because `PROJECT_ID` is a **shell variable**, not literal text.

## The Solution

Always use **double quotes** around the full project namespace:

```bash
taskp add "$PROJECT_ID:plan_id" "task_name"   # ✅ CORRECT
```

## Why Quotes Matter

Without quotes, the shell treats the colon as a special character and splits the argument:

```bash
# Without quotes - BROKEN
taskp "$PROJECT_ID:plan_id" status:pending
# Shell might interpret this as: taskp "$PROJECT_ID" ":plan_id" "status:pending"
# Result: ERROR ❌

# With quotes - WORKS
taskp "$PROJECT_ID:plan_id" status:pending
# Kept as single argument: taskp "piraz_ai_cli_sandboxed:plan_id" "status:pending"
# Result: SUCCESS ✅
```

## Common Patterns

### Task Creation
```bash
# ✅ CORRECT
taskp add "$PROJECT_ID:initiative" "Task description" due:today urgency:9.0

# ❌ WRONG
taskp add PROJECT_ID:initiative "Task description" due:today urgency:9.0
taskp add $PROJECT_ID:initiative "Task description" due:today urgency:9.0
```

### Task Filtering
```bash
# ✅ CORRECT
taskp "$PROJECT_ID:initiative" status:pending
taskp "$PROJECT_ID:initiative" +ACTIVE

# ❌ WRONG  
taskp PROJECT_ID:initiative status:pending
taskp $PROJECT_ID:initiative status:pending
```

### tw-flow (same rule applies)
```bash
# ✅ CORRECT
tw-flow plan "$PROJECT_ID:feature" "Task 1|tag|today" "Task 2|tag|tomorrow"

# ❌ WRONG
tw-flow plan PROJECT_ID:feature "Task 1|tag|today" "Task 2|tag|tomorrow"
tw-flow plan $PROJECT_ID:feature "Task 1|tag|today" "Task 2|tag|tomorrow"
```

## What PROJECT_ID Actually Is

```bash
# It's set automatically when copilot starts:
PROJECT_ID="${PARENT_DIR}_${CURRENT_DIR}"

# Examples of actual values:
piraz_ai_cli_sandboxed
candango_sqlok
myteam_myproject

# When you use $PROJECT_ID in a command, it expands to the actual value
echo "$PROJECT_ID:feature"  # Outputs: piraz_ai_cli_sandboxed:feature
```

## Rule of Thumb

**Whenever you see `$PROJECT_ID` in an example, mentally think:**
> "This will expand to something like `piraz_ai_cli_sandboxed` + whatever comes after. I need quotes to keep it together."

```
"$PROJECT_ID:initiative"  = "piraz_ai_cli_sandboxed:initiative"  ✅
$PROJECT_ID:initiative    = piraz ai_cli_sandboxed :initiative   ❌ (split into pieces)
```

## Pro Tip: Test Your Commands

Always verify by checking what actually gets passed to taskwarrior:

```bash
# Add '-v' for verbose to see what taskp receives
taskp -v add "$PROJECT_ID:feature" "Description"

# Or echo the command first to see expansion
echo taskp add "$PROJECT_ID:feature" "Description"
```

---

See also:
- `/project/templates/context/copilot-instructions.md` - Full integration guide
- `/project/templates/skills/taskwarrior_expert/SKILL.md` - Complete skill documentation
