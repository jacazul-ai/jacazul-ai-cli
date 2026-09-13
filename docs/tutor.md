# Tutors

Guide for learning a language with Jacazul: the shared `tutor` core, the
per-language tutors, and the expert each tutor is paired with.

## Trigger → Action

### When you want to learn a language

Say so in plain words ("me ensina Rust", "teach me Go", "tutorial", "quero
aprender"). The engine activates three skills together:

- `tutor`: the shared teaching contract;
- `<lang>-tutor`: the curriculum and guardrails for that language;
- `<lang>-expert`: the technical authority for that language.

The tutor decides how and when to teach. The expert decides what is true. No
skill activates another; the engine activates all three directly.

Available pairs:

| Tutor | Expert | Curriculum |
|---|---|---|
| [`rust-tutor`](../skills/rust-tutor/SKILL.md) | `rust-expert` | Toolchain, foundations, ownership, production Rust |
| [`go-tutor`](../skills/go-tutor/SKILL.md) | `go-expert` | Module shape, foundations, idiomatic design, production Go |
| [`python-tutor`](../skills/python-tutor/SKILL.md) | `python-expert` | Environment, foundations, legacy reading and modernization, idiomatic design, production Python |
| [`zig-tutor`](../skills/zig-tutor/SKILL.md) | `zig-expert` | Toolchain and build shape, foundations, allocators and ownership, comptime, production Zig with std.Io |
| [`php-tutor`](../skills/php-tutor/SKILL.md) | `php-expert` | Runtime and project shape, foundations, legacy reading and migration, modern PHP, production PHP |

### When the tutor asks calibration questions first

That is the contract. Before any curriculum, initiative, or task, the tutor
establishes your engineering level, languages and memory-management
background, prior exposure, objective, pace, environment, and preferred mode.
Answers already present in session memory or task notes are not asked again.
Confirm the summarized baseline and the curriculum follows from it.

### When you want comparisons with a language you know

Tell the tutor which bridge helps. Comparisons come from your
memory-management background (GC, RAII, manual, scripting) and are bridges,
never claims that the target language is another language.

### When the tutor says the expert is not active

The tutor stops instead of teaching from memory. Activate the paired expert
(or ask the engine to) and continue.

### When a project has its own lesson rules

Lesson size, topic per part, and comparison languages defined in the target
project's `AGENTS.md` win over the tutor defaults.

### When you want to add a tutor for another language

1. Add `skills/<lang>-expert/` first; a tutor without an expert cannot teach.
2. Add `skills/<lang>-tutor/SKILL.md` with only a `Pairing` section, the
   language bridges, the curriculum progression, guardrails, and references.
   The method lives in [`skills/tutor/SKILL.md`](../skills/tutor/SKILL.md).
3. Register the pair in the tutor core's language list and in the engine
   templates under `jacazul/hatch/templates/`, then regenerate with
   `jacazul-hatch --target all`.

See the [skills index](skills/README.md) for the full list.
