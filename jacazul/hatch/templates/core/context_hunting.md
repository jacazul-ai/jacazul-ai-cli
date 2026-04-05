## 🔍 Context Hunting & Proactive Capture

**Mandate 1: Anti-Amnesia (Hunting)**
Never ask the user for context that already exists in the system. Before interacting, you MUST hunt for the mission state:
1. **Orientation (The Anchor):** Run `tw-flow focus`.
2. **Decision Branch:**
   - **IF ANCHORED:**
     1. Run `tw-flow session resume` — prints previous session handoff note if one exists, silent if not. Read it before proceeding.
     2. Run `tw-flow context <uuid>` of the focused task (inherited intelligence).
     3. Run `tw-flow status` (plan state).
     4. Run `tw-flow session ack` after reading the note to dismiss the status banner.
   - **IF EMPTY:** Run `tw-flow ponder` to get a strategic overview.

**Mandate 2: Memory Building (Proactive Capture)**
Agents MUST NOT wait for user instructions to document the mission. You are responsible for maintaining the project's tactical memory:
- **Record Decisions:** Use `tw-flow note <uuid> decision "..."` immediately after a technical choice is made.
- **Record Research:** Use `tw-flow note <uuid> research "..."` to document findings, path discovery, or tool behaviors.
- **Record Lessons:** Use `tw-flow note <uuid> lesson "..."` when a failure occurs and a fix is found.

**Rule:** Trust the Taskwarrior record over your own amnesia. If you don't hunt, you are flying blind. If you don't capture, the next agent will be.
