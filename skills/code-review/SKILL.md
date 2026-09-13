---
name: code-review
description: Global code-review levels, advisory decisions, evidence standards, and follow-up policy.
license: MIT
---

# Code Review Skill

Global review protocol for identifying risk, communicating findings, and
choosing an explicit outcome. Language-specific skills provide the scenarios;
this skill owns the review vocabulary and decision contract.

The labels below are the current project working vocabulary. They are kept in
one place so language skills do not invent competing scales. A language skill
must reference this file rather than redefining these labels.

## Two independent scales

Do not conflate **technical level** with **advisory**:

- Technical level describes how serious the technical outcome can be.
- Advisory describes what the reviewer recommends doing about the finding.

A review finding should report both when action is needed:

```text
Level: WARNING
Advisory: FIX-OR-TECH-DEBT
Area: TEMPORAL
Evidence: REPRODUCED
```

## Review method

Apply this sequence to every review, whatever the language. Language skills
add the scenarios; they do not replace these steps.

1. Read the project's toolchain and language-version manifest before judging
   version-sensitive behavior.
2. Identify the owner and lifetime of every mutable value, resource, task or
   thread, channel or queue, lock, transaction, and cancellation signal.
3. Reconstruct the runtime sequence: what starts, what can return, what can
   be canceled, and what cleanup runs at each boundary.
4. For each risky shape, state the consequence and request the smallest safe
   correction or a test proving the behavior is safe.
5. Run repository-configured checks; treat conventional tools as evidence,
   not proof that a behavior is correct.

## Scenario format

Language skills describe risky code shapes as scenarios. Two forms exist:

- **Catalog form** for numbered entries: `Problem`, `What can happen`,
  optional `Review questions`, and `Safer shape`.
- **Full form** for cross-cutting directives and worked examples: `Avoid`,
  `Context`, `Runtime sequence`, `Failure modes`, `Review directive`,
  `Acceptable correction`, and `Classification`.

Either form reports findings with the labels defined here. A language file
must not redefine levels, advisories, areas, or evidence.

### Tracks

Scenarios are grouped by track, which describes the learning path, not the
severity. A Foundations pattern can still create a critical incident.

| Track | Main concern | Typical impact |
|---|---|---|
| Foundations | Values, control flow, errors, and collection semantics | Wrong output, crashes, lost failures, corrupted responses |
| Boundaries | Ownership, resources, I/O, context, and concurrency lifecycle | Leaks, hangs, races, retries gone wrong, exhausted resources |
| Systems | Memory model, unsafe code, API contracts, security, and performance | Data corruption, privilege impact, process-wide outage, silent regressions |

Do not call tracks "levels". Level is reserved for the technical scale
below.

## Areas

Tag each finding with one or more areas. Areas describe what is at risk, not
how bad it is.

| Area | Covers |
|---|---|
| `CORRECTNESS` | Wrong results, logic errors, invalid state transitions |
| `LIFECYCLE` | Initialization, ownership, cleanup, shutdown, cancellation |
| `CONCURRENCY` | Races, deadlocks, ordering, synchronization protocols |
| `RESOURCE` | Memory, descriptors, connections, retention, backpressure |
| `CONTRACT` | Public API, wire formats, error contracts, compatibility |
| `SECURITY` | Trust boundaries, injection, secrets, randomness, privilege |
| `TEMPORAL` | Clocks, timezones, timers, durations, time-dependent tests |
| `PERFORMANCE` | Allocation, latency, throughput, benchmarks, runtime effects |
| `TEST` | Weak, flaky, or missing tests and false confidence |
| `POLICY` | Repository gates, tooling, conventions, and process |
| `CLARITY` | Naming, readability, documentation, misleading structure |
| `MAINTENANCE` | Duplication, drift, dead code, generated artifacts |

## Security priority mapping

`security-expert` reports formal audits with Critical, High, Medium, and Low.
In a code review those map onto the technical scale under area `SECURITY`:

| Security priority | Technical level | Default advisory |
|---|---|---|
| Critical | `BLOCKER` | `FIX-NOW` |
| High | `BLOCKER` | `FIX-NOW` |
| Medium | `WARNING` | `FIX-OR-TECH-DEBT` |
| Low | `SUGGESTION` | `FIX-OR-TECH-DEBT` or `ACCEPTED` |

Promote Medium to `BLOCKER` when the surface is exposed to untrusted input
and no compensating control exists. A formal audit may report both
vocabularies; a review comment uses the technical scale.

## Technical levels

### `BLOCKER`

The change creates a severe or immediate risk: broken essential behavior,
data loss or corruption, security exposure, unrecoverable lifecycle failure,
or a merge gate that cannot be trusted.

- Merge: do not merge until corrected.
- Evidence: require a reproduction, a clear runtime trace, or strong tool
  evidence.
- Normal advisory: `FIX-NOW`.
- `BLOCKER + TECH-DEBT` is not a valid default; if deferral is acceptable,
  lower the technical level after reassessing the impact.

### `WARNING`

The change contains a credible risk or contract weakness, but the evidence and
impact do not automatically justify blocking the merge.

- Merge: may proceed only with an explicit advisory outcome.
- Evidence: prefer a reproduction or a clear runtime/lifecycle trace.
- Normal advisory: `FIX-OR-TECH-DEBT`.
- Promote to `BLOCKER` when the risk affects critical correctness, security,
  data integrity, essential availability, or the merge gate itself.

### `SUGGESTION`

A meaningful improvement to correctness, maintainability, observability,
performance, or test quality that is not an immediate failure in the reviewed
change.

- Merge: normally may proceed.
- Advisory: `FIX-NOW`, `FIX-OR-TECH-DEBT`, `TECH-DEBT`, or `ACCEPTED`, based on
  scope and expected value.
- Evidence: explain the contract or future failure mode; do not present taste
  as a defect.

### `NIT`

A small readability, wording, naming, or local style improvement with no
meaningful behavior or risk impact.

- Merge: may proceed.
- Advisory: normally `ACCEPTED` or an optional correction.
- Evidence: keep the comment short and avoid pretending it is a defect.

`QUESTION`, `PRAISE`, and similar terms describe comment intent, not technical
levels. They must not be used to disguise an unclassified risk.

## Advisory outcomes

### `FIX-NOW`

The correction belongs in the current change. No deferral is offered by this
outcome. It is the normal advisory paired with a genuine `BLOCKER`.

### `FIX-OR-TECH-DEBT`

The finding is non-blocking, but it is actionable. The author must either fix
it in the current change or create a linked `TECH-DEBT` task before the review
is complete. “Later” without a record is not an outcome.

### `TECH-DEBT`

The team explicitly accepts deferral because the change can safely merge. A
tracked task must preserve:

- the affected file, package, or behavior;
- the failure mode and impact;
- the reason it is not being fixed now;
- the suggested direction;
- a verifiable acceptance criterion;
- ownership or a responsible plan when the project tracks it.

### `ACCEPTED`

The reviewer and owner explicitly accept the current behavior or suggestion.
Record the rationale when the finding represents a real risk; silence is not
acceptance.

## Disposition rules

Use these rules to prevent scale confusion:

| Technical level | Default advisory | Can defer? | Merge effect |
|---|---|---:|---|
| `BLOCKER` | `FIX-NOW` | No | Blocks merge |
| `WARNING` | `FIX-OR-TECH-DEBT` | Yes, with a task | Non-blocking after disposition |
| `SUGGESTION` | `FIX-OR-TECH-DEBT` or `ACCEPTED` | Yes | Normally non-blocking |
| `NIT` | `ACCEPTED` | Yes | Non-blocking |

The table is a default, not a substitute for reasoning. A warning can require
`FIX-NOW` when the team wants the change corrected immediately without calling
it a severe technical incident. A blocker cannot be made harmless by naming it
tech debt.

## Evidence levels

Use the strongest available evidence:

- `REPRODUCED`: a focused test, trace, panic, race report, or failure case
  demonstrates the problem.
- `TOOL`: a configured analyzer or scanner identifies a relevant path.
- `TRACE`: ownership, control flow, or runtime ordering proves a credible
  failure without depending on a lucky schedule.
- `HEURISTIC`: the pattern deserves attention, but the impact depends on an
  unverified contract or workload.

Evidence is not severity. A heuristic security concern can still deserve a
warning; a reproduced cosmetic issue remains a nit.

## Review comment contract

Write actionable findings in this order:

```text
[LEVEL] [ADVISORY] [AREA] [EVIDENCE]

Context: where the risky assumption applies.
Sequence: what runs first and what can run later or concurrently.
Failure: what can happen and who is affected.
Action: fix now, or create/link the required tech-debt task.
Evidence: test, tool output, trace, or missing proof.
```

Example:

```text
[WARNING] [FIX-OR-TECH-DEBT] [TEMPORAL] [REPRODUCED]

Context: the test reads the host clock and mixes local time with UTC.
Sequence: the expected and actual values are computed at different instants
and may cross a timezone or DST boundary.
Failure: the test can pass without proving the contract or fail intermittently.
Action: inject a fixed instant now, or create a tech-debt task covering the
clock contract and UTC/DST cases.
```

## Review workflow

1. Identify the behavior and the contract it must preserve.
2. Reconstruct ownership, lifetime, ordering, cancellation, and trust
   boundaries.
3. Describe the failure mode before assigning a label.
4. Assign one or more technical areas and one technical level.
5. Assign an advisory outcome separately.
6. Request a fix, a linked tech-debt task, or explicit acceptance according to
   the advisory.
7. Verify the correction with the smallest useful test or tool evidence.

## Language-specific extensions

Each `<lang>-expert` skill plugs into this core through a fixed contract:

- Its `SKILL.md` links this file and its own `CODE-REVIEW.md`.
- Its `CODE-REVIEW.md` contains scenarios in the [scenario format](#scenario-format),
  grouped by [track](#tracks), and nothing else about the scale.
- The automated baseline lives once, in the expert `SKILL.md`; the review
  file links it rather than repeating it.
- Findings use the levels, advisories, areas, and evidence defined here.

Current extensions:

- Go: [Go review directives](../go-expert/CODE-REVIEW.md).
- Rust: [Rust review directives](../rust-expert/CODE-REVIEW.md).
