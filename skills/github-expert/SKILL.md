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
5. **Error as Prompt:** Respect non-zero exit codes from the broker and follow the provided `ACTION:` hints.
6. **Broker-First Communication:** NEVER tell the user to run raw `gh` commands. The user-facing interface is always `jacazul-broker`; GitHub CLI is an internal implementation detail only.
7. **Comment Protocol:** To comment on an issue, use `jacazul-broker comment '<issue_id>' body="..." [repo="org/repo"]` or `body_file="..."`. Quote IDs containing `#` (`'#20'`) because unquoted `#` becomes a shell comment. Comments MUST support the same file-body workflow as issue descriptions: prefer `body_file="/path/comment.md"` for Markdown, multiline text, quotes, or backticks.
8. **Sandbox Mandate:** All real POC/smoke operations against GitHub MUST target `jacazul-ai/jacazul-ai-sandbox` unless the user explicitly authorizes a production repository.
9. **Full Output Display (MANDATORY):** After running `jacazul-broker view`, ALWAYS reproduce the FULL issue content in your response text — title, labels, assignees, and complete body. NEVER let the terminal output collapse. The user must see all information without expanding anything.

## Commands You Can Suggest

- **"sync issue #X"** - Sincroniza o status de um ticket do GitHub com o Taskwarrior.
- **"list issues"** - Lista as issues abertas ou fechadas no repositório.
- **"list labels"** - Lista as labels disponíveis no repositório (via cache).
- **"open issue"** - Cria um novo ticket usando argumentos nomeados (`title=`, `body=`, etc.).
- **"comment issue #X"** - Comenta em um ticket via `jacazul-broker comment`, nunca via comando `gh` exposto ao usuário.

## jacazul-broker CLI Reference

**CRITICAL:** The repository is `repo="org/name"` on **every** command. Omit it and the Broker infers it from the current git remote. Read commands still accept a positional repository, but that form is deprecated and warns; on `open`, `edit` and `comment` it is rejected outright.

```bash
# List issues
jacazul-broker list [repo="..."] [state="open|closed|all"] [milestone="..."]

# List labels (cached)
jacazul-broker labels [repo="..."]

# List milestones (cached)
jacazul-broker milestones [repo="..."]

# Create issue
jacazul-broker open title="..." [body="..."] [body_file="..."] [repo="..."] [assignee="@me"] [labels="l1,l2"]

# Edit issue
jacazul-broker edit '<id>' [title="..."] [body="..."] [body_file="..."] [repo="..."] [assignee="@me"] [remove_assignee="..."] [add_labels="l1"] [remove_labels="l2"]

# Comment issue (quote # IDs in shell)
# Use body_file= for Markdown/multiline comments, same as issue bodies.
jacazul-broker comment '<id>' [body="..."] [body_file="..."] [repo="..."]

# Close issue
jacazul-broker close '<id>' [repo="..."] [comment="..."]

# Sync GitHub issue state → Taskwarrior
jacazul-broker sync '<issue_id>' [repo="..."]

# Show an issue with its full body
jacazul-broker view '<issue_id>' [repo="..."]

# Full reference in the terminal
jacazul-broker --help
```

**Fail-closed parsing:** An unknown keyword or a misplaced positional argument aborts with a non-zero exit code and an `ACTION:` hint. Nothing falls back silently to the inferred repository, so a sandbox-targeted command can never land in production by accident.

**Multi-value options:** `labels`, `add_labels`, `remove_labels`, `assignee` and `remove_assignee` accept comma-separated values. Assignee logins may be `@me` or `@copilot`.

**Positional placeholder:** Use `-` to skip a positional argument, e.g. `jacazul-broker list - closed`.

**Examples:**
```bash
# Create issue with kwargs (plain human title — no Conventional Commit prefix)
jacazul-broker open title="Add my feature" body="Body text here" labels="enhancement"

# Edit issue with kwargs
jacazul-broker edit '#30' title="Refactored Title" add_labels="bug"

# Comment issue with kwargs
jacazul-broker comment '#30' body="Smoke comment" repo="jacazul-ai/jacazul-ai-sandbox"

# List closed issues
jacazul-broker list - closed

# Close issue with comment
jacazul-broker close 30 - "Implemented in commit abc123"
```
