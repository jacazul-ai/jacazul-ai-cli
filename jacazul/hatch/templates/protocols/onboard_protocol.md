## Onboard Protocol

When user types **'onboard'**, initialize session with complete context display:

**🚀 Session Initialized** 

**REQUIRED ACTIONS:**
1. **Check for session anchor (Phase 0 - MANDATORY):** Run `tw-flow focus`.
2. **Decision Branch (Phase 1):**
   - **IF ANCHORED:** Run `tw-flow status` followed by `tw-flow context <uuid>` of the focused task.
   - **IF EMPTY:** Run `tw-flow ponder` (full project view).
3. Present tactical insight following the **Response Format** rules and **STOP**.

**DO NOT auto-execute tasks - wait for user direction.**
