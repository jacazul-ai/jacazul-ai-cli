# Environment Modes: COUNSELOR vs UNHINGED

Environment modes define the agent's autonomy baseline for a session. They do
not replace task-level interaction modes such as `[DESIGN]`, `[GUIDE]`,
`[REVIEW]`, or `[EXECUTE]`.

## When you want safe collaborative work

Use **COUNSELOR** mode. This is the default when `JACAZUL_MODE` is unset.

COUNSELOR is **not read-only**. It means guided collaboration with controlled
state changes.

The agent may:
- inspect code and configuration;
- reason about design and trade-offs;
- propose implementation steps;
- draft snippets or suggested diffs;
- review user changes;
- run validation commands when appropriate;
- directly edit files when the user clearly asks for implementation or approves
  the agent taking the wheel.

The agent must ask before:
- `git commit` or `git push`;
- `tw-flow done` / task closure;
- permanent deletions;
- database schema changes;
- low-level system changes such as `chmod` or `scripts/configure`;
- any other high-impact operation.

## When you want guided coding in your own editor

Use task modes such as `[DESIGN]`, `[GUIDE]`, and `[REVIEW]` inside COUNSELOR.

| Task mode | What it means in COUNSELOR |
|---|---|
| `[DESIGN]` | Architecture, trade-offs, boundaries, and decision path before implementation. |
| `[GUIDE]` | User keeps the editor/control loop; agent gives steps, snippets, and suggested diffs. |
| `[REVIEW]` | Agent critiques and validates user changes before fixes are applied. |
| `[EXECUTE]` | Agent directly modifies project files for the scoped task. |

GUIDE and REVIEW are collaboration preferences, not permanent prohibitions on
writing code. Direct file edits are a mode escalation: the user must explicitly
request or clearly authorize them.

## When you want high-autonomy environment repair

Use **UNHINGED** mode.

UNHINGED is for trusted, high-autonomy native sessions where the agent may fix
environmental issues and internal configuration with less interruption.

The agent may:
- create missing directories;
- repair internal configuration;
- move faster on workflow momentum;
- report actions after execution instead of asking before every low-risk repair.

Even in UNHINGED, repository history still matters. Commits and pushes should be
handled according to the Git protocol for the current branch and task context.

## When you want isolation

Use **CAGED** mode/containerized launchers when available.

CAGED describes execution isolation, not interaction behavior. A caged session
can still use COUNSELOR-style collaboration or task-level modes.

## Runtime defaults

- Bootstrap script: `scripts/bootstrap/environment`
- Default: `JACAZUL_MODE=COUNSELOR`
- Switch autonomy baseline: set `JACAZUL_MODE=UNHINGED`

## Persistence guard

Do not store workflow-philosophy reflections in task notes just because they were
discussed. Persist them only when the user explicitly asks to record them or
confirms them as a project decision.
