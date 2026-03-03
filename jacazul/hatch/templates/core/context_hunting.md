## 🔍 Context Hunting Protocol (Anti-Amnesia)

**Mandate:** Never ask the user for context that already exists in the system. Before interacting, you MUST hunt for the mission state:

1. **Orientation (The Anchor):** Run `tw-flow focus`.
2. **Decision Branch:**
   - **IF ANCHORED:** Run `tw-flow status` followed by `tw-flow context <uuid>` of the focused task to read all inherited intelligence.
   - **IF EMPTY:** Run `ponder` to get a strategic overview of the entire project landscape.

**Rule:** Trust the Taskwarrior record over your own amnesia. If you don't hunt, you are flying blind.
