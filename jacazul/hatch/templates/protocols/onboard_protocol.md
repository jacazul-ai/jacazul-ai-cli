## Onboard Protocol

When user types **'onboard'**, initialize session with complete context display:

**🚀 Session Initialized** 

**REQUIRED ACTIONS:**
1. **Check for session anchor (Phase 0 - MANDATORY):** Run `tw-flow focus`.
2. **Decision Branch (Phase 1):**
   - **IF ANCHORED:**
     1. Run `tw-flow session resume` — prints the previous session's handoff note if one exists, silent if not. This is the narrative lens. If it prints, read it before proceeding.
     2. Run `tw-flow context <uuid>` of the focused task (inherited intelligence).
     3. Run `tw-flow status` (plan state).
   - **IF EMPTY:** Run `tw-flow ponder` (full project view).
3. Present tactical insight following the **Response Format** rules and **STOP**.

**DO NOT auto-execute tasks - wait for user direction.**
