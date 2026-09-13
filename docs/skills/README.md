# Available Skills

Index of skills available in the AI CLI Sandboxed environment.

## 📋 Skills List

### Taskwarrior Expert
**Status:** ✅ Active  
**Version:** 1.2.0  
**Documentation:** [Complete Guide](../taskwarrior-expert.md)

Structured workflow management system with 7-phase workflow and interaction modes.

**Key Features:**
- Dashboard visualization with `tw-flow ponder`
> **Note:** The standalone `ponder` command is deprecated and will be removed in the future. Prefer using `tw-flow ponder` for full workflow integration.
- Task management with `tw-flow`
- Session continuity and handoffs
- 18 comprehensive tests

**Quick Start:**
```bash
tw-flow ponder
> **Note:** The standalone `ponder` command is deprecated and will be removed in the future. Prefer using `tw-flow ponder` for full workflow integration.
tw-flow initiative my-feature "EXECUTE|Build API|implementation|today"
```

**Location:** `/project/skills/taskwarrior-expert/`

---

### Git Expert
**Status:** ✅ Active
**Documentation:** [`skills/git-expert/SKILL.md`](../../skills/git-expert/SKILL.md)

When preparing a commit, the agent must treat the commit message as a
technical artifact: classify the changed area, choose a scope only when it is
clear, keep the title within 50 characters, wrap body lines at 72 characters,
and use a ticket footer only when an external GitHub, Bitbucket, or Jira ticket
exists.

Commits with bodies must use a file-based message:

```bash
git commit -F - <<'EOF'
fix: example title

Explain what changed and why.

Refs: #123
EOF
```

Use `git commit -m` only for a single-line, title-only commit. Never place
literal `\n` separators in a `-m` argument. After committing, verify the body
with `git log -1 --format=%b | cat -A` and confirm that no literal `\n` appears.

**Trigger → Action**
- When the diff touches a clear area, use a scoped Conventional Commit title.
- When the diff is generic or cross-cutting, omit scope or ask for guidance.
- When drafting the body, explain what changed and why with 72-column wrapping.
- When an external ticket exists, keep `Refs: #X`, `Fixes: #X`, or the
  configured external tracker reference as the final line.
- When no external ticket exists, omit the footer entirely; never reference
  internal Taskwarrior UUIDs or local task IDs.

**Location:** `/project/skills/git-expert/`

---

### Security Expert
**Status:** ✅ Active
**Documentation:** [`skills/security-expert/SKILL.md`](../../skills/security-expert/SKILL.md)

Repository security review system for CI/CD, secrets, dependency supply chain,
GitHub Actions, cache poisoning, and automation hardening.

**Trigger → Action**
- When reviewing GitHub Actions, activate `security-expert` and inspect triggers,
  permissions, `actions/cache`, `restore-keys`, artifacts, and secrets.
- When a workflow handles PRs from forks or uses `pull_request_target`, treat the
  code path as hostile until proven otherwise.
- When deploy/release jobs restore caches, verify the cache cannot be written by
  untrusted workflows.
- When secrets or credentials are involved, prefer least privilege, OIDC, and
  short-lived tokens.

**Location:** `/project/skills/security-expert/`

---

### Code Review
**Status:** ✅ Active
**Documentation:** [`skills/code-review/SKILL.md`](../../skills/code-review/SKILL.md)

Global code-review vocabulary and policy. Owns the review method, the
scenario format, the tracks (Foundations, Boundaries, Systems), the areas,
the technical levels, the advisory outcomes, the evidence labels, and the
mapping of security priorities onto the scale. Language skills add scenarios
in their own `CODE-REVIEW.md` and reference this shared scale.

**Trigger → Action**
- When reviewing any code, activate `code-review` plus the language expert;
  classify technical level and advisory separately and tag the area.
- When a non-blocking finding is actionable, fix it now or create a linked
  tech-debt task with context and acceptance criteria.
- When a language-specific review skill exists (`go-expert`, `rust-expert`),
  use its scenarios with this global scale instead of redefining labels.
- When `security-expert` reports Critical/High/Medium/Low, map them to
  BLOCKER/BLOCKER/WARNING/SUGGESTION under area `SECURITY`.

**Location:** `/project/skills/code-review/`

---

### Go Expert
**Status:** ✅ Active
**Documentation:** [`skills/go-expert/SKILL.md`](../../skills/go-expert/SKILL.md) and [Go Expert Guide](../go-expert.md)

Idiomatic Go guidance with explicit distinction between project mandates and
conventional baselines. Uses the project-preferred `gofmt` to `goimports`
formatting sequence and applies Line of Sight readability for control flow.

**Trigger → Action**
- When Go files change, run configured repository gates first.
- When no stronger project gate exists, use the conventional baseline:
  `gofmt`, `goimports`, `go test ./...`, and `go vet ./...` when supported.
- When reviewing control flow, keep the happy path left-aligned and handle
  failures early with guard clauses.
- When reviewing design, challenge Java-style ceremony and prefer standard
  library patterns.

**Location:** `/project/skills/go-expert/`

---

### Rust Expert
**Status:** ✅ Active
**Documentation:** [`skills/rust-expert/SKILL.md`](../../skills/rust-expert/SKILL.md)

Idiomatic, safe, performant Rust with an explicit policy boundary between
repository mandates, language guarantees, community convention, and options.
Review scenarios live in
[`skills/rust-expert/CODE-REVIEW.md`](../../skills/rust-expert/CODE-REVIEW.md)
on the shared code-review scale.

**Trigger → Action**
- When Rust files change, run the configured gates, then the conventional
  `cargo fmt`, `check`, `clippy`, `test`, and `doc` sequence.
- When reviewing Rust, concentrate on what the compiler cannot see: panics on
  runtime input, runtime borrow checks, async lifecycle, `unsafe` invariants,
  public-API contracts, and build-time trust.
- When a version-sensitive claim appears, read `edition`, `rust-version`, and
  the toolchain before judging it.

**Location:** `/project/skills/rust-expert/`

---

### Tutor (shared core)
**Status:** ✅ Active
**Documentation:** [`skills/tutor/SKILL.md`](../../skills/tutor/SKILL.md)

Language-agnostic teaching contract: learner calibration before any
curriculum, comparison bridges by memory-management background, the teaching
loop, lesson format, adaptive recalibration, and the pairing rule. A tutor
decides how and when to teach; its paired expert decides what is true.

**Trigger → Action**
- When the operator wants to learn a language, activate `tutor`, the
  `<lang>-tutor`, and the `<lang>-expert` together.
- When the paired expert is not active, the tutor stops and says so instead
  of teaching from memory.
- When a project defines lesson rules in its `AGENTS.md`, those rules win.

**Location:** `/project/skills/tutor/`

---

### Rust Tutor
**Status:** ✅ Active
**Documentation:** [`skills/rust-tutor/SKILL.md`](../../skills/rust-tutor/SKILL.md)

Rust curriculum on the shared tutor core, paired with `rust-expert`: bridges
from GC, RAII, and manual-memory backgrounds; four levels from toolchain to
production Rust; a foundations review sequence with explicit guardrails on
bindings, inference, generics, macros, and `enum` versus `Any`.

**Location:** `/project/skills/rust-tutor/`

---

### Go Tutor
**Status:** ✅ Active
**Documentation:** [`skills/go-tutor/SKILL.md`](../../skills/go-tutor/SKILL.md)

Go curriculum on the shared tutor core, paired with `go-expert`: bridges from
ownership, manual-memory, class-based, and scripting backgrounds; four levels
from module shape to production Go; a foundations review sequence on zero
values, slices, maps, interfaces, and errors with the aliasing and typed-nil
guardrails made explicit.

**Location:** `/project/skills/go-tutor/`

---

### Python Expert
**Status:** ✅ Active
**Documentation:** [`skills/python-expert/SKILL.md`](../../skills/python-expert/SKILL.md) and [Python Expert Guide](../python-expert.md)

Python engineering in three modes. `py-mode` names the tree legacy,
greenfield or migration from its markers; `py-check` is the house gate with
the explicit 79-column preference, a check-only mode and a guard that never
reformats a legacy tree. Playbook and review scenarios on the shared scale.

**Trigger → Action**
- When touching Python, run `py-mode <root>` and state the mode.
- When the tree is legacy, run `py-check --check` and match the local style.
- When migrating, follow the playbook sequence one commit per step.
- When reviewing, use `CODE-REVIEW.md` scenarios with the shared scale.

**Location:** `/project/skills/python-expert/`

---

### Python Tutor
**Status:** ✅ Active
**Documentation:** [`skills/python-tutor/SKILL.md`](../../skills/python-tutor/SKILL.md)

Python curriculum on the shared tutor core, paired with `python-expert`:
bridges from compiled, ownership, class-based and scripting backgrounds;
five levels from environment to production Python, including reading and
modernizing legacy code; a foundations review sequence on references,
mutable defaults, `is` versus `==`, iterator exhaustion and exceptions.

**Location:** `/project/skills/python-tutor/`

---

### JS/TS Expert
**Status:** ✅ Active
**Documentation:** [`skills/js-ts-expert/SKILL.md`](../../skills/js-ts-expert/SKILL.md) and [JS/TS Expert Guide](../js-ts-expert.md)

JavaScript and TypeScript across browser and Node, framework-neutral.
`js-mode` names the tree legacy, greenfield or migration without Node;
`js-check` runs only what the tree declares with the explicit 4-space
preference, a check-only mode and a guard for legacy trees. Serves the
operator who keeps JavaScript thin at the edge of a Go/Rust/Zig backend
and the one who chose full-stack JavaScript.

**Trigger → Action**
- When touching JS/TS, run `js-mode <root>` and state the mode.
- When adding logic, answer the boundary question once (edge, backend,
  WebAssembly, or full-stack JavaScript) and record it.
- When the tree is legacy, run `js-check --check` and match the local style.
- When reviewing, use `CODE-REVIEW.md` scenarios with the shared scale.

**Location:** `/project/skills/js-ts-expert/`

---

## 🔜 Future Skills

Skills planned for addition:
- Test generation
- Documentation generation
- Deployment workflows

---

## 🛠 Creating Custom Skills

### Structure
```
skills/my-skill/
├── SKILL.md           # Skill documentation
├── HIERARCHY.md       # (Optional) Conventions
├── scripts/           # Helper scripts
│   ├── main-script
│   ├── test-script.sh
│   └── README.md
└── ...
```

### Requirements
- Clear documentation in SKILL.md
- Executable helper scripts
- Test suite (recommended)
- Examples and usage guide

### Integration
Place skill directory in `/project/skills/` and reference in agent instructions.

---

**Last Updated:** 2026-09-13
