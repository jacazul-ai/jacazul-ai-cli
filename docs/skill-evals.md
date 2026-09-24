# Skill Evals

How we measure whether a skill changes model behavior, and how to read the
result. The authoring rules for a good case (adversarial, baseline-checked,
judgment over API recall) live in
[`skill-methodology.md`](skill-methodology.md#evaluation); this page covers
running, grading and reading.

The runner is Claude Code's `claude plugin eval`: every run is a Claude Code
session, and the traces, tools and sandbox below are Claude Code's. A result
therefore holds for Claude Code and the model it ran; Gemini, pi, Copilot and
Opencode load skills their own way and are not measured by it.

## Trigger → Action

### When you want to know if a skill actually helps

Run its suite with a no-skill baseline arm. The harness runs every case
twice: once with the skill installed (`with`) and once without (`without`).
The delta is the skill's effect.

```bash
claude plugin eval skills/<name> --case <case-name> --runs 1 \
  --ablation with-without --no-scaffold --no-publish \
  --max-cost-usd 1 --keep-temp </dev/null
```

| Flag | Why |
|---|---|
| `--case <name>` | One exact case name per call. The filter takes neither `[..]` nor `{..}` globs; loop over names instead. |
| `--runs 1` | Enough to spot a gap. Use more runs before claiming a small delta. |
| `--no-publish` | The default publishes the HTML report. |
| `--max-cost-usd` | Runaway guard. The reported USD is an equivalent figure; on a subscription it is plan usage, not a charge. |
| `--keep-temp` | Keeps each run's `trace.jsonl` so you can see what the agent actually did. |
| `</dev/null` | A backgrounded run otherwise inherits a stdin that never closes, and any prompt inside it hangs forever. |

`--trust-plugin` and `--allow-tools Bash` are the operator's call. Cases that
check shell commands need `--allow-tools Bash`, or the agent cannot even try
them.

### When you write a grader

Grade what the agent *did*, not text that happens to be in the trace.

| Check | Grader | Watch out for |
|---|---|---|
| The agent ran a command | `tool_used`, `tool: Bash`, `input_match` | `input_match` is a regex over the whole serialized input, the Bash `description` included. Anchor it: `'"command":\s*"[^"]*tw-flow focus'`. |
| The agent never ran a command | same, with `min: 0`, `max: 0`, `arm: both` | Without `arm: both` the check does not score under ablation. |
| The agent read a file | `tool_used`, `tool: Read`, `input_match` on the path | Proves loading; it says nothing about obeying the file. |
| The skill fired | `tool_used`, `tool: Skill`, `input_match: <skill>` | Only an indicator under ablation; it does not score. |
| The final reply says or refuses something | `llm` with the default `focus: last_message` | One claim per bullet. An ambiguous bullet fails correct replies. |
| The reply starts with a signature | `regex` over the final message | Fine for fixed text; never regex the trace. |

Two traps cost a full run each before we learned them:

- **Regex over the trace.** A loaded skill quotes command names, so
  `tw-flow focus` matches whether or not the agent ran it.
- **An `llm` judge fed the whole trace.** A trace of about 90 KB made the
  judge vote FAIL on correct runs with no explanation. Point it at the last
  message.

Change a grader only between baselines, never between the two sides of a
comparison.

### When the sandbox cannot run your tool

The eval sandbox hides the operator's home, so `tw-flow` and `taskp` start
and then crash with `ModuleNotFoundError: No module named 'jacazul'`. Grade
the attempt and the reaction: did the agent try the workflow tool first,
report the crash as the blocker, and refuse the raw `task` bypass? Behavior
that only happens *after* a successful call (reading a session note, running
status after focus) stays out of reach until a stub `tw-flow` exists.

### When you need to know whether a reference was read

The hub routes triggers to `references/`. Whether a reference was read shows
only in the trace, so keep the temp dirs and look:

```bash
for d in $(command ls -1dt /tmp/claude-eval-* | head -6); do
  t=$d/out/trace.jsonl
  echo "== $d"
  grep -oE '"skill":"[^"]+"' "$t" | sort -u
  grep -oE '"file_path":"[^"]*references/[^"]*"' "$t" | sort -u
done
```

A healthy run reads exactly the reference its trigger names, and nothing
when nothing triggers. The no-skill arm never reads one. Promote a check you
rely on into a `tool_used` `Read` grader, so the next run proves it without
anyone opening a trace.

Do not run `git` inside a kept directory; the harness seals what the plugin
wrote there.

### When you compare before and after a change

1. Freeze the graders and record the baseline: cases, flags, model, scores.
2. Make the change.
3. Re-run the same cases with the same flags.
4. Read the `with` column case by case. A drop is a regression even if the
   delta still looks positive, since the `without` arm varies between runs.
5. Record both runs on the task that owns the change.

## Current record: jacazul-engine

Cases in `skills/jacazul-engine/evals/`, runs=1, `claude-opus-5-5` agent,
haiku judge, graders as of the command-anchored revision.

| Case | Baseline (monolith, 66 KB) | After hub split (33 KB) | Reference read after the split |
|---|---|---|---|
| 01 onboard anchors first | 1.00 / 0.00 | 1.00 / 0.33 | `onboard.md`, then `tw-flow focus` |
| 03 status stays on status | 0.75 / 0.25 | 0.75 / 0.50 | `onboard.md` |
| 04 close waits for outcome | 1.00 / 0.67 | 1.00 / 0.67 | none (no trigger) |

Scores are `with / without`. Per-run cost of the `with` arm dropped about 20
percent after the split. Without a launcher, every `with` run also read
`references/personas/jacazul.md`, the documented fallback voice.

Not covered yet:

- `session.md`, `modes.md`, `language.md` and `glossary.md` triggers;
- a persona handoff reading another voice and switching signature;
- the real launcher path, where the injected voice should make the persona
  read unnecessary;
- harnesses other than Claude Code;
- case 02 (handoff) and the status call in case 03, which need a stub
  `tw-flow`; case 05 (review routing), which never fires the engine.
