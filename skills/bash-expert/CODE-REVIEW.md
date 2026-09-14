# Shell Code Review Directives

Shell-specific review scenarios: the code shape to avoid, the runtime
sequence it creates, what can fail, and the evidence or correction a
reviewer should require.

The review method, scenario format, tracks, areas, technical levels,
advisories, and evidence labels are owned by the shared
[Code Review skill](../code-review/SKILL.md). This file adds shell
scenarios only and never redefines those labels. Before judging a script,
run `sh-mode <root>` to know its dialect and minimum interpreter and
`sh-census <root>` to know which pitfall families it already carries.

Scenarios are grouped by [track](../code-review/SKILL.md#tracks). The track
describes the learning path, not the severity: a Foundations pattern can
still create a critical security or availability incident. A review
comment must be tied to the repository's contract or a credible failure
mode.

Nothing compiles a shell script. `bash -n` proves it parses; everything
else is review: quoting, `set -e`'s exceptions, filenames as input,
destructive commands on possibly empty variables, and the shell the script
will actually meet.

## Mode-aware review

- **portable:** any bashism is `BLOCKER` / `FIX-NOW` / `CONTRACT`: it
  parses on the author's bash and fails on dash.
- **bash:** a feature above the minimum bash the project supports is
  `WARNING` / `FIX-NOW` / `CONTRACT` (macOS bash 3.2 is the usual floor).
- **mixed:** the shebang and the content disagree; the fix is a decision
  (change the shebang or the constructs), `WARNING` / `FIX-NOW` /
  `POLICY`.

## Worked example (full form)

```bash
#!/bin/bash
set -e
cd $1
for f in $(ls *.log); do
    rm -rf $TMP_DIR/$f
done
```

**Context:** A cleanup helper called from cron with a directory argument;
`TMP_DIR` comes from the environment.

**Runtime sequence:** `cd $1` word-splits the argument; with an empty or
missing argument `cd` goes to `$HOME` and `set -e` does not stop it
because `cd` succeeded. `$(ls *.log)` splits on spaces and newlines, so a
file named `a b.log` becomes two words. With `TMP_DIR` unset, the
expansion is empty and the command is `rm -rf /a.log`; with a filename of
`..`-shaped garbage, worse.

**Failure modes:** Wrong directory cleaned; files with spaces skipped or
misnamed; deletion outside the intended tree; `set -e` provides no
protection on any of these paths.

**Review directive:** Quote every expansion; check `cd`; iterate with a
glob; guard destructive variables with `${var:?}` and `--`; never parse
`ls`.

**Acceptable correction:**

```bash
#!/usr/bin/env bash
set -euo pipefail
dir=${1:?usage: cleanup <dir>}
cd -- "$dir" || exit 1
for f in ./*.log; do
    [ -e "$f" ] || continue
    rm -rf -- "${TMP_DIR:?}/$f"
done
```

Add a test with a filename containing a space and one run with `TMP_DIR`
unset (expect exit 1, nothing removed).

**Classification:** `BLOCKER` / `FIX-NOW` / `SECURITY` / `TRACE`.

## Foundations: correctness

### 1. Unquoted expansions

**Problem:** `$var`, `$(cmd)`, `$@`, `${arr[@]}` without double quotes
outside `[[ ]]` and `(( ))`.

**What can happen:** Word splitting on whitespace, glob expansion on `*`
and `?`, arguments with spaces broken, empty expansions vanishing so the
next argument shifts position.

**Safer shape:** Quote everything; `"$@"` for arguments; `${var:-}` when
empty is acceptable.

### 2. `echo` with flags or escapes

**Problem:** `echo -e`, `echo -n`, `echo "$var"` where `$var` may start
with `-` or contain backslashes.

**What can happen:** Flags printed literally on dash, escapes interpreted
or not depending on the shell and `xpg_echo`, a value of `-n` swallowed.

**Safer shape:** `printf '%s\n' "$var"`; `printf '%b'` when escapes are
wanted.

### 3. `read` without `-r`

**Problem:** `read line` or `while read line`.

**What can happen:** Backslashes are interpreted and dropped; leading and
trailing whitespace trimmed unless `IFS=`.

**Safer shape:** `while IFS= read -r line; do ...; done < file`.

### 4. `==` and unquoted variables inside `[ ]`

**Problem:** `[ $a == $b ]`, `[ -n $var ]`.

**What can happen:** `==` is not POSIX (dash: `unexpected operator`); an
empty `$var` makes `[ -n ]` true; a value starting with `-` becomes an
operator.

**Safer shape:** `[ "$a" = "$b" ]`, `[ -n "$var" ]`; `[[ ]]` in bash-only
scripts.

### 5. Arithmetic and `let`

**Problem:** `let x=x+1`, `expr $x + 1`, `$[ ]`, `(( x++ ))` as the last
line under `set -e`.

**What can happen:** `expr` spawns a process and fails on non-integers;
`let` is bash only; `(( x++ ))` returns 1 when the result is 0 and `set -e`
exits.

**Safer shape:** `x=$(( x + 1 ))`; `(( x++ )) || true` when the value may be
zero under `-e`.

### 6. Backticks and nesting

**Problem:** `` `cmd` `` especially nested or containing quotes.

**What can happen:** Quoting rules differ; nesting needs escaping; hard to
read.

**Safer shape:** `$( )`, which nests and quotes naturally.

### 7. Parsing `ls`, `find` without `-print0`, `for` over command output

**Problem:** `for f in $(ls)`, `for f in $(find . -name '*.log')`.

**What can happen:** Filenames with spaces or newlines split; globs
expand; `ls` output formatting varies.

**Safer shape:** `for f in ./*.log` with `[ -e "$f" ] || continue`;
`find ... -print0 | while IFS= read -r -d '' f`; `find -exec`.

### 8. `$?` checked after the wrong command

**Problem:** `cmd; echo done; if [ $? -eq 0 ]`.

**What can happen:** `$?` is the status of `echo`.

**Safer shape:** `if cmd; then` or `if ! cmd; then`; capture immediately
(`status=$?`) when the value must be kept.

### 9. Missing `--` before variable arguments

**Problem:** `rm "$file"`, `grep "$pattern" "$file"`, `git checkout "$ref"`.

**What can happen:** A value starting with `-` becomes an option: `-rf`,
`--help`, `-i`.

**Safer shape:** `rm -- "$file"`; `grep -e "$pattern" -- "$file"`; `./`
prefix for paths.

### 10. `cd` without a check

**Problem:** `cd "$dir"` followed by relative-path commands.

**What can happen:** On failure the script continues in the previous
directory; with `set -e` inside a function called from a condition it
still continues.

**Safer shape:** `cd -- "$dir" || exit 1`; or `( cd -- "$dir" && cmd )` so
the change does not leak.

## Boundaries: errors, lifecycle, portability

### 11. `set -e` trusted where it does not fire

**Problem:** Pipelines without `pipefail`, commands in `if`/`while`/`&&`/
`||`, functions called in conditions, `local x=$(cmd)`.

**What can happen:** Failures pass silently; the author believes the
script is guarded.

**Safer shape:** `set -euo pipefail` plus explicit checks where `-e` is
defined not to apply; `local x` then `x=$(cmd)`; see the playbook's table.

### 12. Temporary files without `trap`

**Problem:** `tmp=$(mktemp)` and no `trap 'rm -f "$tmp"' EXIT`.

**What can happen:** Files left behind on error or interrupt; `/tmp` fills
on servers.

**Safer shape:** `trap` on `EXIT` (and `INT TERM` when children must be
killed); one cleanup function.

### 13. Directory changes and state that leak

**Problem:** `cd` in a function without a subshell; `export` of variables
the caller did not ask for; `set` options changed and not restored in
sourced files.

**What can happen:** Callers run in the wrong directory; environment
polluted; a sourced library turns on `-e` for the caller.

**Safer shape:** Subshells for `cd`; `local`; sourced files do not change
shell options.

### 14. Subshells losing variables

**Problem:** `cmd | while read -r line; do count=$((count+1)); done` then
using `count`.

**What can happen:** The loop runs in a subshell (bash); `count` is
unchanged outside.

**Safer shape:** `while ... done < <(cmd)` (bash), a here-string, or
`shopt -s lastpipe`; in sh, redirect from a file.

### 15. Bashisms under `#!/bin/sh`

**Problem:** `[[`, arrays, `local` (POSIX), `source`, `${var//}`,
`echo -e` in a script that declares `sh`.

**What can happen:** Works on Fedora and macOS where `sh` is bash;
parse error on Debian, Ubuntu, Alpine.

**Safer shape:** Change the shebang to bash when bash is required, or
rewrite in POSIX; `sh-mode` reports the file as `mixed` until fixed.

### 16. Features above the minimum bash

**Problem:** `mapfile`, `declare -A`, `${var^^}`, `${var@Q}` on a project
that supports macOS's bash 3.2.

**What can happen:** `command not found` or `bad substitution` on the
oldest supported machine.

**Safer shape:** Declare the minimum; `sh-mode --files` shows what each
script implies; provide fallbacks or raise the floor deliberately.

### 17. GNU-only coreutils flags

**Problem:** `sed -i`, `readlink -f`, `date -d`, `find -printf`, `grep -P`
in scripts that run on macOS or BSD.

**What can happen:** Errors or silent differences on BSD tools.

**Safer shape:** Portable alternatives (`cd`/`pwd -P`, `perl -pi`, `date
-j` guards) or an explicit "GNU coreutils required" check.

### 18. `which`, `type`, and optional tools

**Problem:** `which tool` to detect availability; a tool assumed present.

**What can happen:** `which` is not POSIX and its exit codes vary; the
script fails mid-way with a confusing error.

**Safer shape:** `command -v tool >/dev/null 2>&1 || { echo "..." >&2; exit 1; }`
at the top, with the actionable message.

### 19. Sourced files with side effects

**Problem:** A library file that runs commands, changes options, or
`exit`s when sourced.

**What can happen:** Sourcing terminates the caller's shell; options leak.

**Safer shape:** Definitions only when sourced; `return` not `exit`;
guard with `[ "${BASH_SOURCE[0]}" = "$0" ] && main "$@"`.

### 20. Non-idempotent setup

**Problem:** `mkdir` without `-p`, `ln -s` without `-fn`, appending to a
file on every run, `rm` of a link target.

**What can happen:** Second run fails or duplicates; a wrong link is
never corrected; user data removed.

**Safer shape:** Check-then-act with a log line only on change; `ln -sfn`;
`grep -q || printf >>`; never remove what you did not create.

## Systems: security, contracts, and process

### 21. `eval` and command strings

**Problem:** `eval "$cmd"`, `bash -c "$cmd $arg"`, building commands as
strings.

**What can happen:** Command injection through any input reaching the
string; quoting bugs that only appear with special characters.

**Safer shape:** Argument arrays (`args=(...)`; `"${args[@]}"`), `case`
dispatch, functions; `printf %q` only as a last resort.

### 22. `curl | sh` and unverified downloads

**Problem:** `curl -s URL | bash`, `wget -O- URL | sh`, `sudo` variants.

**What can happen:** Arbitrary code execution from a compromised host or
a partial download; no chance to review.

**Safer shape:** Download to a file, verify a checksum or signature, read
it, then run; pin versions.

### 23. Destructive commands on possibly empty variables

**Problem:** `rm -rf "$dir/"`, `rm -rf $PREFIX/*`, `chown -R user $path`.

**What can happen:** `/` or the current directory targeted when the
variable is empty or unset; globs expanding to everything.

**Safer shape:** `${var:?}`; `--`; assert the path is inside the expected
root (`case "$dir" in /expected/*) ;; *) exit 1;; esac`); `DRY=true`
paths for anything destructive.

### 24. `sudo` inside scripts

**Problem:** Scripts that call `sudo` for individual commands or re-exec
themselves as root.

**What can happen:** Password prompts in automation; privilege applied to
more than intended; `sudo` environment differences.

**Safer shape:** The caller escalates; the script checks `[ "$(id -u)" -eq 0 ]`
and tells the user what to do.

### 25. Secrets exposed

**Problem:** Tokens on the command line, `set -x` around secret handling,
secrets in log lines or `DEBUG` output, world-readable temp files.

**What can happen:** Visible in `ps`, shell history, CI logs, `/tmp`.

**Safer shape:** Read from files with `umask 077` or from the environment;
`set +x` around secret handling; redact before logging; pass through
stdin or files, not arguments.

### 26. Exit codes as an API

**Problem:** `exit 1` for every failure, `exit 0` after an error message,
`exit` from a function.

**What can happen:** Callers cannot distinguish usage errors from runtime
failures; automation treats failures as success.

**Safer shape:** Documented codes (`2` usage, `sysexits` when adopted);
`return` in functions, `exit` in `main`; stderr messages with the next
action.

### 27. Signal handling and children

**Problem:** Long-running scripts without `INT`/`TERM` traps; background
jobs orphaned on exit; `wait` missing.

**What can happen:** Ctrl-C leaves workers running; cleanup never runs;
zombie processes.

**Safer shape:** `trap 'kill -- -$$' INT TERM` or per-job `kill "$pid"`;
`wait` for every background job; `EXIT` trap for cleanup.

### 28. Locking and concurrency

**Problem:** Cron jobs that may overlap; scripts that write shared files
without a lock.

**What can happen:** Corrupted state; duplicated work.

**Safer shape:** `flock -n "$lock" cmd` on Linux, `mkdir "$lockdir"` as a
portable atomic lock, with cleanup in the `EXIT` trap.

## Cross-cutting directives

### Dialect declared versus dialect used

**Avoid:** Reviewing only the content or only the shebang.

**Review directive:** Every shell review names the declared shell, the
constructs used (`sh-mode --files`), and the oldest interpreter the
project supports; a mismatch is a finding even when the script works on
the reviewer's machine.

**Classification:** `WARNING` / `FIX-NOW` / `CONTRACT` / `TOOL`; `BLOCKER`
when the script runs in production on the mismatched shell.

### `set -e` as a substitute for checks

**Avoid:** Accepting "it has `set -e`" as evidence that failures stop the
script.

**Review directive:** Require explicit handling at each place the table in
the playbook lists; treat `set -euo pipefail` as a default, not a proof.

**Classification:** `WARNING` / `FIX-OR-TECH-DEBT` / `CORRECTNESS` / `TRACE`.

## Automated review baseline

The verification commands are defined once in
[`SKILL.md`](SKILL.md#-conventional-verification-baseline).
Repository-configured gates always take precedence.

Evidence scope:

- `bash -n` / `sh -n` / `dash -n`: parse only, with the declared shell.
- `sh-mode` and `sh-census`: dialect and pitfall heuristics; evidence, not
  proof.
- `shellcheck`: the reference analyzer for most scenarios above, when the
  project adopts it; `shfmt` for formatting.
- `bats` or the project's runner: behavior verification; `DRY=true` runs
  as decision-path tests.

## Source index

- [Bash Reference Manual](https://www.gnu.org/software/bash/manual/) —
  expansions, `set` options, traps.
- [POSIX Shell Command Language](https://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html)
  — what portable scripts may use.
- [Bash Pitfalls](https://mywiki.wooledge.org/BashPitfalls) — the
  canonical catalog of the Foundations scenarios.
- [BashFAQ 105: Why doesn't set -e do what I expected?](https://mywiki.wooledge.org/BashFAQ/105)
- [ShellCheck wiki](https://www.shellcheck.net/wiki/) — SC codes for each
  scenario.
- [Filenames and Pathnames in Shell](https://dwheeler.com/essays/filenames-in-shell.html)
- [sysexits(3)](https://man.freebsd.org/cgi/man.cgi?query=sysexits) — exit
  code conventions.
