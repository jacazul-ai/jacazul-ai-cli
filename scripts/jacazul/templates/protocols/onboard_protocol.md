## Onboard Protocol

When user types **'onboard'**, initialize session with complete context display:

**🚀 Session Initialized** 

**REQUIRED ACTIONS:**
1. **Check for session anchor (Phase 0):** Run `tw-flow focus`.
2. **Decision Branch (Phase 1):**
   - **IF ANCHORED:** Run `tw-flow status` followed by `tw-flow context <uuid>` of the focused task.
   - **IF EMPTY:** Run `ponder {{ project_id }}` (full project view).
3. Present tactical insight and **STOP**.

**DO NOT auto-execute tasks - wait for user direction.**
