## Multi-Agent Continuity Extension

This is an additive engine feature for collaboration across independent agents
and sessions. The existing solo workflow remains unchanged. The feature must
not remove or change existing solo behavior.

### Solo workflow remains unchanged

The solo workflow remains the default path:

```text
focus → context/status → execute → note → test/docs → outcome → done
```

Agents must continue to use the existing `tw-flow` commands, completion gates,
focus handling, and project isolation when working alone.

### Multi-agent continuity

When another agent or session continues the work:

1. `Taskwarrior` remains the source of truth for the project, focused task,
   dependencies, status, decisions, outcomes, and blockers.
2. The incoming agent reads `tw-flow focus`, the focused task context, and the
   current plan status before acting.
3. Decisions, research, lessons, outcomes, and handoffs are recorded with
   `tw-flow` annotations so they survive beyond chat history.
4. Persistent annotations use `JACAZUL_TASK_SIGNATURE` to identify the active
   persona, model, harness, and short session ID.
5. The next agent continues the same task or selects the next dependency; it
   does not recreate completed work or infer state from memory alone.
6. Completion still requires the existing `OUTCOME` record and `tw-flow done`.

This extension adds continuity and attribution around the solo workflow. It
must not change task semantics, autonomy gates, project isolation, or the
existing order of work for a solo agent.

## Consensus Review Protocol

Consensus review is an optional multi-persona feature layered on top of the
solo workflow. Use it when the decision is contested, cross-cutting, or costly
to get wrong:

- architecture, design, or policy decisions with meaningful trade-offs;
- security-sensitive, irreversible, or high-impact changes;
- conflicting findings from agents, tests, or authoritative sources;
- explicit requests for a second perspective or a consensus review.

Use a single-persona review for routine implementation, straightforward tests
or documentation, narrow fixes with an established cause, and decisions whose
scope and evidence are already clear.

### Consensus procedure

1. State the decision question and the evidence boundary before reviewing.
2. Have each relevant persona review independently from its own lens, such as
   Jacazul for workflow and policy or Codama for technical precision.
3. Cross-check findings and identify agreements, disagreements, assumptions,
   and missing evidence.
4. Resolve disagreements explicitly; do not hide a minority finding.
5. Verify material claims against authoritative sources before locking the
   decision.
6. Present the convergence as a verdict table with the decision and rationale.
7. Record the result as a signed `DECISION` note using
   `JACAZUL_TASK_SIGNATURE` on the active task.
8. Return to the normal solo workflow for implementation, testing,
   documentation, outcome, and completion.

### Consensus boundary

The current default mechanism is an in-context persona handoff in one shared
session. This protocol does not spawn separate agents automatically, change
persona authority, or alter the existing solo workflow. Separate-agent support
is an independent capability question and must be evaluated before adoption.
