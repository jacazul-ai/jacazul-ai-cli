# Git Engineering Playbook

Implementation guidance for building commits and changing history without
losing work, without surprising people who already fetched it, and
without interactive commands an agent cannot drive. This file answers
**how to do the operation**. Scenario-based review directives live
separately in [`CODE-REVIEW.md`](CODE-REVIEW.md).

These are defaults, not automatic repository policy. Read the
`## Git Workflow` section of `AGENTS.md`, `CONTRIBUTING`, hooks, CI and
branch protection before adopting an optional gate or changing how the
project integrates work.

## Before touching history

1. Run `git-mode <path>` and name the mode (`linear`, `merge`, `unknown`),
   its source, the reference branch and the layout.
2. Run `git status`: know every modified, staged and untracked file before
   any command that moves `HEAD`.
3. Find what is published: `git log --oneline @{u}..HEAD` lists commits
   the upstream does not have; `git branch -r --contains <commit>` is
   non-empty when a commit already lives on a remote branch.
4. Create a backup ref before any rewrite:
   `git branch backup/<topic>-$(date +%Y%m%d%H%M%S)`.
5. Never use the stash as a parking lot in a worktree layout: the stack is
   shared. Prefer a temporary WIP commit; if a stash is unavoidable, push
   it with a unique message, apply it by hash, and drop only that entry.

## Mode: linear

- Topic branches start from the reference and are rebased onto it before
  integration: `git fetch origin`, then `git rebase origin/<reference>`.
- Clean the series before integration with the rebase recipe below:
  `fixup` often, `drop` occasionally, reorder when it tells a clearer
  story, `squash` rarely.
- Integrate by fast-forward only. With the reference checked out in its
  own worktree: `git -C <reference-worktree> merge --ff-only <topic>`.
  With the reference checked out nowhere:
  `git fetch . <topic>:<reference>` (refuses anything but a fast-forward).
- A rejected fast-forward means the reference moved: rebase the topic
  again, never merge.
- Run the suite on every commit of the series when the project wants a
  bisectable history: `git rebase --exec '<test command>' <reference>`.

## Mode: merge

- Never rewrite commits that exist on a remote branch.
- Update a published topic with `git merge <reference>` when the project
  accepts merge commits on topics; rebase only commits that are not
  published yet.
- Integrate with the project's style: `git merge --no-ff <topic>` for
  git-flow style histories, or the host's PR merge button when merges go
  through review.
- Keep merge commit messages meaningful: name the topic and the ticket.

## Mode: unknown

Show the `git-mode` evidence and ask the operator which integration style
applies before rebasing, merging or pushing. Suggest pinning the answer
(the `## Git Workflow` section or `git config git-expert.integration`) so
the next agent does not ask again.

## Commit construction

The message standard lives in [`SKILL.md`](SKILL.md#-commit-standards).
Building the commit itself:

- One logical change per commit. When the working tree mixes a refactor
  and a fix, stage and commit them separately.
- Stage by path: `git add -- <file>...`. New files that should appear in
  `git diff` before staging: `git add -N -- <file>`.
- Unstage without touching the working tree:
  `git restore --staged -- <file>` (Git 2.23+) or `git reset -- <file>`.
- Corrections to an unpublished commit in the series become fixups:
  `git commit --fixup=<hash>`; message-only corrections use
  `git commit --fixup=reword:<hash>` (Git 2.32+).
- Always finish with `git log -1 --format=%b | cat -A`.

## Non-interactive staging (hunks)

`git add -p` needs a terminal. Stage hunks through a patch instead:

```bash
tmp=$(mktemp -d)
git diff -- path/to/file > "$tmp/all.patch"
cp "$tmp/all.patch" "$tmp/wanted.patch"
# edit wanted.patch: delete the hunks that belong to another commit
git apply --cached --check --recount "$tmp/wanted.patch"
git apply --cached --recount "$tmp/wanted.patch"
git diff --staged -- path/to/file
rm -rf -- "$tmp"
```

Deleting whole hunks keeps the patch valid; deleting lines inside a hunk
needs `--recount` so Git recomputes the hunk header counts. `--check`
first: it proves the patch applies without changing the index.

## The rebase recipe (non-interactive rebase -i)

One auditable operation instead of a chain of resets and cherry-picks.

```bash
tmp=$(mktemp -d)
base=$(git merge-base HEAD <reference>)
backup=backup/<topic>-$(date +%Y%m%d%H%M%S)
git branch "$backup"

# 1. Write the full todo list, oldest commit first.
git log --reverse --format='pick %h %s' "$base"..HEAD > "$tmp/todo"
# 2. Edit it: pick, fixup, drop, reorder lines, exec lines.

# 3. Hand the file to the sequence editor (it receives the todo path).
GIT_SEQUENCE_EDITOR="cp $tmp/todo" git rebase -i "$base"

# 4. Prove the result.
git range-diff "$base" "$backup" HEAD
git diff "$backup" HEAD      # empty when only order or messages changed
```

Todo commands an agent can use without an editor:

| Command | Effect |
|---|---|
| `pick <hash>` | Keep the commit |
| `fixup <hash>` | Meld into the previous commit, discard its message |
| `drop <hash>` | Remove the commit |
| `exec git commit --amend -F <file>` | Reword the commit just picked from a message file |
| `exec <test command>` | Stop the rebase when the test fails at that point |

`squash` and `reword` open the message editor; prefer `fixup` plus an
`exec ... --amend -F` line, or set `GIT_EDITOR=true` to accept the
combined message a `squash` proposes.

Fixups prepared while working collapse without writing a todo:

```bash
GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash "$base"
git rebase --autosquash "$base"    # Git 2.44+, no -i needed
```

After rebasing onto a reference that moved, compare against the old base:

```bash
git range-diff "$(git merge-base "$backup" <reference>)..$backup" \
    "<reference>..HEAD"
```

Stacked topic branches follow the rebase with `--update-refs`
(Git 2.38+). Delete the backup ref only after the push is verified.

## Pushing rewritten history

- Only to a branch the workflow allows rewriting (a topic branch in
  `linear` mode, or commits never published).
- Always with a lease:
  `git push --force-with-lease --force-if-includes origin <topic>`
  (`--force-if-includes` is Git 2.30+). A rejected lease means someone
  pushed: fetch, `git range-diff` their commits, and ask.
- Never force-push the reference branch.

## Recovery

- `git reflog` lists every position `HEAD` held; `git reflog <branch>` for
  a branch. A lost commit is usually one `git branch rescue <hash>` away.
- `ORIG_HEAD` points to where `HEAD` was before a reset, rebase or merge.
- A rebase, merge or cherry-pick in progress: `--abort` returns to the
  starting point; `--continue` after resolving; `--skip` drops the
  current commit (confirm first).
- Back to the backup: `git reset --hard <backup>` destroys uncommitted
  work, so check `git status` and confirm with the operator.
- Commits no ref reaches: `git fsck --lost-found` before `git gc` prunes
  them.

## Conflicts

- Enable readable conflict hunks: `git config merge.conflictStyle zdiff3`
  (Git 2.35+) shows the common ancestor between the two sides.
- Preview a merge without touching the working tree:
  `git merge-tree --write-tree <branch1> <branch2>` (Git 2.38+) exits 1
  and lists the conflicted paths when the merge would conflict.
- During a rebase, sides are inverted: `--ours` is the branch being
  rebased onto, `--theirs` is the commit being replayed.
  `git checkout --theirs -- <file>` keeps the replayed commit's version.
- `git config rerere.enabled true` records resolutions and replays them
  when the same conflict returns in the next rebase; the cache is shared
  by every worktree.
- Resolve, `git add -- <file>`, run the tests, then `--continue`. Never
  commit conflict markers: `git diff --check` finds them.

## Worktrees and bare repositories

Set up a bare layout (one directory per branch):

```bash
git clone --bare <url> project/.bare
cd project
printf 'gitdir: ./.bare\n' > .git
git config remote.origin.fetch '+refs/heads/*:refs/remotes/origin/*'
git fetch origin
git worktree add main main
```

- A bare clone does not set `remote.origin.fetch`; without it no
  remote-tracking branches exist and `@{u}` does not resolve.
- New work gets a new worktree:
  `git worktree add <dir> -b <topic> <reference>`.
- A branch can be checked out in one worktree at a time; never
  `git switch` inside a worktree to a branch another worktree holds.
- Shared by every worktree: refs, config, hooks, the stash, rerere.
  Per worktree: `HEAD`, the index, bisect state.
- `git worktree list` before creating one; `git worktree remove <dir>`
  refuses a dirty worktree unless forced (confirm first);
  `git worktree prune` cleans entries whose directory is gone.
- A project root that moves between machines or containers benefits from
  relative links: `worktree.useRelativePaths` (Git 2.48+).

## Bisect with the reproduction test

```bash
git bisect start <bad> <good>
git bisect run <reproduction>   # 0 good, 125 skip, other 1-127 bad
git bisect log > "$tmp/bisect.log"
git bisect reset
```

Keep the reproduction script outside the tracked tree (or untracked) so
it exists at every checked-out commit. A series where each commit builds
and passes the suite is what lets bisect name one commit.

## Secrets in history

1. Find every occurrence: `git log --all -S'<fragment>' --oneline`, and
   `git log --all -G'<regex>'` for patterns.
2. Treat a pushed secret as compromised: rotate or revoke it first.
3. Rewrite only with the operator's approval, using `git filter-repo`
   (a separate tool, not bundled with Git): `--replace-text` or
   `--invert-paths --path <file>`.
4. Coordinate: every clone must re-clone, and hosts keep old objects
   reachable through forks and pull-request refs until their support
   purges them.
5. Activate `security-expert` for the rotation and the audit.

## Hooks, signing and tags

- Hooks live in `.git/hooks` or `core.hooksPath`. A failing hook is a
  finding: read its output and fix the cause; never `--no-verify`.
- Signing: `commit.gpgsign true` with OpenPGP, or `gpg.format ssh` and
  `user.signingkey` for SSH keys (Git 2.34+). Verify with
  `git log --show-signature -1`.
- Release tags are annotated: `git tag -a v1.2.0 -m 'v1.2.0'`, or signed
  with `-s` when the project signs.
- Push tags by name: `git push origin v1.2.0`. `--tags` pushes every stray
  local tag.
- Never move or delete a published tag; release a new version instead.

## Version ladder

Verified against the release notes of the installed Git. Check
`git --version` before relying on a row.

| Git | Feature |
|---|---|
| 2.19 | `git range-diff` |
| 2.23 | `git switch`, `git restore` |
| 2.30 | `git push --force-if-includes` |
| 2.32 | `git commit --fixup=amend:<commit>` and `--fixup=reword:<commit>` |
| 2.34 | SSH signing (`gpg.format ssh`) |
| 2.35 | `merge.conflictStyle zdiff3` |
| 2.38 | `git rebase --update-refs`, `git merge-tree --write-tree` |
| 2.44 | `--autosquash` without `-i`, `git replay` |
| 2.48 | relative worktree links (`worktree.useRelativePaths`) |

`init.defaultBranch` and `push.autoSetupRemote` exist in current Git; on
an older installation, confirm them with `git help config` before use.

## References

- [Git reference documentation](https://git-scm.com/docs)
- [Git release notes](https://github.com/git/git/tree/master/Documentation/RelNotes)
- [Pro Git book](https://git-scm.com/book)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [git filter-repo](https://github.com/newren/git-filter-repo)
- [Git Code Review Directives](CODE-REVIEW.md)
