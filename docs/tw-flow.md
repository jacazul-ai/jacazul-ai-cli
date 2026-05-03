# tw-flow CLI Reference

The main workflow tool for the Jacazul AI CLI. Manages tasks, initiatives (plans/inis), session focus, and project state.

> For agent behavior and the 7-phase workflow, see [taskwarrior-expert.md](taskwarrior-expert.md).
> For output caching, see [tw-flow-cache.md](tw-flow-cache.md).

---

## 📍 Script Locations

```
~/bin/          (symlinked from /project/skills/taskwarrior-expert/scripts/)
```

Available scripts:
- `tw-flow` — Main workflow tool
- `taskp` — Project-aware Taskwarrior wrapper

**For AI Agents:** Always use `taskp` or `tw-flow`. NEVER invoke the raw `task` binary directly.

---

## 🚀 Quick Start

```bash
# See current state
tw-flow ponder

# Create an initiative (plan and ini are aliases)
tw-flow plan my-feature \
  "DESIGN|Design API schema|research|today" \
  "EXECUTE|Implement endpoints|implementation|tomorrow" \
  "TEST|Write tests|testing|2days"

# Execute a task
tw-flow execute <uuid>

# Add context
tw-flow note <uuid> decision "Using approach A"

# Close
tw-flow outcome <uuid> "Implemented OAuth flow"
tw-flow done <uuid>
```

---

## 📋 Command Reference

### Plan / Initiative Management

`plan` and `ini` (initiative) are aliases — both refer to the same concept.

```bash
tw-flow plan <name> <tasks...>     # Create a new plan/ini
tw-flow ini <name> <tasks...>      # Same as plan
tw-flow plans                      # List active plans (backlog hidden by default)
tw-flow plans --with-backlog       # Include backlog plans (marked 💤)
tw-flow plans --all                # Show all plans including closed
tw-flow rename <old> <new>         # Rename a plan
```

### Plan State Management

Plans have three lifecycle states:

| State | Visibility | Command | Marker |
|---|---|---|---|
| **active** | Default views | (created state) | `●` |
| **backlog** | Hidden by default | `tw-flow backlog <plan>` | `💤` |
| **archive** | Hidden by default | auto on last task done | `✓` |

```bash
tw-flow backlog <plan>             # Move plan to backlog (hidden, 💤)
tw-flow activate <plan>           # Restore backlog plan to active
```

Backlog plans are hidden from `ponder` and `plans` by default. Use `--with-backlog` to reveal them.

### Task Execution

```bash
tw-flow execute <uuid>             # Start working on a task
tw-flow done <uuid>                # Close a task (requires outcome)
tw-flow outcome <uuid> "<msg>"     # Record result before closing
tw-flow reopen <uuid>              # Revert completed task to pending
tw-flow discard <uuid>             # Soft-delete (moves to _archive)
```

### Context & Annotations

```bash
tw-flow note <uuid> <type> "<msg>" # Add structured note
tw-flow context <uuid>             # Show full task context
tw-flow amend <uuid> description="..." ticket="..."  # Fix metadata
```

Note types: `research` (r), `decision` (d), `blocked` (b), `lesson` (l), `question` (q), `hypothesis` (y), `outcome` (o), `note` (n), `link`.

### Status & Visibility

```bash
tw-flow status [plan]              # Current plan status (hands-on view)
tw-flow status [plan] --pending    # Hide completed tasks
tw-flow ponder                     # Full project landscape (horizon view)
tw-flow ponder <plan>              # Filtered landscape
tw-flow ponder --all               # Bypass interest filters
tw-flow ponder --with-backlog      # Include backlog plans
tw-flow tree [plan]                # ASCII dependency tree
```

### Ticket Integration

```bash
tw-flow ticket <uuid> <id>         # Link task to external ticket
```

### Focus & Session Anchor

```bash
# Global focus
tw-flow focus plan <name>          # Anchor to a plan
tw-flow focus task <uuid>          # Anchor to a task
tw-flow focus pop                  # Revert to previous focus
tw-flow focus clear                # Reset anchors (keeps session file)
tw-flow focus interest add <name>  # Add plan to dashboard interest list
tw-flow focus <plan-name>          # Smart focus

# Independent session (isolated via JACAZUL_SESSION_ID)
tw-flow focus ind plan <name>      # Anchor in isolated session
tw-flow focus ind task <uuid>      # Anchor task in isolated session
tw-flow focus back                 # Exit independent session, return to global focus.json
```

Bootstrap pre-seed:
```bash
JACAZUL_FOCUS_PLAN=my-plan JACAZUL_FOCUS_TASK=<uuid> jacazul-claude
```

### Cache

```bash
tw-flow status --force             # Bypass cache, always show full output
tw-flow ponder --force             # Bypass cache, always show full output
tw-flow cache clear                # Clear all cached output
tw-flow cache clear status         # Clear only status cache
tw-flow cache clear ponder         # Clear only ponder cache
tw-flow cache config               # Configure TTLs
tw-flow cache info                 # Show cache state and expiry times
```

> See [tw-flow-cache.md](tw-flow-cache.md) for full cache documentation.

---

## 🔄 Taskwarrior Version Parity

To ensure data integrity across host OS versions (e.g., Debian 12 with TW 2.6.2 and Fedora 43 with TW 3.4.1):

### Host Version Detection

`scripts/bootstrap/environment` detects the host Taskwarrior version:
- **TW 3 (host):** Selects `ai-sandbox-fedora` image (Fedora 43).
- **TW 2 (host):** Selects `ai-sandbox` image (Ubuntu/Debian).

### Automatic SQLite Migration

When running in a TW 3 environment, `scripts/bootstrap/taskwarrior` detects legacy 2.x data and migrates automatically:
- **Backup:** Full backup at `~/.jacazul-ai/.task-backups/migration-TIMESTAMP/`
- **Import:** Runs `task import-v2 rc.hooks=0` to convert to Taskchampion (SQLite)
- **Isolation:** Migration is per-project via `TASKDATA`

---

**Version:** 1.1.0
**Last Updated:** 2026-04-02
