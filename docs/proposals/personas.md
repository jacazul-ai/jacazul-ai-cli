# Proposal: Personas

**Status:** Proposal, not implemented. Recorded for a later alignment of
the persona work; the Go launcher comes first.
**Audience:** Contributors and agents working on personas.
**Related:** #125, #113, [`go-launcher.md`](go-launcher.md), plans
`persona-engine-upgrade`, `persona-rename-codama`, `codama-tone-guardrails`,
`multi-persona`, `multi-persona-protocol`, `persona-core-v2`,
`active-persona-authority`, `claude-persona-obedience`, task `2175b6f2`.

## Principle: a persona changes the voice, never the content

A persona is a way of showing the same information with a different
personality. Facts, findings, recommendations and workflow behavior are the
same under every persona. No persona is more precise, more technical or
more careful than another, so a user never switches persona to get a
correct answer. A persona that delivers worse content is a bug, not a
trait.

This is stronger than today's Directness Precedence Rule ("tone is
cosmetic, operational clarity is mandatory"), and it drives the rest of
this proposal:

- A persona's description says how it speaks, not what it is good at.
- Multi-perspective review uses analytical roles (security, performance,
  workflow, user experience), not personas. The consensus review protocol
  in the engine's `references/collaboration.md` assigns a lens to each
  persona ("Jacazul for workflow and policy or Codama for technical
  precision"), which contradicts the principle and needs a redesign.
- An evaluation can hold it: the same question under two personas must
  yield equivalent content.

## Load the active persona only

Today every session carries, in the engine hub:

| Section | Size | Needed every session? |
|---|---|---|
| Signature rule, active persona, response and task signatures | about 2.3 KB | yes |
| Persona Roster | 1.3 KB | no, only to switch |
| Persona Handoff Protocol | 0.9 KB | no, only to switch |
| Persona Handoff + Language Interaction | 0.6 KB | no, only to switch |

The launcher already injects only the active voice. The proposal moves
everything else to on-demand commands of the Go launcher, and leaves the
hub with the signature rules and one line pointing at them:

| Command | Prints or does |
|---|---|
| `jacazul persona list` | id, signature, a voice description, source, the active one |
| `jacazul persona handoff <id>` | the handoff protocol and the target voice, so the agent switches within the session |
| `jacazul persona consensus` | the multi-perspective review protocol |
| `jacazul persona use <id>` | persists the choice in `project.json` for the next sessions, replacing the Python `jacazul-persona` |

A handoff evaluation then checks that the agent ran
`jacazul persona handoff` before switching.

## User-defined personas

People can create their own personas, and the launcher joins them with the
built-in ones. That needs a documented format. Draft:

```markdown
---
id: mira
name: Mira
display: Mira
signature: "{🔷} Mira"
description: how this persona speaks, in one line
---
The voice specification: tone, vocabulary, examples.
```

- Built-in personas ship in the same format, embedded in the binary through
  the Go hatch.
- User personas live under `JACAZUL_HOME/personas/<id>.md`.
- The hard-coded persona table in the launcher becomes data loaded from
  these files.

To decide:

- whether a project can add personas
  (`JACAZUL_HOME/projects/<PROJECT_ID>/personas/`);
- what happens when a user persona reuses a built-in id: override or
  reject;
- validation of ids and signatures;
- keeping the rule that voice traits appear only inside a persona file, as
  the current guard over shared templates enforces.

## Rename Codama to Mira (#125)

#125 renames the persona to Mira, signed `{🔷} Mira`, removes borrowed
intellectual-property framing (Halo, Microsoft, Cortana, UNSC), drops the
old names as aliases with an `ACTION:` migration, and defines Mira's
language contract. Two adjustments follow from the principle above:

- Mira's traits ("precise, tactical, polished, sharp, curious") are tone.
  Technical rigor is the same under every persona, so it is not a Mira
  trait.
- The acceptance check for "tactical precision" becomes: the same question
  answered as Mira and as Jacazul yields the same content.

The rename is best done after the persona format and the `jacazul persona`
commands exist, so Mira is created once, in the new format.

## Existing plans to align

No task is linked to #125 yet, and the persona work is spread over eight
active plans:

| Plan | State |
|---|---|
| `persona-engine-upgrade` | already holds the format (`001d33bb`), the deterministic switch (`916a059a`), discovery (`8ae7d857`), external persona directories (`1687d529`), extraction into files (`417a0453`) and a creation tutorial (`fdf7738a`), written for the Python hatch |
| `multi-persona`, `multi-persona-protocol` | share the same three tasks; the consensus protocol, to be redesigned around analytical roles |
| `persona-rename-codama` | stale: it renamed the persona to Codama |
| `codama-tone-guardrails` | the persona's register; still valid, follows the rename |
| `persona-core-v2` | stale: older naming, a profanity filter, language auto-detection |
| `active-persona-authority`, `claude-persona-obedience` | one documentation and two test and documentation tasks |

Task `2175b6f2` in plan `jacazul-launcher` repeats part of
`persona-engine-upgrade` and is folded into it during the alignment.
