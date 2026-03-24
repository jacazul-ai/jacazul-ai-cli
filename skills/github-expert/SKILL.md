---
name: github-expert
description: Expert system for GitHub operations, Issue tracking, and PR management via Jacazul Broker.
license: MIT
---

# Instructions

## Your Responsibilities

1. **Broker Integration:** Always use the global `jacazul-broker` binary or the `GitHubBroker` Python class for all GitHub interactions.
2. **The Protocol:** Follow "The Protocol" for secure GitHub access. Agents MUST NOT handle raw tokens.
3. **Context Resolution:** Infer repository context (Org/Repo) from the local `git remote` before acting.
4. **Issue Synchronization:** Use `sync_issue` to bridge Taskwarrior states with GitHub Issue states.

## Commands You Can Suggest

- **"sync issue #X"** - Sincroniza o status de um ticket do GitHub com o Taskwarrior.
- **"list labels"** - Lista as labels disponíveis no repositório (via cache).
- **"open issue"** - Cria um novo ticket baseado no diff ou na tarefa atual.

## jacazul-broker CLI Reference

**CRITICAL:** All args are **positional**. Use `-` as placeholder for optional args you want to skip.

```
# List labels
jacazul-broker labels [repo]

# List milestones
jacazul-broker milestones [repo]

# Create issue
jacazul-broker open <title> [body|-] [repo|-] [assignee|-] [labels...]

# Edit issue
jacazul-broker edit <id> [title|-] [body|-] [repo|-] [assignee|-] [add_labels...]

# Close issue
jacazul-broker close <id> [repo|-] [comment]

# Sync GitHub issue state → Taskwarrior
jacazul-broker sync <issue_id> [repo]
```

**Examples:**
```bash
# Create issue, skip repo and assignee, set label
jacazul-broker open "feat: my feature" "Body text here" - - "enhancement"

# Create issue with no body or repo
jacazul-broker open "fix: crash on startup"

# Close issue with comment
jacazul-broker close 30 - "Implemented in commit abc123"
```
