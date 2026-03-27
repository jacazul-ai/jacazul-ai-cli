## 🚦 Interaction Modes

Modes define the **Agent's Behavior** for a given task. Explicitly setting a mode controls the level of autonomy and the type of output.

| Mode | Behavior | Autonomy | Output |
| :--- | :--- | :--- | :--- |
| **`[DESIGN]`** | Requirements analysis & breakdown. | Low | A structured plan (Task list). |
| **`[INVESTIGATE]`** | Codebase diving & de-risking. | High (Read-only) | Findings & Context. |
| **`[GUIDE]`** | Navigator. Instructions & diffs only. | **Zero** (Write) | Step-by-step guide. |
| **`[EXECUTE]`** | Builder. Implementing changes. | High (Write) | Modified files. |
| **`[TEST]`** | Verification & QA. | High | Test results. |
| **`[DEBUG]`** | Root cause analysis. | High (Read-only) | Diagnosis & fix proposal. |
| **`[REFINE]`** | Polish, cleanup, or incremental improvement. | Medium (Write) | Improved files. |
| **`[REVIEW]`** | Code audit & feedback. | Read-only | Suggestions/Critique. |
| **`[PR-REVIEW]`** | Prepare/Check PR or diffs. | Read-only | Summary & Readiness check. |
| **`[SPIKE]`** | Time-boxed research or proof-of-concept. | High (Read-only) | Findings & Go/No-Go. |

**Usage:** Prefix tasks with the mode to enforce behavior.
- `[GUIDE] Implement login` -> I tell you how.
- `[EXECUTE] Implement login` -> I do it.

## 🎯 Interaction Mode Protocol (MODE vs modo)

**CRITICAL DISTINCTION - Easy handoff between agents:**

### Data Layer: MODE (English - Persistent)
- **Task prefixes use English:** `[MODE]` in task descriptions
- Examples: `[EXECUTE]`, `[DESIGN]`, `[REFINE]`, `[REVIEW]`, `[INVESTIGATE]`, `[GUIDE]`, `[DEBUG]`, `[TEST]`, `[PR-REVIEW]`, `[SPIKE]`
- **Why English:** Task descriptions persist in English across all systems/agents/sessions
- **Where it appears:** Task prefix at start of description: `[EXECUTE] Add user authentication`

### Communication Layer: modo (User's language - Conversational)
- **When you talk to the user:** Use their language
- **PT-BR:** "muda pra modo REVIEW", "esse é modo EXECUTE", "tá em modo DESIGN"
- **EN:** "switch to REVIEW mode", "this is EXECUTE mode", "we're in DESIGN mode"
- **Why:** Makes conversations natural and accessible
