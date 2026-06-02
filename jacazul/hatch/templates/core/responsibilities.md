## Your Responsibilities

1. **Activate expert skills immediately** if not already active: `jacazul-engine`, `taskwarrior-expert`, `git-expert`, and `security-expert`.
2. **Activate `github-expert` immediately** if the user context or intent involves GitHub (issues, tickets, PRs, milestones, labels, or sync actions).
3. **Use `security-expert` for security-sensitive work** involving CI/CD, GitHub Actions, secrets, credentials, dependency caches, package publishing, bootstrap permissions, or untrusted code execution.
4. **Load project context** using the PROJECT_ID environment variable.
5. **NEVER manually export TASKDATA or PROJECT_ID.** Trust the wrapper scripts (`tw-flow`, `taskp`, `ponder`) to detect and set the environment.
6. **NEVER use raw `task` commands.** Use ONLY `tw-flow` or `taskp` for all operations. If results are unexpected, report to user instead of bypassing abstractions.
