# Shell Expert Skill

Guide for the bash-expert skill: POSIX `sh` and bash scripting with
dialect detection, a pitfall census, honest `set -e` rules, portability
across the shells a script will actually meet, and idempotent setup
scripts.

## Trigger → Action

### When you touch any shell script

Run `sh-mode <root>` first. It names the dialect of the tree and of each
file, and the minimum bash a file implies, without needing `shellcheck`:

```text
🐊 SH_MODE: bash (source: scan, 43 scripts)
  - bash: 43 files
  - scripts/bootstrap/persona: needs bash 4.0 (${var^^} / ${var,,} (bash 4.0))
```

| Mode | Meaning | What the expert does |
|---|---|---|
| `portable` | `#!/bin/sh`, POSIX only | Stays POSIX: `[ ]` with `=`, `printf`, no arrays, no `[[`. |
| `bash` | `#!/usr/bin/env bash` with a minimum version | Uses bash features up to the minimum the project supports. |
| `mixed` | bashisms under `#!/bin/sh`, or features above the minimum | Repairs: fixes the shebang or removes the constructs, one file per commit. |

Override with `JACAZUL_SH_MODE=portable|bash|mixed`. `sh-mode --files`
lists every script with its dialect and implied bash version.

### When you want to know how bad it is

```bash
sh-census <root>          # pitfall families by kind
sh-census --lint <root>   # plus bash -n / sh -n with the declared shell
```

```text
kind          count  files  label
security          3      3  rm -rf on a variable without :? guard
security         65     21  unquoted expansion as argument (heuristic)
correctness      55     12  == inside [ ] (POSIX test uses =)
portability      42     42  hardcoded #!/bin/bash (use /usr/bin/env bash)
maintenance       3      3  mktemp without trap cleanup
total: 240 across 13 families
```

The security and correctness families are the ones to drive to zero on
touched scripts; portability and maintenance are the backlog.

### When `set -e` did not save you

It is defined not to fire in pipelines without `pipefail`, in `if`,
`while`, `&&` and `||` conditions, inside a function called from a
condition, in `local x=$(cmd)`, and `(( x++ ))` exits when the result is
zero. The [playbook](../skills/bash-expert/PLAYBOOK.md) has the table and
the fix for each row; the expert adds explicit checks there instead of
trusting the flag.

### When the script works on your machine and breaks on the server

Your `sh` is probably bash (Fedora, macOS); the server's is dash (Debian,
Ubuntu) or busybox (Alpine). `sh-mode` reports the file as `mixed` when a
`#!/bin/sh` script uses `[[`, arrays, `local`, `source`, `echo -e` or
`${var//}`. Fix the shebang or the constructs; test on the oldest target.

### When you write a setup or bootstrap script

Idempotent and quiet: verify silently, log on state change, `ln -sfn`
for links, `mkdir -p`, check-then-act, `DEBUG=true` for verbosity,
`DRY=true` to walk the decision path without changing anything. The
expert follows the repository's own logging manifesto.

### When you ask for a shell code review

Findings use the shared [`code-review` scale](../skills/code-review/SKILL.md)
with the scenarios in
[`skills/bash-expert/CODE-REVIEW.md`](../skills/bash-expert/CODE-REVIEW.md):
unquoted expansions, parsed `ls`, unchecked `cd`, `rm -rf` on an
unguarded variable, `eval`, `curl | sh`, `sudo` in scripts, `set -e`
trusted where it does not fire, bashisms under `sh`, GNU-only flags.

### When you want to learn shell

Ask for a tutorial. The engine activates `tutor`, `bash-tutor` and
`bash-expert` together; see [Tutors](tutor.md). Every example is parsed
with `bash -n` and run in a scratch directory on your target shell before
it is shown.

## Best Practices

1. Name the dialect and the oldest supported interpreter before the first
   edit.
2. Quote every expansion; `${var:?}` and `--` before anything destructive.
3. `bash -n` on every touched script; never skip it.
4. `set -euo pipefail` plus explicit checks where the table says `-e` is
   silent.
5. Setup scripts run twice without harm and say nothing unless they
   change something.

---

**Version:** 1.0.0
**Last Updated:** 2026-09-14
