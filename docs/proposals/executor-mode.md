# Proposal: EXECUTOR Mode

**Status:** Proposal, not implemented. Recorded while porting the launcher;
worked on after it.
**Audience:** Contributors and agents.
**Related:** [`environment-modes.md`](../environment-modes.md),
[`go-launcher.md`](go-launcher.md), plan `mode-evolution`, #113.

## Two modes, two ways of working

| Mode | Who is on the other side | How the agent behaves |
|---|---|---|
| `COUNSELOR` | a person working with the agent | proposes, asks before commits, pushes and closing tasks; the default |
| `EXECUTOR` | nobody: the agent was spawned to do a task | does the work without asking; when blocked, records the problem on the task, sends a notice and closes the harness |

`EXECUTOR` replaces `UNHINGED`. The difference is not how much the agent is
trusted inside a conversation, but whether there is a conversation at all:
an executor is started with its task already assigned and ends on its own.

## How an executor runs

1. It is spawned with one task, already anchored.
2. It works the task through the normal workflow: context, notes, tests,
   outcome.
3. When it finishes, it records the outcome.
4. When it is blocked, it annotates the task with what failed and why,
   sends a notice so a person knows, and exits instead of waiting for an
   answer that will not come.

## What this changes

- The mode describes the running session, so it stays the `JACAZUL_MODE`
  variable set per launch and is never stored per project.
- The mode no longer decides where Taskwarrior reads its configuration.
  Today `UNHINGED` switches `TASKRC` to `JACAZUL_HOME/.taskrc` built from
  `templates/taskwarrior/unhinged/.taskrc`, and `COUNSELOR` injects missing
  UDAs into whatever `TASKRC` the user exported. Both are revisited here,
  not ported as they are; the Go launcher only creates the task data
  directory and reports it under `--debug` for now.

## To decide

- How an executor is started: a launcher command such as
  `jacazul executor <task>`, the harness it uses and its non-interactive
  flags.
- What an executor may do without a person: commit, push, close tasks,
  open pull requests.
- The notice channel for "blocked" and "done".
- Permissions and sandboxing for unattended runs.
- How a person reviews an executor's work afterwards.
- Taskwarrior configuration: one `.taskrc` for every mode, owned by
  Jacazul, instead of per-mode templates or edits to the user's file.

## Existing plan to align

Plan `mode-evolution` still describes renaming `UNHINGED` to `COMPANION`
(tasks `03e5dde2`, `1c9ad998`, `f98b2a45`, `5ff1b5f9`). That direction is
replaced by `EXECUTOR` and needs rewriting before anyone picks it up.
