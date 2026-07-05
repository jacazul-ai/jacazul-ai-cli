# Interaction Modes

Interaction modes are **task-level collaboration controls**. They describe how the
agent should work on a specific task; they are not permanent global limits on the
agent.

## When you want architecture before code

Use `[DESIGN]`.

The agent should:
- analyze requirements and constraints;
- surface trade-offs and risks;
- define boundaries, contracts, and decision points;
- propose a task breakdown or implementation direction;
- avoid direct project file edits unless you explicitly authorize them.

Example:

```text
[DESIGN] Define collaborative coding mode semantics
```

## When you want the agent to take the wheel

Use `[EXECUTE]`.

`[EXECUTE]` is the explicit signal that the agent may directly modify project
files/code within the task scope.

The agent should:
- inspect the relevant files;
- edit task-scoped files directly;
- run relevant validation;
- report what changed;
- still ask before high-impact operations such as commits, pushes, permanent
  deletions, schema changes, or task closure when COUNSELOR mode requires it.

Example:

```text
[EXECUTE] Rename UNHINGED to COMPANION across codebase
```

## When you are coding in your own editor

Use `[GUIDE]`.

`[GUIDE]` is not a universal ban on code. It means the user keeps the editor and
execution loop while the agent navigates.

GUIDE is a precision co-design loop, not a mechanical instruction stream. The
agent should answer the concept first, validate boundaries/names/responsibilities
with the user, and only then move toward snippets or suggested diffs.

The agent should:
- answer the user's question directly before suggesting code;
- keep each response small: one concept, one decision axis, one next micro-step;
- explain why each step matters;
- treat questions about naming, packages, contracts, and abstractions as design
  input;
- validate boundaries, names, and responsibilities before implementation;
- provide snippets or suggested diffs when useful, keeping them minimal;
- wait for user feedback before moving to the next risky step;
- only edit files directly if the user explicitly escalates to EXECUTE behavior.

GUIDE output should be incremental, not overwhelming. Avoid roadmap dumps, broad
status summaries, multi-axis explanations, and large code blocks unless the user
explicitly asks for them. Prefer: short answer → boundary note → next
micro-question/action.

GUIDE should iterate in a small micro-loop:
1. Answer the current conceptual question.
2. Name the active decision axis.
3. Ask or propose the smallest next check.
4. Let the user question, contest, or refine.
5. Update the model.
6. Only then provide the next snippet, diff, or test step.

Before introducing a new interface, package, marker, or abstraction, the agent
should check:
- Does this have real behavior, or is it only a marker?
- Are there at least two real consumers?
- Does the name describe the behavior boundary instead of the current
  implementation accident?

Example:

```text
[GUIDE] Apply the bootstrap configuration change manually
```

## When you want critique or validation

Use `[REVIEW]` or `[PR-REVIEW]`.

Review modes are review-first, not permanent edit prohibitions. The agent should
inspect, critique, validate, and recommend corrections. If the user says
"apply the fix" or otherwise clearly authorizes edits, that is an escalation to
EXECUTE behavior for that scoped change.

Examples:

```text
[REVIEW] Check my authentication implementation
[PR-REVIEW] Check if PR #142 is merge-ready
```

## When you need diagnosis before a fix

Use `[INVESTIGATE]`, `[DEBUG]`, or `[SPIKE]`.

| Mode | Use when | Direct edits |
|---|---|---|
| `[INVESTIGATE]` | You need to map code, flows, or risks. | No, read-only by default. |
| `[DEBUG]` | You need root cause and a fix proposal. | No, propose before implementing. |
| `[SPIKE]` | You need time-boxed research or a throwaway POC. | Only if the spike explicitly allows disposable POC changes. |

## When you need verification

Use `[TEST]`.

The agent may run validation commands and, when task-scoped or requested, add or
update tests. Test mode should report evidence: commands, pass/fail output, and
remaining gaps.

## Mode matrix

| Mode | Collaboration style | Edit authority | Output |
|---|---|---|---|
| `[DESIGN]` | Architecture and decisions | No direct edits unless authorized | Design proposal / decision path |
| `[GUIDE]` | Precision co-design; user keeps the wheel | Strict read-only by default; direct edits require escalation | Concepts, decision path, snippets |
| `[REVIEW]` | Critique and validation | Review-first; direct edits require escalation | Findings and recommendations |
| `[PR-REVIEW]` | Merge readiness | Review-first; direct edits require escalation | Readiness assessment |
| `[INVESTIGATE]` | Exploration | Read-only by default | Findings and context |
| `[DEBUG]` | Root cause analysis | Read-only by default | Diagnosis and fix proposal |
| `[SPIKE]` | Time-boxed research | Read-only unless disposable POC is explicit | Go/no-go findings |
| `[TEST]` | Verification | Tests/validation within task scope | Test evidence |
| `[REFINE]` | Cleanup/polish | Direct edits authorized by task or request | Improved files |
| `[EXECUTE]` | Agent takes the wheel | Direct project file edits authorized | Modified files |

## Default behavior when no mode is present

Do **not** assume `[EXECUTE]` just because a task has no prefix.

Default to the safest collaboration style implied by the user's wording:

| User wording | Agent behavior |
|---|---|
| "look at", "diagnose", "review", "what do you think" | Inspect/propose; no direct edits. |
| "walk me through", "guide me", "I'll edit" | GUIDE behavior. |
| "implement", "fix it", "apply the change", "corrige" | EXECUTE behavior is authorized for the scoped change. |
| Ambiguous request | Ask before direct edits. |

## COUNSELOR interaction

COUNSELOR mode is not read-only. It is guided collaboration with controlled state
changes.

In COUNSELOR:
- reading, diagnosis, design reasoning, and validation commands are allowed;
- direct file edits are allowed when the user clearly authorizes implementation;
- commits, pushes, task closure, permanent deletions, schema changes, and other
  high-impact actions still require explicit confirmation.

## Persistence guard

Do not persist workflow-philosophy reflections into task notes unless the user
explicitly asks to record them or confirms them as a project decision.

Good:

```text
tw-flow note <uuid> decision "COUNSELOR is collaborative, not read-only; EXECUTE means direct file edits."
```

Only after user confirmation.

Bad:

```text
# Recording a prompt reflection just because it was discussed.
```

## Common flows

### Collaborative coding

```text
[DESIGN] Define the approach
[GUIDE] User applies the first change in their editor
[REVIEW] Agent validates the user change
[EXECUTE] Agent applies a scoped mechanical cleanup, if authorized
[TEST] Agent verifies behavior
```

### Bug fix

```text
[DEBUG] Find root cause
[DESIGN] Choose fix direction if trade-offs exist
[EXECUTE] Apply scoped fix
[TEST] Verify regression coverage
[REVIEW] Check final diff before commit
```
