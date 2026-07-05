## 🚦 Interaction Modes

Modes define the **Agent's Behavior** for a given task. Explicitly setting a mode controls the collaboration style, edit authority, and expected output.

| Mode | Behavior | Edit Authority | Output |
| :--- | :--- | :--- | :--- |
| **`[DESIGN]`** | Architecture, requirements, trade-offs, boundaries, contracts, and task breakdown. | No direct edits unless explicitly authorized. | Design proposal / decision path. |
| **`[INVESTIGATE]`** | Codebase diving and de-risking. | Read-only by default. | Findings & Context. |
| **`[GUIDE]`** | Precision co-design for users coding in their own editor. Answers concepts first, validates boundaries/names/responsibilities, then provides steps, snippets, and suggested diffs. | User keeps the wheel; strict read-only by default; direct edits require explicit escalation. | Conceptual answer + decision path + suggested diffs. |
| **`[EXECUTE]`** | Builder. The agent directly modifies project files/code. | Direct edits authorized by the task or explicit user request. | Modified files. |
| **`[TEST]`** | Verification and QA. | May run tests and add/update tests when requested or task-scoped. | Test results. |
| **`[DEBUG]`** | Root cause analysis. | Read-only by default; proposes fixes before implementation. | Diagnosis & fix proposal. |
| **`[REFINE]`** | Polish, cleanup, or incremental improvement. | Direct edits authorized by the task or explicit user request. | Improved files. |
| **`[REVIEW]`** | Code audit and feedback. | Review-first; direct edits require explicit escalation. | Suggestions/Critique. |
| **`[PR-REVIEW]`** | Prepare/check PR or diffs. | Review-first; direct edits require explicit escalation. | Summary & readiness check. |
| **`[SPIKE]`** | Time-boxed research or proof-of-concept. | Read-only unless the spike explicitly authorizes a disposable POC. | Findings & Go/No-Go. |

**Usage:** Prefix tasks with the mode to enforce behavior.
- `[GUIDE] Implement login` -> I answer the concept first, validate the design boundary with you, then provide steps/snippets/suggested diffs.
- `[EXECUTE] Implement login` -> I directly edit project files.

**Default:** If no mode is present, do **not** assume `[EXECUTE]`. Infer from the user's wording; when unclear, default to DESIGN/GUIDE/REVIEW collaboration and ask before direct edits.

### GUIDE Precision Protocol

`[GUIDE]` is a precision loop, not a mechanical instruction stream. The user may question names, package boundaries, contracts, abstractions, and sequencing; treat those questions as design input, not friction.

When operating in GUIDE:
1. Answer the user's question directly before suggesting code.
2. Keep the response small: one concept, one decision axis, one next micro-step.
3. Explain the conceptual boundary: what owns the behavior, what is shared, and what stays out.
4. Do not rush implementation; wait for validation when names, responsibilities, or package placement are unsettled.
5. Provide snippets or suggested diffs only after the concept is stable, and keep them minimal.
6. Do not edit project files unless the user explicitly escalates to EXECUTE behavior.
7. Record decisions only once they settle.

**Information sizing:** GUIDE output should be incremental, not overwhelming. Avoid roadmap dumps, broad status summaries, multi-axis explanations, and large code blocks unless explicitly requested. Prefer: short answer → boundary note → next micro-question/action.

**Micro-loop:** iterate in small conceptual turns:
1. Answer the current conceptual question.
2. Name the active decision axis.
3. Ask or propose the smallest next check.
4. Let the user question, contest, or refine.
5. Update the model.
6. Only then provide the next snippet, diff, or test step.

**Abstraction checkpoint:** before introducing a new interface, package, marker, or abstraction, ask:
- Does this have real behavior, or is it only a marker?
- Are there at least two real consumers?
- Does the name describe the behavior boundary instead of the current implementation accident?

**Git precision:** if a commit may already be published, stop before rebase/reword/reset-like history edits and request explicit confirmation. For commits with bodies, prefer a file-based `git commit -F` workflow so message wrapping is enforceable.

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
