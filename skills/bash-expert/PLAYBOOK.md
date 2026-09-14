# Shell Engineering Playbook

Implementation guidance for writing shell scripts that are correct under
`set -e`'s real rules, safe with hostile filenames and input, portable
across the shells and coreutils they will actually meet, idempotent, and
quiet by default. This file answers **how to build the change**.
Scenario-based review directives live separately in
[`CODE-REVIEW.md`](CODE-REVIEW.md).

These are defaults, not automatic repository policy. Read the shebangs,
`.shellcheckrc`, `.editorconfig`, CI, and the project's conventions
(logging, `DEBUG`/`DRY` flags, exit codes) before adopting an optional
gate or changing an established contract.

## Before writing code

1. Run `sh-mode <root>` and name the dialect: portable, bash, or mixed.
   Then name the minimum interpreter the script must run on (dash on
   Debian, busybox on Alpine, bash 3.2 on macOS, bash 5 on Linux).
2. Read the shebang of the file you are editing and stay inside its
   dialect; a bashism in a `#!/bin/sh` file is a parse error on the next
   Debian box.
3. Read the project's conventions: how it logs, how it reports errors,
   whether it is silent by default, what `DEBUG=true` and `DRY=true`
   mean, which exit codes callers depend on.
4. Identify trust boundaries: arguments, environment, filenames, `stdin`,
   command output you parse, anything fetched over the network.
5. Decide idempotence: what a second run does, what a run after a partial
   failure does, what cleanup runs on every exit.

## Mode: portable (POSIX sh)

- `#!/bin/sh`; `[ ]` with `=` (never `==`), no arrays, no `local` (dash
  has it, POSIX does not), no `[[`, no `<( )`, no `${var//}`, no `$'...'`,
  no `source` (use `.`), no `echo -e` or `echo -n` (use `printf`).
- Arithmetic with `$(( ))`; string tests with `case`; loops over
  positional parameters with `"$@"`.
- Test under dash or busybox `sh` when the target is Debian or Alpine;
  `bash --posix` is not the same shell.

## Mode: bash

- `#!/usr/bin/env bash` unless the project pins `/bin/bash` on purpose.
- Declare the minimum bash the script needs and check it when it
  matters (`(( BASH_VERSINFO[0] >= 4 ))`); `sh-mode` prints the minimum
  implied by the features used.
- `[[ ]]` for tests, arrays for lists, `local` in every function,
  `mapfile -t` to read lines, `printf -v` to build strings.

## Mode: mixed (repair)

A `#!/bin/sh` file using bashisms, or a bash file using zsh-isms, works on
the author's machine and breaks elsewhere. Either change the shebang to
what the code needs (usually the honest fix) or remove the constructs the
declared shell lacks. One commit per file, `sh-mode` clean after it.

## Quoting and expansion

- Double-quote every expansion: `"$var"`, `"$(cmd)"`, `"$@"`, `"${arr[@]}"`.
  Unquoted expansions word-split and glob; `$@` unquoted loses arguments
  with spaces.
- `"$@"` for all arguments, never `$*` unless you want one string.
- `${var:?message}` to fail on unset or empty; `${var:-default}` for
  defaults; `${var:?}` before any `rm -rf "$var/..."`.
- `--` before paths and arguments that may start with `-`:
  `rm -- "$file"`, `grep -- "$pattern" "$file"`.
- `printf '%s\n' "$x"` instead of `echo "$x"`: `echo` eats `-n`, `-e`,
  and interprets backslashes on some shells.
- Filenames can contain spaces, newlines, and leading dashes; never parse
  `ls`; iterate with globs (`for f in ./*.log`) or
  `find ... -print0 | while IFS= read -r -d '' f`.
- `read -r` always; `IFS=` when leading and trailing whitespace matters.

## Errors and exit codes

`set -euo pipefail` is a good default and a bad guarantee. What `-e` does
not catch, and the honest fix:

| Case | `-e` behavior | Fix |
|---|---|---|
| Command in a pipeline (not last) | ignored without `pipefail` | `set -o pipefail` |
| Command inside `if`, `while`, `until`, `&&`, `\|\|`, `!` | ignored by design | check explicitly |
| Function called in a condition | `-e` disabled inside the function | return codes, `\|\| return` |
| Command substitution in an assignment `x=$(cmd)` | exit status of the assignment is the command's, but `local x=$(cmd)` masks it | separate `local x` and `x=$(cmd)` |
| Subshell `( cmd )` | inherits `-e` but the parent continues after it fails only if checked | `( ... ) \|\| exit` |
| Arithmetic `(( x == 0 ))` when result is zero | exits with status 1 | `(( x == 0 )) \|\| true` or `if (( ... ))` |

- Exit codes are the contract: `0` success, `1` generic failure, `2`
  usage, `64`–`78` from `sysexits` when the project uses them; document
  them in the header.
- Errors go to stderr with an actionable message (Error as Prompt): what
  failed, what the caller should do next.
- `trap cleanup EXIT` for temporary files and partial state; `trap` on
  `INT TERM` when the script owns children; `mktemp` for every temp
  path.
- Never `cd` without `|| exit`; prefer `cd -- "$dir" || return 1` inside
  functions, or subshells `( cd -- "$dir" && cmd )` to avoid leaking the
  directory change.
- Check `command -v tool >/dev/null 2>&1` before relying on optional
  tools; `which` is not standard.

## Functions and structure

- `main "$@"` at the bottom; functions above; `local` for every variable
  in a function; `readonly` for constants.
- `return` from functions, `exit` from `main`; a function that calls
  `exit` is untestable.
- Small functions with one job; long pipelines get a name.
- Use `getopts` for flags; document usage in a `usage()` function that
  prints to stderr and exits `2`.

## Portability

- GNU versus BSD coreutils: `sed -i` (BSD needs `-i ''`), `readlink -f`
  (macOS before 12.3 lacks it; use `cd`+`pwd -P` or `realpath` when
  available), `date -d` versus `date -v`, `mktemp` template rules,
  `find -printf` is GNU only.
- `#!/usr/bin/env bash` finds the user's bash (Homebrew) instead of
  macOS's 3.2 at `/bin/bash`.
- `command -v`, not `which`; `printf`, not `echo -e`; `$( )`, not
  backticks (nesting and quoting).
- `[ "$a" = "$b" ]` in sh; `==` is bash only inside `[ ]`.
- Test on the oldest target shell, not the newest.

## Idempotence and logging

- Setup scripts are re-runnable: create if missing, relink if wrong,
  leave alone if right. Verification of existing state is silent unless
  `DEBUG=true`; state changes are logged ("Creating directory X").
- `DRY=true` runs the whole decision path and prints what would change
  without changing it.
- Symlinks: `ln -sfn` to replace atomically; check `readlink` before
  relinking; never `rm -rf` the target of a link you did not create.
- Locks for scripts that must not overlap (`flock` on Linux, `mkdir` as a
  portable lock).

## Security boundary

Treat external input as hostile by default:

- no `eval` on strings that contain input; build argument arrays instead;
- no `curl ... | sh`; download, verify (checksum or signature), then run;
- no `sudo` inside scripts; the caller escalates, the script does not;
- `${var:?}` before destructive paths, `--` before variable arguments,
  quotes everywhere;
- temp files from `mktemp`, never predictable names in `/tmp`; `umask`
  when files hold secrets;
- secrets never on the command line (`ps` shows them) nor in `set -x`
  output; read them from files or the environment and redact logs;
- `IFS` reset to default in scripts that accept environment from callers.

## Tests and validation

- `bash -n` / `sh -n` parse every script on every change; it is the
  cheapest gate and never skipped.
- `shellcheck` and `shfmt` when the project declares them (`.shellcheckrc`,
  `.editorconfig`, CI); their findings are evidence, not policy, until the
  project adopts them.
- `bats` for behavior tests when present; otherwise a plain bash runner
  that calls the script with fixtures: a temporary `HOME`, fake
  executables on a prepended `PATH`, captured stdout and stderr, asserted
  exit codes.
- `DRY=true` runs are tests: the decision path executes end to end without
  touching the system.
- Process isolation for environment-sensitive behavior: run the script in
  a child with an explicit environment (`env -i` plus what it needs).

Run repository-configured checks first. If no stronger gate exists, use
the baseline from [`SKILL.md`](SKILL.md#-conventional-verification-baseline)
and label it as such.

## Version awareness

- bash 3.2 (macOS default): no `mapfile`, no associative arrays, no
  `${var^^}`, no `|&`, no `;;&`.
- bash 4.0: associative arrays, `mapfile`, case conversion, `coproc`.
- bash 4.2: `test -v`. 4.3: namerefs, negative array indices.
- bash 4.4: `${var@Q}`. 5.0: `EPOCHSECONDS`. 5.1: `${var@U}`.
- dash: POSIX plus `local`; no arrays, no `[[`.
- busybox `ash`: POSIX subset; check each builtin.

`sh-mode --files` prints the minimum bash each script implies.

## References

- [Bash Reference Manual](https://www.gnu.org/software/bash/manual/)
- [POSIX Shell Command Language](https://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html)
- [ShellCheck wiki](https://www.shellcheck.net/wiki/)
- [Bash Pitfalls (Greg's Wiki)](https://mywiki.wooledge.org/BashPitfalls)
- [BashFAQ](https://mywiki.wooledge.org/BashFAQ)
- [Shell Code Review Directives](CODE-REVIEW.md)
