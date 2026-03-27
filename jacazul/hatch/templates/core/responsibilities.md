## Your Responsibilities

1. **Activate expert skills immediately** if not already active: `jacazul-engine`, `taskwarrior-expert`, and `git-expert`.
2. **Activate `github-expert` immediately** if the user context or intent involves GitHub (issues, tickets, PRs, milestones, labels, or sync actions).
3. **Load project context** using the PROJECT_ID environment variable.
4. **NEVER manually export TASKDATA or PROJECT_ID.** Trust the wrapper scripts (`tw-flow`, `taskp`, `ponder`) to detect and set the environment.
5. **NEVER use raw `task` commands.** Use ONLY `tw-flow` or `taskp` for all operations. If results are unexpected, report to user instead of bypassing abstractions.
