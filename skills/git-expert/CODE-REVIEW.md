# Git Code Review Directives

Git-specific review scenarios for commits, series and history operations:
the shape to avoid, the sequence it creates, what can fail, and the
evidence or correction a reviewer should require.

The review method, scenario format, tracks, areas, technical levels,
advisories, and evidence labels are owned by the shared
[Code Review skill](../code-review/SKILL.md). This file adds Git scenarios
only and never redefines those labels. Before judging a series, run
`git-mode <path>` to know the integration mode and its source, and
`git-census <path> --range <base>..<tip>` to know which message and
history families the series already carries.

Scenarios are grouped by [track](../code-review/SKILL.md#tracks). The track
describes the learning path, not the severity: a Foundations pattern can
still create a critical security incident. A review comment must be tied
to the repository's contract or a credible failure mode.

The diff is only half of a Git review. The other half is the series: what
each commit claims, whether it can be reverted or bisected alone, and
whether the operation that produced it respected what other people already
fetched.

## Mode-aware review

- **linear:** a merge commit on the reference, or a series integrated
  without a fast-forward, is `WARNING` / `FIX-NOW` / `POLICY`. Leftover
  `fixup!` and `squash!` commits are `WARNING` / `FIX-NOW` /
  `MAINTENANCE`.
- **merge:** a rewrite of commits that already exist on a remote branch is
  `BLOCKER` / `FIX-NOW` / `CONTRACT`: every clone now holds a diverged
  history.
- **unknown:** any rebase, force-push or integration done without asking
  is `WARNING` / `FIX-NOW` / `POLICY`; the correction includes pinning the
  workflow.

Message widths and title case are house convention: report them as
`NIT` unless a project mandate (hook, commitlint, CI check) enforces them,
then as `WARNING` / `FIX-NOW` / `POLICY`.

## Worked example (full form)

```text
$ git log --oneline origin/main..origin/release-script
e4f5a6b fix(deploy): read the token from the environment
a1b2c3d feat(deploy): add release script
$ git show a1b2c3d -- scripts/release
+DEPLOY_TOKEN=ghp_...
```

**Context:** A topic branch already pushed for review. The second commit
removes a token the first commit hardcoded.

**Runtime sequence:** The push sent both commits to the host. The final
tree is clean, so a diff-only review of the branch shows nothing. Anyone
who fetched the branch, every fork, and the host's pull-request refs hold
`a1b2c3d` with the token.

**Failure modes:** The token is usable by anyone with read access to the
repository or its forks; squashing on merge does not remove the object
already pushed; a later force-push does not remove it from other clones.

**Review directive:** Search the whole series, not the final tree, for
secrets (`git log -p <base>..<tip>`, `git log --all -S'<fragment>'`).
Treat a pushed secret as compromised.

**Acceptable correction:** Rotate or revoke the token first. Then remove
it from history: when the branch was never merged, rewrite the series
(fixup the removal into `a1b2c3d`) and push with a lease; when it reached
the reference, follow the playbook's secrets procedure with
`git filter-repo` and coordinate re-clones. Activate `security-expert`.

**Classification:** `BLOCKER` / `FIX-NOW` / `SECURITY` / `TRACE`.

## Foundations: commits and messages

### 1. Commit mixing unrelated changes

**Problem:** One commit carries a refactor and a fix, a formatting sweep
and a feature, or two features.

**What can happen:** The behavior change hides inside mechanical noise;
reverting the fix reverts the refactor; `git bisect` names a commit too
large to explain the regression.

**Review questions:** Can each part be reverted alone? Would the title
still be true for every hunk?

**Safer shape:** One logical change per commit; formatting sweeps in their
own commit; split with path staging or `git apply --cached`.

### 2. Title or body that does not explain the change

**Problem:** `fix stuff`, `wip`, `update files`, or a body that narrates
the diff line by line.

**What can happen:** Release notes, `git log --grep` and `git blame` lose
the reason; the next maintainer reverse-engineers intent from code.

**Safer shape:** Title in imperative mood naming the effect; body with what
changed and why it matters.

### 3. Body collapsed by a literal `\n`

**Problem:** `git commit -m "title\n\nbody"` from a double-quoted shell
string.

**What can happen:** Git stores the backslash sequences literally: the
whole message becomes a single title line, tooling that reads trailers
finds none, and the footer is lost.

**Safer shape:** `git commit -F` from a file or a quoted heredoc;
`git log -1 --format=%b | cat -A` after the commit.

### 4. Title over 50, body over 72, missing blank line

**Problem:** Long titles, unwrapped bodies, or a body starting on the
second line.

**What can happen:** Titles truncate in `--oneline` views and PR lists;
without the blank line Git treats the first paragraph as the subject.

**Safer shape:** The widths from the house standard or the project's own;
always a blank line after the title.

### 5. `Fixes:` on an intermediate commit

**Problem:** The first commit of a multi-commit series carries
`Fixes: #123`.

**What can happen:** The host closes the ticket when that commit lands on
the default branch, while the rest of the work is still pending or gets
dropped.

**Safer shape:** `Refs: #123` on intermediate commits; `Fixes: #123` only on
the commit that completes the ticket.

### 6. Internal workflow identifiers in footers

**Problem:** `Refs: 9d0edacf`, a task number, or a plan name from a local
workflow tool.

**What can happen:** Nobody outside the author's machine can resolve the
reference; short hexadecimal IDs look like commit hashes and mislead.

**Safer shape:** External ticket references only; no footer when there is
no external ticket.

### 7. Scope that does not match the diff

**Problem:** `fix(broker): ...` on a commit that touches bootstrap and
docs.

**What can happen:** Changelog tooling files the change under the wrong
component; reviewers skip it.

**Safer shape:** The scope names the real area, or no scope for a
cross-cutting change.

### 8. Files swept in by staging everything

**Problem:** `git add -A` or `git add .` staged editor files, scratch
scripts, `.env`, or files from another task.

**What can happen:** Unrelated or sensitive files enter history; the
commit claims less than it changes.

**Review questions:** Does every path in `git show --stat` belong to the
title?

**Safer shape:** Stage by path; ignore generated and local files in
`.gitignore`.

### 9. Generated files and large binaries

**Problem:** Build output, archives, or media committed directly.

**What can happen:** Repository size grows permanently; diffs become
unreviewable; generated files drift from their source.

**Safer shape:** Generate in the build; Git LFS or release assets for
binaries the project must distribute; commit lockfiles only when the
project tracks them.

## Boundaries: series, history and integration

### 10. Leftover `fixup!`, `squash!` and `amend!` commits

**Problem:** Correction commits reach the reference unsquashed.

**What can happen:** Titles without meaning in the permanent history;
bisect lands on half-finished states.

**Safer shape:** `git rebase --autosquash <base>` before integration;
`git-census` shows zero leftovers.

### 11. Accidental merge commit in a linear workflow

**Problem:** `git pull` with `pull.rebase false` merged `origin/<topic>`
into the local topic, or the reference got a merge instead of a
fast-forward.

**What can happen:** The history stops being linear; the next rebase
replays or drops the merge unexpectedly.

**Safer shape:** `git pull --rebase` or `git fetch` plus rebase on topics;
`merge --ff-only` on the reference.

### 12. Rebase of published commits

**Problem:** A branch that other people fetched is rebased and
force-pushed without agreement.

**What can happen:** Collaborators' next pull merges both histories or
fails; their local commits based on the old series need manual rescue.

**Review questions:** Does the mode allow it? Does anyone else build on
the branch?

**Safer shape:** Rewrite only unpublished commits, or topic branches the
workflow marks as rewritable, and announce it.

### 13. Force-push without a lease

**Problem:** `git push --force` to a shared or reviewed branch.

**What can happen:** Commits pushed by someone else since the last fetch
are silently overwritten.

**Safer shape:** `git push --force-with-lease --force-if-includes`; fetch
and `git range-diff` when the lease is rejected.

### 14. Rewrite without a backup or proof

**Problem:** A rebase, reset or filter operation run with no backup ref
and no comparison afterwards.

**What can happen:** A dropped commit or a wrong conflict resolution goes
unnoticed until the reflog has expired.

**Safer shape:** Backup ref first; `git range-diff` and `git diff <backup>`
after; delete the backup only after the push is verified.

### 15. Series that breaks between commits

**Problem:** The tip passes the tests, but intermediate commits do not
build or fail the suite.

**What can happen:** `git bisect` stops on unrelated failures; reverting a
single commit leaves the tree broken.

**Safer shape:** `git rebase --exec '<test command>' <base>` before
integration when the project wants bisectable history.

### 16. Conflict resolution that loses a side

**Problem:** A conflict resolved by taking `--ours` or `--theirs` for the
whole file, markers committed, or the sides confused during a rebase.

**What can happen:** Changes from the other side disappear without a
trace in the diff of the resolution commit.

**Review questions:** Does `git range-diff` show the replayed commit still
carrying its change? Does `git diff --check` pass?

**Safer shape:** `merge.conflictStyle zdiff3`; resolve hunk by hunk; run
the tests before `--continue`; remember that sides invert during a rebase.

### 17. Branch switch or stash across worktrees

**Problem:** An agent switches branches inside a linked worktree or pops a
stash entry in a bare-plus-worktrees layout.

**What can happen:** Another session's working directory changes under
it; a stash entry created by another worktree lands in the wrong tree.

**Safer shape:** A new worktree per branch; WIP commits instead of the
stash; stash entries applied by hash with a unique message.

### 18. Reverts without a reason

**Problem:** `Revert "..."` with the default message only, or a revert of a
revert with no explanation.

**What can happen:** Nobody knows whether the original change was wrong or
the environment was; the change comes back with the same defect.

**Safer shape:** The body names the reverted hash and why; a reapply
explains what changed since.

## Systems: security, contracts and process

### 19. Secret removed later but still in history

**Problem:** A credential added in one commit and removed in a later one
(see the worked example).

**What can happen:** Anyone with read access recovers it from history,
forks, or host caches.

**Safer shape:** Rotate first, then rewrite with the operator's approval
and coordinate every clone.

### 20. AI attribution trailer

**Problem:** `Co-authored-by:` naming an AI tool, `Claude-Session:`, or a
`Generated with` footer.

**What can happen:** Violates the hard rule of this skill; leaks tooling
metadata into a permanent record; breaks trailer-based tooling
expectations.

**Safer shape:** Remove the trailer with a message-only rewrite before the
series is published.

### 21. Hooks bypassed or signing disabled

**Problem:** `--no-verify`, `-c commit.gpgsign=false`, or
`core.hooksPath=/dev/null` to get past a failing gate.

**What can happen:** The project's gate stops being evidence; unsigned
commits reach a branch that requires signatures.

**Safer shape:** Fix the cause the hook reported; ask the operator when
the gate itself is wrong.

### 22. Published tag moved or deleted

**Problem:** `git tag -f v1.2.0` or deleting and recreating a pushed tag.

**What can happen:** Clones and package mirrors keep the old object; two
builds of "v1.2.0" differ; checksums in lockfiles fail.

**Safer shape:** Release a new version; tags are immutable once pushed.

### 23. History rewrite of the reference branch

**Problem:** A force-push, filter or reset on `main`, `master`, `develop`
or a release branch.

**What can happen:** Every open topic branch, every clone, and every CI
cache holds diverged history; tags may point to commits no branch reaches.

**Safer shape:** Revert commits on the reference; a real rewrite (secret
purge) is a coordinated incident with the operator.

### 24. Breaking change without a marker

**Problem:** An incompatible API, flag or format change committed as a
plain `feat` or `fix`.

**What can happen:** Release tooling computes a minor or patch version;
consumers upgrade into a break.

**Safer shape:** `!` after the type or scope and a `BREAKING CHANGE:`
paragraph with the migration.

### 25. Credentials in remotes or configuration

**Problem:** `https://user:token@host/...` remotes, or a committed file
with tokens for a Git host.

**What can happen:** Tokens leak through `git remote -v`, logs, shell
history and shared configuration.

**Safer shape:** A credential helper or SSH keys; `security-expert` for
any token already exposed.

## Cross-cutting directives

### A clean diff with a dirty history

**Avoid:** Approving a branch from its combined diff alone.

**Context:** Squash-on-merge hides intermediate commits from the final
history, but pushed objects stay on the host and in every clone.

**Review directive:** Read the series (`git log -p <base>..<tip>`) for
secrets, generated files, and reverted accidents even when the final
diff is clean.

**Classification:** by what the series contains; a secret is `BLOCKER` /
`FIX-NOW` / `SECURITY`.

### History as evidence

**Avoid:** Treating commit structure as cosmetic.

**Context:** Revert, bisect, blame and release notes all operate on
commits, not on pull requests.

**Review directive:** Ask whether each commit can be understood, reverted
and tested alone; request a restructure before integration when it
cannot.

**Classification:** usually `SUGGESTION` / `FIX-OR-TECH-DEBT` /
`MAINTENANCE`; `WARNING` when the project mandates bisectable history.

## Automated review baseline

The verification baseline lives once in
[`SKILL.md`](SKILL.md#-conventional-verification-baseline). For a review,
run `git-mode <path>` first, then `git-census <path> --range <base>..<tip>`
over the series under review; its counts are `TOOL` evidence, not a
verdict.

## Source index

- [Git reference documentation](https://git-scm.com/docs)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [git filter-repo](https://github.com/newren/git-filter-repo)
- [Git Engineering Playbook](PLAYBOOK.md)
- [Shared Code Review skill](../code-review/SKILL.md)
