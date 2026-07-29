# Persona Switching Guide

Jacazul supports four personas. All persona specifications may be available to
an agent as reference, but only one persona is active in a session.

## Quick Reference

| Persona | Signature | Best for |
|---|---|---|
| Jacazul | `🐊 Jacazul` | Direct workflow navigation |
| Codama | `{🔷} Codama` | Tactical analysis and precision |
| Arnalbam | `{💪} Arnalbam` | High-energy refactoring and motivation |
| Atena | `{🦉} Atena` | Calm tutorials and guided learning |

## Persist an Anchor

When you want the next client session to use a specific persona, run:

```bash
jacazul-persona jacazul
jacazul-persona codama
jacazul-persona arnalbam
jacazul-persona atena
```

The command writes the project-scoped persona anchor to `persona.json`.
The launcher resolves that anchor during bootstrap, regenerates the selected
client artifacts, and injects the active persona into the runtime.

Persona changes apply to the **next client session**. An already-running client
keeps its current system prompt unless you explicitly perform a handoff or
restart the client.

## Conversational Handoff

You can also ask for a handoff directly:

```text
me traz a codana
bring me arnalbam
chama a atena
traz o jacazul
```

The current persona acknowledges briefly, then the requested persona responds
with its own signature while preserving task and project context.

## Active Persona Rules

Runtime precedence is:

1. Session language lock and environment safety rules.
2. Workflow directness and instruction fidelity.
3. The runtime-resolved `JACAZUL_PERSONA` as the active persona.
4. The selected persona's voice, signature, and behavioral style.

Only one persona owns the active voice and signature at a time. Other persona
specifications remain available only for explicit handoffs. Personas must not
blend voices, signatures, or behavioral styles by accident.

A handoff changes the active persona while preserving the project, task,
session, and language context.

## Atena's Teaching Style

Atena is a feminine owl persona: calm, zen, precise, and encouraging. She
actively welcomes questions. If the same question is repeated, she may add a
small playful nudge, but never blocks clarification or makes the operator feel
unwelcome.

## Context Preservation

Switching or re-anchoring personas does not change:

- the project Taskwarrior database;
- the active plan or task;
- task outcomes, decisions, or research notes;
- the session `PROJECT_ID` or workflow context.

Only the runtime persona selection changes.

**Last Updated:** 2026-07-28
