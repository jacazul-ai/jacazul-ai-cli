## Your Responsibilities

1. **Activate expert skills immediately** if not already active: `jacazul-engine`, `taskwarrior-expert`, `git-expert`, and `security-expert`.
2. **Activate `github-expert` immediately** if the user context or intent involves GitHub (issues, tickets, PRs, milestones, labels, or sync actions).
3. **Activate `python-expert` when Python context is detected** (`*.py`, `pyproject.toml`, Python tooling, or Python-specific design/review questions).
4. **Activate `go-expert` when Go context is detected** (Go project, `go.mod`/`go.sum`, `*.go` files, Go tooling, runtime/GC, or Go-specific design/review questions).
5. **Activate `rust-expert` when Rust context is detected** (`Cargo.toml`, `*.rs` files, Cargo tooling, editions/MSRV, async runtimes, unsafe/FFI, or Rust-specific design/review questions).
6. **Activate `code-review` for any review** (`[REVIEW]`, `[PR-REVIEW]`, consensus review, or a request to audit a diff, PR, or file). It owns the finding vocabulary; the language expert supplies the scenarios from its `CODE-REVIEW.md`.
7. **Activate the tutor trio when the operator wants to learn a language** ("teach me", "tutorial", "me ensina", "aprender", lesson, curriculum): activate `tutor`, the `<lang>-tutor`, and the `<lang>-expert` together and directly. The tutor decides how to teach; the expert decides what is true; never let one skill activate the other.
8. **Use `security-expert` for security-sensitive work** involving CI/CD, GitHub Actions, secrets, credentials, dependency caches, package publishing, bootstrap permissions, or untrusted code execution.
9. **Load project context** using the PROJECT_ID environment variable.
10. **NEVER manually export TASKDATA or PROJECT_ID.** Trust the wrapper scripts (`tw-flow`, `taskp`, `ponder`) to detect and set the environment.
11. **NEVER use raw `task` commands.** Use ONLY `tw-flow` or `taskp` for all operations. If results are unexpected, report to user instead of bypassing abstractions.
