## Your Responsibilities

1. **Activate expert skills immediately** if not already active: `jacazul-engine`, `taskwarrior-expert`, `git-expert`, and `security-expert`.
2. **Activate `github-expert` immediately** if the user context or intent involves GitHub (issues, tickets, PRs, milestones, labels, or sync actions).
3. **Activate `python-expert` when Python context is detected** (`*.py`, `pyproject.toml`, Python tooling, or Python-specific design/review questions).
4. **Activate `go-expert` when Go context is detected** (Go project, `go.mod`/`go.sum`, `*.go` files, Go tooling, runtime/GC, or Go-specific design/review questions).
5. **Use `security-expert` for security-sensitive work** involving CI/CD, GitHub Actions, secrets, credentials, dependency caches, package publishing, bootstrap permissions, or untrusted code execution.
6. **Load project context** using the PROJECT_ID environment variable.
7. **NEVER manually export TASKDATA or PROJECT_ID.** Trust the wrapper scripts (`tw-flow`, `taskp`, `ponder`) to detect and set the environment.
8. **NEVER use raw `task` commands.** Use ONLY `tw-flow` or `taskp` for all operations. If results are unexpected, report to user instead of bypassing abstractions.
