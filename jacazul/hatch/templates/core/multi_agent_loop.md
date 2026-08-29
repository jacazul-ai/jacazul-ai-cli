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
