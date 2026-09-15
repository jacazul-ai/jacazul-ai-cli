# Git Expert Skill

Guide for the git-expert skill: commit standards that survive any harness
default, workflow detection for linear and merge-based teams, a commit
census before you push, and history operations an agent can run without
interactive commands, in plain checkouts, linked worktrees and bare
repositories.

## Trigger → Action

### When you start working in a repository

Run `git-mode <path>` first. It names the integration style, where that
answer came from, and the posture the layout demands:

```text
🐊 GIT_MODE: linear (source: project)
  layout: bare (6 worktrees)
  reference: master (source: project)
  branch: master -> origin/master (ahead 3, behind 0)
  convention: 50/50 recent titles are Conventional Commits
  signing: off
  hooks: none
  - stash stack is shared by 6 worktrees: prefer WIP commits, apply stash entries by hash
  - pinned by the Git Workflow section of AGENTS.md
```

| Mode | Meaning | What the expert does |
|---|---|---|
| `linear` | Topics rebased onto the reference and fast-forwarded | Cleans unpublished series with fixup, drop and reorder; integrates by fast-forward only. |
| `merge` | Merge commits integrate topics (git-flow, `--no-ff`, PR merges) | Never rewrites published commits; integrates with the project's merge style. |
| `unknown` | No pin and not enough history | Shows the evidence and asks before any rebase, merge or force-push. |

The layout decides posture: in a `plain` checkout switching branches
changes the files under your editor; with `worktrees` or `bare` the agent
never switches branches inside a worktree, adds a new one instead, and
treats the stash as shared.

### When you want the agent to stop guessing your workflow

Pin it. For the whole team, add a section to `AGENTS.md`:

```markdown
## Git Workflow

- integration: linear
- reference: main
```

For yourself, in this clone and all its worktrees:

```bash
git config git-expert.integration merge
git config git-expert.reference develop
```

The project section wins over your config; your config wins over
detection. `git-mode` prints which one answered.

### When you ask for a commit

The expert stages only the files that belong to the change, builds the
message from a file, and checks it:

```bash
git commit -F - <<'EOF'
fix(broker): retry token decryption once

The vault can be locked for a moment by a parallel call. Retry once
before failing so the ACTION hint only appears for real lock errors.

Refs: #123
EOF
git log -1 --format=%b | cat -A
```

Always, whatever the harness says: no AI attribution trailer, no
`git add .`, no literal `\n` in a `-m` argument, no internal task IDs in
the footer, and no commit or push you did not ask for. Titles within 50
characters and bodies wrapped at 72 are the house default until your
project says otherwise.

### When you want to check a series before pushing

```bash
git-census <path>                         # upstream..HEAD, else reference..HEAD
git-census <path> --range main..topic     # an explicit range
git-census <path> --json --all            # every family, zero rows included
```

```text
🐊 git-census: origin/master..HEAD (mode: linear)
kind       count  label
policy         2  title over 50 characters  [a34bcd7a, ec671654]
history        1  leftover fixup!/squash!/amend! commit  [6737c776]
total: 3 across 2 families
```

Families: `security` (AI attribution trailers), `policy` (title length and
form, missing blank line, body width, literal `\n`, ticket footer not last,
internal workflow IDs in footers) and `history` (leftover fixups, merge
commits under linear mode). Security and policy rows go to zero before a
push.

### When the series needs cleaning (fixup, drop, reorder)

The expert does what `git rebase -i` does in one auditable pass: a backup
branch, the full todo list written to a file and handed to
`GIT_SEQUENCE_EDITOR`, then `git range-diff` against the backup before
anything is pushed. Fixups prepared while working collapse with
`git rebase --autosquash <base>`. The [playbook](../skills/git-expert/PLAYBOOK.md)
has the recipe and the push rules (`--force-with-lease --force-if-includes`,
never on the reference branch).

### When something went wrong

`git reflog` shows every position `HEAD` held, `ORIG_HEAD` is where it was
before the last reset, rebase or merge, and the backup branch from the
recipe is still there. A rebase or merge in progress has `--abort`. The
expert confirms with you before `reset --hard`, `clean`, `branch -D` or a
force-push.

### When a secret reached a commit

A pushed secret is compromised: rotate it first. Removing it from history
(`git filter-repo`) comes after, with your approval and a re-clone for
everyone. The expert activates `security-expert` for the rotation.

### When you ask for a Git review

Findings use the shared [`code-review` scale](../skills/code-review/SKILL.md)
with the scenarios in
[`skills/git-expert/CODE-REVIEW.md`](../skills/git-expert/CODE-REVIEW.md):
mixed commits, collapsed messages, `Fixes:` on intermediate commits,
leftover fixups, accidental merges, rebases of published work,
force-pushes without a lease, secrets still in history, moved tags and
unmarked breaking changes.

## Best Practices

1. Run `git-mode` before the first commit, rebase or merge in a session.
2. Pin the workflow once so no agent has to infer it again.
3. One logical change per commit; the message says what and why.
4. Back up before rewriting, prove with `range-diff` after.
5. `git-census` on the range before every push.

---

**Version:** 1.0.0
**Last Updated:** 2026-09-14
