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

## 🔜 Future Skills

Skills planned for addition:
- Code review automation
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

**Last Updated:** 2026-01-31
