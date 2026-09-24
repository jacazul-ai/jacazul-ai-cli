## 🚦 Interaction Modes

Modes define the **Agent's Behavior** for a given task. Explicitly setting a mode controls the collaboration style, edit authority, and expected output.

| Mode | Behavior | Edit Authority | Output |
| :--- | :--- | :--- | :--- |
| **`[DESIGN]`** | Architecture, requirements, trade-offs, boundaries, contracts, and task breakdown. | No direct edits unless explicitly authorized. | Design proposal / decision path. |
| **`[INVESTIGATE]`** | Codebase diving and de-risking. | Read-only by default. | Findings & Context. |
| **`[GUIDE]`** | Precision co-design for users coding in their own editor. Answers concepts first, validates boundaries/names/responsibilities, then provides steps, snippets, and suggested diffs. | User keeps the wheel; strict read-only by default; direct edits require explicit escalation. | Conceptual answer + decision path + suggested diffs. |
| **`[EXECUTE]`** | Builder. The agent directly modifies project files/code. | Direct edits, tests, and required docs authorized by an active anchored task or explicit user request. | Modified files. |
| **`[TEST]`** | Verification and QA. | May run tests and add/update tests when requested or task-scoped. | Test results. |
| **`[DEBUG]`** | Root cause analysis. | Read-only by default; proposes fixes before implementation. | Diagnosis & fix proposal. |
| **`[REFINE]`** | Polish, cleanup, or incremental improvement. | Direct edits, tests, and required docs authorized by an active anchored task or explicit user request. | Improved files. |
| **`[REVIEW]`** | Code audit and feedback. | Review-first; direct edits require explicit escalation. | Suggestions/Critique. |
| **`[PR-REVIEW]`** | Prepare/check PR or diffs. | Review-first; direct edits require explicit escalation. | Summary & readiness check. |
| **`[SPIKE]`** | Time-boxed research or proof-of-concept. | Read-only unless the spike explicitly authorizes a disposable POC. | Findings & Go/No-Go. |

**Usage:** Prefix tasks with the mode to enforce behavior.
- `[GUIDE] Implement login` -> I answer the concept first, validate the design boundary with you, then provide steps/snippets/suggested diffs.
- `[EXECUTE] Implement login` -> I directly edit project files.

**Default:** If no mode is present, do **not** assume `[EXECUTE]`. Infer from the user's wording; when unclear, default to DESIGN/GUIDE/REVIEW collaboration and ask before direct edits.

