## 🧭 Reference Router

The triggered protocols live in `references/`, next to this file. When a
trigger below fires, read the reference before acting; it holds the full
procedure. Every reference is one read, with no further references inside.

| Trigger | Read |
|---|---|
| `onboard`, `cuida`, `rala`, `avia`, `atividade`; a status, ponder, roadmap or project-overview request; presenting `tw-flow status` or `tw-flow ponder` output | `references/onboard.md` |
| A pending session note, `tw-flow session resume`, a handoff question; dump phrases ("dá um dump", "salva o estado", "vou fechar", "contexto tá zoado", "freeze state", "lost track") | `references/session.md` |
| A `[GUIDE]` task or request; naming a mode in the user's language (MODE vs modo) | `references/modes.md` |
| The session language is not anchored yet, or the user keeps writing in another language | `references/language.md` |
| `i&d`, `ied`, `consensus review`, `revc`, `crev`, or any other shorthand not defined in this hub | `references/glossary.md` |
| A `tw-flow`, `ponder`, broker, hatch or persona command you need the syntax for | `references/onboard.md` (CLI Quick Reference) |

Two triggers act before any read:

- **Focus anchoring** ("foca nisso", "focus on this"): run
  `tw-flow focus ind task <uuid>` as the first action, then continue.
- **Immediate dump** ("dá um dump", "congela o estado", "restart session",
  "contexto tá zoado", "lost track"): run `tw-flow session dump` first, then
  read `references/session.md` to fill in the note.
