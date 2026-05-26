# pi-jacazul-line

Use `jacazul-pi` when you want Pi to show Jacazul workflow state directly in the footer.

## I want to see my Jacazul state inside Pi

Run Pi through the Jacazul wrapper:

```bash
jacazul-pi
```

On startup, the Pi bootstrap links the production footer extension from
`extensions/pi/jacazul-line.ts` into Pi's global extension discovery directory:

```text
~/.pi/agent/extensions/
```

Pi can then load or reload the footer extension with its normal extension flow.
Diagnostic Pi probes may also live under `extensions/pi/`, but they are not
linked automatically; load them explicitly only while investigating.

If Pi is already running, use:

```text
/reload
```

## I want to know what the footer shows

`pi-jacazul-line` is a multi-line dashboard footer, not a strict lualine clone.
It avoids powerline separators by default because multi-line layouts need clear
rows more than decorative segment arrows.

The footer uses the `PROJECT_ID` exported by the Jacazul bootstrap. The bootstrap
is responsible for resolving the current project from the launch cwd before Pi
starts.

The footer prioritizes:

| Row | Shows |
|---|---|
| Workflow | Crocodile marker with `JACAZUL_MODE`, then `PROJECT_ID` |
| Focus | Focus label qualified as `(independent)` when session-scoped, focused plan, plus short task UUID and task description when present |
| Location/Git | Current path, normal Git repository, or linked worktree/common Git identity |
| Runtime | Pi model, thinking level, context usage, tokens, cache, and cost |

## I want to understand task descriptions

Focused task descriptions are resolved through the project-aware Taskwarrior
wrapper:

```text
taskp <uuid> export
```

The extension keeps a short in-memory cache and redraws the footer when the
description resolves. It does not read Taskwarrior storage internals directly,
because Jacazul may run against older Taskwarrior data files or newer
Taskwarrior 3/taskchampion storage. `taskp` is the compatibility boundary.

`taskp` is invoked with the current `PROJECT_ID`, so task lookup stays inside the
active project's Taskwarrior silo.

## I want to understand focus scope

When `JACAZUL_SESSION_ID` points to an independent session focus file, the
focus label becomes `focus (independent)`. Global focus does not add extra text.

This makes it visible when the current Pi session is using an isolated focus
without spending space on the workflow row.

## I want to change the visual style

The MVP style is dashboard-first:

```text
🐊 COUNSELOR | jacazul-ai_jacazul-ai-cli
🎯 focus (independent) | pi-lualine-footer-extension | aeab3350 [DESIGN] Design Pi lualine-style custom footer extension
 worktree | ~/.bare/jacazul-ai-cli | tw-flow-to-go(branch)
🤖 | gpt-5.5 · medium · ctx 23.3%/272k | ↑65k ↓2.1k R170k $0.471
```

Future style variants can add a single-line lualine mode, but the default is
optimized for readable workflow state.
