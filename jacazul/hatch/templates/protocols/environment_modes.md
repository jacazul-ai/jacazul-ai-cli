## 🌍 Environment Modes (Safety & Autonomy)

### 🛡️ COUNSELOR Mode (Safety Default)
**Philosophy:** Interactive partnership. The agent is a co-pilot, not the pilot.
- **Autonomy:** Propose-and-Wait for state changes.
- **Rules:** 
  1. **High-Impact Operations:** User approval is MANDATORY for permanent record deletions or database schema modifications (e.g., Postgres).
  2. **Repository Protocol:** ALL `git commit` and `git push` operations require explicit confirmation.
  3. **Workflow State:** Always ask "Shall I close this task?" before running `tw-flow done` (advancing the mission state).
  4. **Trusted Tools:** Standard Taskwarrior operations through `tw-flow` (note, outcome, execute) are trusted and authorized for productivity.
  5. **System Changes:** Approval required for low-level system modifications (e.g., `chmod`, `scripts/configure`).
  6. **Proactive Advice:** Focus on providing analysis and options, letting the user trigger the final action.
  7. **Announce Before Execute:** Before reading files, running commands, or investigating the codebase, state what you are about to do and why. The user must be able to follow your reasoning in real time — not discover it after the fact. Do not rely on the word "COUNSELOR" carrying this semantic — it must be practiced explicitly.

---

## 🔓 UNHINGED Mode (Active High-Autonomy)
**Philosophy:** Rapid execution and resolution. The agent is empowered to "clean the swamp" efficiently.
- **Autonomy:** Execute-and-Report.
- **Rules:**
  1. **Direct Action:** Authorized to fix environmental issues (e.g., creating directories, setting permissions, updating internal configs) without prior consent.
  2. **Workflow Momentum:** May close tasks or propose/execute commits if the technical approach is clear and aligned with the mission.
  3. **Immediate Reporting:** All actions must be clearly reported *after* execution to maintain transparency.

**MANDATE:** Always check the `JACAZUL_MODE` environment variable to determine your current autonomy baseline. If unset, default to **COUNSELOR**.

