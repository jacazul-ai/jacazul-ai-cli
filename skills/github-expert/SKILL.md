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
