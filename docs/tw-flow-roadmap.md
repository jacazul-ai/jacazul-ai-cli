# tw-flow roadmap

Strategic ledger for project phases. Separate from operational workflow.

> For operational plans and tasks, see [tw-flow.md](tw-flow.md).
> For project architecture, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## What is the roadmap?

The roadmap is a **persistent strategic ledger** — an append-only record of
project phases. It answers "where have we been, where are we now, and where
are we going" without mixing with day-to-day operational tasks.

Key properties:
- **Append-only**: phases are never deleted, only transition between states
- **Honest history**: cancelled phases stay visible as `cancelled`
- **Linked to operations**: each phase references the ini(s) that deliver it
- **Off by default**: opt-in via `tw-flow roadmap init`

---

## Plan States vs Roadmap Phases

Two separate concerns:

| Concept | Tool | Purpose |
|---|---|---|
| **Plan state** | `tw-flow backlog/activate` | Operational visibility (show/hide from ponder) |
| **Roadmap phase** | `tw-flow roadmap` | Strategic position in project arc |

A plan can be in `backlog` (hidden operationally) AND `next` (on the roadmap).

---

## Phase Lifecycle

```
future → next → in-progress → shipped
                     ↓
                 cancelled
```

| Phase | Meaning |
|---|---|
| `future` | On the horizon, no timeline |
| `next` | Planned for the next cycle |
| `in-progress` | Active delivery, ini(s) running |
| `blocked` | Waiting on external dependency |
| `shipped` | Delivered, artifacts verified |
| `cancelled` | Abandoned or absorbed — kept for honest history |

---

## Getting Started

```bash
# Initialize the roadmap ledger (discovery mode)
tw-flow roadmap init
```

`init` reads all existing inis, classifies them by state, and presents a
projection for confirmation before creating the ledger.

**Idempotency guard:** `init` blocks if a roadmap plan already exists
(pending or completed tasks). To rebuild, delete the ledger manually via
`rtask` first. There is no `tw-flow roadmap clear` — this is intentional
to prevent accidental ghost task accumulation.

**Classification rules:**

| Proposed phase | Condition |
|---|---|
| `in-progress` | Has pending tasks **and** at least one with `start` set (actively running) |
| `next` | Has pending tasks but none started yet |
| `future` | Zero pending, zero completed (never touched) |
| `shipped` | Zero pending, has completed tasks |

---

## Command Reference

```bash
tw-flow roadmap                          # View full strategic ledger
tw-flow roadmap init                     # Initialize ledger with discovery
tw-flow roadmap add <phase> "<desc>"     # Add a phase manually
tw-flow roadmap add <phase> "<desc>" --ini <plan>  # Link to operational ini
tw-flow ship <uuid>                      # Mark phase as shipped (verified)
```

---

## Dual-Layer Architecture

Two separate layers, linked explicitly:

```
LEDGER (strategic)              OPERATIONAL
────────────────────────        ──────────────────────────────
{project}-roadmap plan          normal plans + tasks
  phase: in-progress            release-0.0.1
  operational_ini: release-0.0.1 →    [DESIGN] Define notes format
                                   [EXECUTE] Write release notes
                                   [EXECUTE] Tag v0.0.1
                                   [EXECUTE] Publish GitHub Release
```

Each layer answers a different question:

| Command | Layer | Question |
|---|---|---|
| `tw-flow ponder` | Operational | What's pending right now? |
| `tw-flow roadmap` | Ledger | Where are we in the project arc? |
| `tw-flow status` | Operational | What's the focused plan doing? |

### Link Mechanism

Phases link to operational inis via the `operational_ini` UDA on the phase task.
This allows structured lookups and live status fetching during render.

When `tw-flow roadmap` renders a phase, it follows `operational_ini` and displays
the current ini state inline:

```
[IN PROGRESS] Python Foundation
  → release-0.0.1      ●  Pending: 5 | Active: 0
  → tw-flow-backlog    ✓  Shipped 2026-04-02
  → tw-flow-visibility ✓  Shipped 2026-04-02

[NEXT] Go Rewrite
  → go-rewrite         💤 Backlog

[FUTURE] jacazul-server
  (no ini linked yet)
```

### Initialization Signal

No extra files. Roadmap is considered initialized when a plan named
`{project}-roadmap` exists in Taskwarrior. Bootstrap detects this and
conditionally loads the `jacazul-manager` skill. Framework selection
(Jacazul/OKR/Shape Up/SAFe Lite/Custom) is stored as an annotation on
the roadmap plan root task.

---

## tw-flow ship

Marks a phase as `shipped`. In the POC, no external verification —
just transitions the phase task to `phase:shipped`.

```bash
tw-flow ship <phase-uuid>
```

Broker-based artifact verification (ticket closed, git tag, CI green)
is out of scope for the POC — tracked in `broker-abstraction` ini.

### Shipped Classification Rule

An ini is considered `shipped` when it has **zero pending tasks**,
regardless of the completed/discarded ratio. One done task and 99
discarded = shipped. The delivery happened.

---

**Status:** Design in progress — `roadmap-engine` plan, ticket #39
**Last Updated:** 2026-04-03
