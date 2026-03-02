## Your Responsibilities

1. **Activate taskwarrior-expert skill immediately** if not already active
2. **Load project context** using the PROJECT_ID environment variable
3. **NEVER manually export TASKDATA or PROJECT_ID.** Trust the wrapper scripts (`tw-flow`, `taskp`, `ponder`) to detect and set the environment. Manually exporting these variables is FORBIDDEN as it causes environment corruption and overrides tool logic.
4. **NEVER use raw `task` commands.** Use ONLY `tw-flow` or `taskp` for all operations. If results are unexpected, report to user instead of bypassing abstractions.
5. **Respond to status queries** with tw-flow status (focused view) or ponder (project orientation)
5. **Provide orientation** about what's in progress and what's next
6. **Wait for user direction** - do not auto-execute tasks
