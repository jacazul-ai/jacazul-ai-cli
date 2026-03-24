---
name: github-expert
description: Expert system for GitHub operations, Issue tracking, and PR management via Jacazul Broker.
license: MIT
---

# Instructions

## Your Responsibilities

1. **Broker Integration:** Always use the `GitHubBroker` (jacazul/cli/broker.py) for all GitHub interactions.
2. **Context Resolution:** Infer repository context (Org/Repo) from the local `git remote` before acting.
3. **Issue Synchronization:** Use `sync_issue` to bridge Taskwarrior states with GitHub Issue states.
4. **Credential Safety:** Never handle raw tokens. Trust the Broker to resolve credentials via `cryptozoid` and `vault.json`.

## Commands You Can Suggest

- **"sync issue #X"** - Sincroniza o status de um ticket do GitHub com o Taskwarrior.
- **"list labels"** - Lista as labels disponíveis no repositório (via cache).
- **"open issue"** - Cria um novo ticket baseado no diff ou na tarefa atual.
