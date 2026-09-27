# Proposal: The Go Launcher

**Status:** In progress. The scaffold and the claude parity references are
committed; the harness subcommands are not implemented yet.
**Audience:** Contributors and agents working on the launcher.
**Related:** #113, plan `jacazul-launcher`, `go-expert`, `bash-expert`,
[`tw-flow-session.md`](../tw-flow-session.md).

## What changes for the user

One Go binary, `jacazul`, replaces the per-harness Bash launchers. Each
harness becomes a subcommand:

| Today | With the Go launcher |
|---|---|
| `jacazul-claude` | `jacazul claude` |
| `jacazul-pi` | `jacazul pi` |
| `jacazul-gemini`, `jacazul-gemini-sandboxed` | `jacazul gemini` |
| `jacazul-copilot` | `jacazul copilot` |
| `jacazul-opencode` | `jacazul opencode` |

The old names keep working during the transition as entry points to the
same binary.

## Command shape

```text
jacazul [--dry] [--debug] [--jacazul-session <id>] <harness> [harness args...]
```

- Everything before the harness name belongs to `jacazul`; everything after
  it reaches the harness untouched. The Bash launchers scanned every
  argument for `--jacazul-session` and `--resume`; the Go launcher
  intercepts nothing after the harness.
- `--jacazul-session` selects the Jacazul session, the focus lane that
  carries mission continuity. The harness keeps its own session flags for
  conversation continuity (see [`tw-flow-session.md`](../tw-flow-session.md)).
- `--dry` runs every bootstrap step except the harness launch; `--debug`
  prints what each step does. The `DRY` and `DEBUG` environment variables
  stay honored for compatibility; either source turns the mode on.
- `-v`/`--version` prints the version stamped by the Go toolchain from
  version control (a tag, or a pseudo-version with `+dirty`).

### `--resume` is fixed on the way

Since the Bash launchers were introduced, `jacazul-<harness> --resume`
skips the onboard prompt and drops `--resume` before calling the harness,
so the conversation is never resumed. With the pass-through above,
`--resume` reaches the harness. Whether a resumed conversation still skips
the onboard prompt is an open decision.

## Layout

The layout follows other Go projects of the organization:

```text
cmd/jacazul/main.go      the entry point only
internal/cli/            parser and commands, one file per harness
internal/bootstrap/      one package per bootstrap step
internal/parity/         temporary, test-only (see Parity below)
testdata/parity/         scenario table, capture script, references
```

The Go tree mirrors the Bash one, so each step has a counterpart that is
easy to trace and to hold to parity. Shared and harness-specific steps sit
side by side, as they do in `scripts/bootstrap/`:

| Bash | Go |
|---|---|
| `scripts/jacazul-<harness>` | `internal/cli/<harness>.go` |
| `scripts/bootstrap/<harness>` | `internal/bootstrap/<harness>/` |
| `scripts/bootstrap/project-identity` | `internal/bootstrap/project/` |
| `scripts/bootstrap/environment` | `internal/bootstrap/environment/` |
| `scripts/bootstrap/persona` | `internal/bootstrap/persona/` |
| `scripts/bootstrap/language` | `internal/bootstrap/language/` |
| `scripts/bootstrap/taskwarrior` | `internal/bootstrap/taskwarrior/` |
| `scripts/bootstrap/onboard` | `internal/bootstrap/onboard/` |
| `scripts/bootstrap/python` | removed: no Python on the launch path |
| `scripts/bootstrap/hatch` | the Go hatch (below) |

Shared steps are ported once and reused by every harness command.

- Module `github.com/jacazul-ai/launcher`, ahead of the planned rename of
  the repository to `jacazul-ai/launcher`.
- `go 1.25`, `jessevdk/go-flags`.
- Make targets: `build` (to `bin/jacazul`), `clean`, `fmt`, `go-test`,
  `tidy`, `vet`, `parity`. Until the Python cutoff `make test` stays the
  Python suite and the Go suite runs with `make go-test`; at the cutoff
  `make test` becomes the Go suite.
- CI: `.github/workflows/run_tests.yml` runs `make vet` and `make go-test`
  on Go 1.25 to 1.27 with read-only permissions.

## What moves into Go

The launcher runs no Python. Every step the Bash launchers source or spawn
is ported:

| Step | Today | In Go |
|---|---|---|
| Project identity, `PROJECT_ID` | `bootstrap/project-identity` | computed from the path |
| `JACAZUL_HOME` | forced to `~/.jacazul-ai` in two bootstraps | a preset value wins |
| Session ID | `python3 -c uuid` | generated in Go, or `--jacazul-session` |
| Persona, language | `persona.json`, `language.json`, `jq`/`grep` | read from `project.json` (below) |
| Mode | `JACAZUL_MODE`, default `COUNSELOR` | unchanged: a variable of the running session |
| Taskwarrior data and UDAs | `bootstrap/taskwarrior` | `TASKDATA`/`TASKRC` computed, UDAs injected in Go |
| Python venv | `uv venv` + `uv pip install -e` on every launch | off the launch path |
| Claude settings, skill and extension links | `bootstrap/claude` | merged and linked in Go, honoring `HOSTS` |
| Onboard prompt | `bootstrap/onboard` | rendered from `prompts/onboard.md` plus the active voice |
| Hatch | `jacazul-hatch` (Python) on every launch | the Go hatch, only when content changed (below) |

A Bash `DRY` launch takes about 1.1 s; `uv pip install -e` alone is about
590 ms of it, `jacazul-hatch` about 140 ms and `python3` for the session ID
about 33 ms.

## Per-project configuration

Stable project settings move from environment variables to one file:

```json
// <JACAZUL_HOME>/projects/<PROJECT_ID>/project.json
{ "persona": "arnalbam", "language": { "chat": "pt-br", "data": "en" } }
```

- It absorbs `.task/<PROJECT_ID>/persona.json` and lets a project override
  the global `language.json`.
- Precedence: environment variable, then `project.json`, then the global
  `language.json`, then defaults.
- The file is the source; environment variables stay the transport to the
  harness and the tools it starts.
- Mode is not stored: it describes the running session.
- Migration reads `persona.json` when `project.json` is absent, and
  `jacazul-persona` writes the new file.

## The hatch

The hatch moves to Go and hatches everything hatchable, including skills
owned by other Go projects such as `jacazul-ai/flow`:

- Each provider module exports its hatchable files with `//go:embed`, for
  example `var Hatch embed.FS` over a `hatch/` directory that holds
  `skills/<name>/...`. This repository's own skills become a provider too.
- The launcher imports its providers through `go.mod`, so a skill's version
  is pinned to the version of the module that owns it.
- The hatch writes the files under `JACAZUL_HOME/agents/<harness>/skills/`,
  honoring `HOSTS`. Embedded content cannot be symlinked, so it writes
  copies with a version marker and re-hatches only when the binary's
  content differs, which takes the hatch off the per-launch path.
- Templates render with pongo2, which uses Django template syntax. Today's
  templates are Tornado's: `include` and `{{ variable }}` read the same, and
  Tornado's generic `{% end %}` becomes `{% endif %}`.

Still to settle: `include` with `../` paths and loading from an
`embed.FS` in pongo2, access to modules without a published tag or in
private repositories (`GOPRIVATE`), and the provider contract, which goes
into [`skill-methodology.md`](../skill-methodology.md).

## Workflow engine

`jacazul flow` is the door to the workflow engine
(`jacazul-ai/flow`):

- Until the engine is embedded, `jacazul flow <args...>` passes through to
  the current `tw-flow` with the same arguments, streams and exit code,
  marked for replacement by `flow.Run`.
- `jacazul flow session list` is implemented in Go now. It reads the
  session files directly (focus lane, age, status, handoff note present),
  as `tw-flow session list` does. Sessions stay owned by the workflow
  engine; the launcher only creates or accepts the session ID.

## Parity with the Bash launchers

`DRY=true DEBUG=true` is the observability contract of the Bash launchers:
it shows environment, hatch, skill links and settings without starting the
harness. The Go launcher is held to it:

- `testdata/parity/scenarios.tsv` lists the scenarios; `make parity` (or
  `testdata/parity/capture <harness>`) records each one in a throwaway HOME
  with its own venv, and stores exit code, output, the HOME tree and the
  settings files, with machine paths replaced by placeholders.
- `internal/parity` checks the references and compares them with
  `jacazul --dry --debug <harness>`.
- Both are temporary and leave at the cutoff.

## Transition and cutoff

1. Harness subcommands land one by one, each checked against its parity
   references.
2. The legacy `jacazul-<harness>` names route to the Go binary.
3. At the cutoff the Bash launchers, `testdata/parity`, `internal/parity`
   and the `parity` target are removed, and `make test` runs the Go suite.

## Open decisions

- Root of `projects/`: `~/.jacazul-ai/projects` (inside `JACAZUL_HOME`) or
  another directory.
- Whether a resumed conversation still skips the onboard prompt.
- Whether the Bash launchers call the Go steps during the transition, so
  each rule has one source, or keep their own copies until the cutoff.
