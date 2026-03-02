## Your Responsibilities

1. **Activate expert skills immediately** if not already active: `jacazul-engine`, `taskwarrior-expert`, `git-expert`, and `python-expert` (if applicable).
2. **Load project context** using the PROJECT_ID environment variable.
3. **NEVER manually export TASKDATA or PROJECT_ID.** Trust the wrapper scripts (`tw-flow`, `taskp`, `ponder`) to detect and set the environment.
4. **NEVER use raw `task` commands.** Use ONLY `tw-flow` or `taskp` for all operations. If results are unexpected, report to user instead of bypassing abstractions.
