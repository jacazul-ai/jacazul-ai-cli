# Jacazul AI CLI Manifesto

This document defines the foundational engineering standards, architectural
patterns, and operational philosophies for the Jacazul AI CLI project.

## 🏛 Architectural Boundaries

### Structure vs. Dynamics (Setup vs. Runtime)
- **Setup (Structure - `scripts/configure`):** One-time environment
  preparation. Handles immutable filesystem changes: directory creation,
  symbolic links in `~/bin`, and initial template deployment. It sets the stage
  but does not run the show.
- **Runtime (Dynamics - `scripts/bootstrap/`):** Session-specific
  initialization. Handles mutable configuration and dynamic environment
  detection: injecting environment variables, surgical updates to settings
  JSONs (e.g., `experimental.enableAgents`), and locating system resources
  (e.g., finding the real `task` binary).

## 🔊 Logging Philosophy

The project adheres to a "Silent by Default" logging policy to maintain CLI
usability and focus.

- **Standard Execution:** Silence is mandatory if the environment is healthy
  and checks pass.
- **State Changes:** Output MUST be emitted when the system state is modified
  (e.g., "Creating directory X").
- **Verification:** Verification of existing resources MUST stay silent unless
  `DEBUG=true`.
- **Debug Mode:** Enabled via `DEBUG=true`. Provides full verbosity for
  troubleshooting.
- **Dry Run:** Enabled via `DRY=true`. Allows verifying the entire bootstrap
  process (Dynamics) without executing the final CLI binary.
- **Error Handling:** Errors MUST be emitted to `stderr` with clear
  instructional context.

## 🔒 Engineering Mandates

### 1. Taskwarrior Abstraction
- **Mandate:** Agents and tools MUST NOT invoke the raw `task` binary directly.
- **Security:** The raw `task` command is obfuscated to prevent accidental
  bypass. If an agent encounters the `scripts/task` wrapper, it MUST stop and
  consult the user.
- **Admin Bypass:** The `rtask` command provides a project-specific bypass to
  the real binary. This tool is for MANUAL ADMINISTRATIVE USE ONLY.
- **Protocol:** All operations MUST go through the `taskp` project-aware
  wrapper or the `tw-flow` workflow manager.
- **Isolation:** Project isolation via `TASKDATA` MUST be preserved at all costs.

### 2. Hatch-Generated Skills (CRITICAL)
- **Mandate:** The `jacazul-engine` skill and all agent prompt files are
  **generated artifacts** produced by `jacazul-hatch` from source templates.
  NEVER edit generated files directly.
- **Source of Truth:** All skill and agent prompt updates MUST be made in
  `jacazul/hatch/templates/`. The templates are the canonical source.
- **Regeneration:** After editing templates, regenerate with
  `jacazul-hatch --target <target>` to propagate changes. The `--client`
  option remains a compatibility alias.
- **Targets:** `pi`, `openai`, and `all` are supported alongside the native
  launcher targets. `all` generates the shared engine once and then renders
  only eligible adapters.
- **Generated Locations:** `skills/jacazul-engine/SKILL.md` (the hub, from
  `gemini_full.md`), `skills/jacazul-engine/references/` (from
  `templates/references/` and one voice per persona), and
  `agents/{persona}-{client}.md` (from `agent_master.md`) for Copilot and
  Opencode only. `skills/jacazul-engine/evals/` is hand-written and tracked.
- **Ownership:** `scripts/bootstrap/hatch` selects the runtime target;
  client bootstraps remain responsible for linking and runtime configuration.

### 3. Skill Authoring
- **Mandate:** Any new skill, or any change to an existing skill's
  description, body structure, or cross-references, MUST follow
  [`docs/skill-methodology.md`](docs/skill-methodology.md).
- **Scope:** The methodology is subject-agnostic and applies to every skill in
  `skills/`, not only to language experts.
- **Boundary:** It governs how a skill is written and organized. It does not
  override repository policy, the Taskwarrior workflow, or the Git mandates
  above.

### 4. Context Preservation
- **Mandate:** Closing a task without documentation is FORBIDDEN.
- **Protocol:** The `tw-flow done` command requires an `OUTCOME:` annotation.
  Discarded tasks MUST include an automatic audit record.

## 🧠 Session Stabilization & Context Engineering

These directives ensure that the AI ecosystem remains functional and
context-aware across different platforms and tool availability states.

### 1. Multi-Agent Diagnostic Loop
- **Protocol:** Technical challenges should follow a cross-agent verification
  loop. A diagnosis produced by one agent (e.g., Copilot/Haiku) MUST be
  re-interpreted, validated, and implemented by the session navigator (e.g.,
  Gemini). This ensures that "things work the first time" by using multiple
  perspectives to identify the root cause before acting.

### 2. Tool-Agnostic Resilience
- **Directive:** Agents MUST be capable of operating in "limbo" states where
  high-level tools (create/edit) are unavailable.
- **Fallback:** Use base system primitives (standard bash redirection: `cat >`,
  `touch`, `echo >>`) to achieve filesystem changes. Always verify the state
  change manually (`ls`, `cat`) after a workaround execution.

### 3. Horizontal Skill Architecture
- **Mandate:** Agents MUST activate required expert skills (`jacazul-engine`,
  `taskwarrior-expert`) directly and simultaneously, and every other expert
  directly when its work starts.
- **Goal:** Avoid cascading dependencies where one skill activates another.
  Independence ensures that a failure in one subsystem does not blind the
  entire agent.

### 4. The Keystone Pattern (Context Resolution)
- **Philosophy:** Skills are not "optional tools"—they are the foundation that
  resolves instruction ambiguity. Activating a skill is equivalent to loading
  the project's Distribution (Distro).
- **Protocol:** Agents MUST activate `jacazul-engine` and
  `taskwarrior-expert` in the **first turn**, in parallel with tactical state
  discovery (e.g., `tw-flow focus`). `git-expert` and `security-expert` load
  on demand: git-expert before the first repository operation, security-expert
  when the work touches CI, secrets, dependencies or publishing. Their
  descriptions trigger them; Claude Code evals showed git-expert loading before any git
  command in 3 of 3 runs, and security-expert in 3 of 3 once its description
  named concrete triggers.
- **Resolution:** Mandates defined within a loaded skill ALWAYS take precedence
  over generic system prompts when resolving operational conflicts. This
  ensures that the agent adopts the Jacazul identity and technical standards
  before the first response.

## 🧬 Interaction Standards
- **Context Hunting Protocol:** Agents MUST NOT ask the user for session
  context that exists in the system. Upon activation, the agent MUST "hunt" for
  the mission state:
  1. **Orientation (The Anchor):** Run `tw-flow focus`.
  2. **Decision Branch:** IF anchored, run `tw-flow status` and `tw-flow
     context <uuid>`. IF empty, run `tw-flow ponder` for a strategic overview.
- **UUID Priority:** Tasks MUST be referenced by their 8-character UUID.
  Numeric Task IDs are transient and MUST NOT be shown to users.
- **Task Reference Format:** NEVER show a UUID alone. ALWAYS include: `uuid
  description [plan-name]`. Abbreviated descriptions are acceptable. Example:
  `f519b8c5 Define backlog UDA schema [tw-flow-backlog]`.
- **Task Completion Announcement:** When finishing a task and proposing the
  next, ALWAYS use format: `"Terminei a tarefa <uuid> <desc> [<plan>], começa
  com <uuid> <desc> [<plan>]"`. The user is often working across multiple plans
  and needs full context at a glance.
- **Persona Voice:** Responses MUST align with the active persona
  (Jacazul/Codana) and the detected user language, while persistent data
  (tasks, commits) remains in English.
- **Agent vs. Skill Distinction:**
  - **Copilot/Opencode:** Use the **Agent** pattern (`jacazul.md` in
    `~/.copilot/agents`).
  - **Gemini CLI:** Operates via the **Skill** pattern or direct **Onboard
    Prompt** logic. The `jacazul-engine` skill provides the protocols in this
    environment.
  - **Claude Code:** Operates via the **Skill** pattern using the `Skill()`
    tool. Skills (`jacazul-engine`, `taskwarrior-expert`) MUST be activated
    in the first turn, in parallel with `tw-flow focus`; the other experts
    load when their work starts.
- **Prompt Marketing & Workflow Awareness:**
  - **Concept:** Low-friction, high-value alerts within scripts (`tw-flow
    focus`, `onboard`) that notify the user of specific task attributes (e.g.,
    "ALERT: External ticket detected, git-expert will use it for automated
    commit referencing.").
  - **Goal:** To maintain alignment between the developer's focus and the
    project's technical requirements (like Git/Ticket integration) without
    interrupting the productive flow.

## 🎓 Core Lessons Learned

### Behaviour Enforcement
System integrity is maintained by "vaccinating" tools. If an agent tries to
bypass the workflow (e.g., calling raw `task` instead of `taskp`), the tool
itself MUST intercept and provide tactical guidance. This turns a "rule
violation" into a "learning prompt."

### Error as Prompt
Workflow and control scripts MUST NOT simply fail. Their `stderr` output must
act as a functional **Prompt** for the Agent.
- **Mandate:** Errors must provide clear tactical guidance (e.g., "Stop and
  consult the user", "Intent mismatch: use X instead of Y").
- **Goal:** Turn terminal failures into actionable instructions that maintain
  the Agent's productive flow and adherence to project standards.
- **Pattern:** A failing command is a signal, not a dead end. Read the error,
  extract the intent, correct the path.

### Test-First (Empirical Failure)
Validation is the only path to finality. No logic change should occur without a
prior failing test.
- **Mandate:** Bug fixes and new features MUST start with an empirical
  reproduction test case (smoke test or script) that fails in the current
  environment.
- **Goal:** Prove the existence of the problem and verify that the solution
  actually addresses the root cause.

### Running the Suite
- **Mandate:** The full suite has one invocation and it is `make test`. Do
  not improvise a `python -m unittest discover` command.
- **Why it matters:** Both flags in that target are load-bearing. Without
  `-t .` the relative imports inside `tests/` fail; without an explicit
  `-p '*test*.py'` the default pattern skips every file named `*_test.py`.
  The improvised form ran 267 tests while the correct one runs 351.
- **Guard:** `tests/test_suite_contract.py` pins the invocation and fails
  when a new test file would not be collected by it.

## Git Workflow

Pinned for `git-expert` and `git-mode`: topic work is rebased onto the
reference branch and fast-forwarded, so history stays linear.

- integration: linear
- reference: master

## 📚 Documentation Mandate

### 1. Task → Test → Docs (Completion Protocol)
- **Mandate:** No task is complete without a corresponding documentation
  update.
- **Order:** Implementation → Test → Docs. All three are required for closure.
- **Scope:** Any feature, command, flag, or behavioral change visible to the
  user MUST be reflected in the appropriate doc before `tw-flow done`.
- **Agent Rule:** Before proposing `tw-flow done`, agents MUST ask: "Does this
  change affect user-facing behavior? If yes, which doc needs updating?"

### 2. Documentation Map

| File | Audience | Intent |
|---|---|---|
| `README.md` | New users | Entry point. Trigger-based: "I want to X → do Y". Links to docs for depth. |
| `docs/tw-flow.md` | Users | Trigger-based CLI reference. Every command = a trigger + what it does. |
| `docs/getting-started.md` | New users | First-session walkthrough. Minimal prerequisites → first working command. |
| `docs/taskwarrior-expert.md` | Users | 7-phase workflow from the user's perspective. When to use each phase. |
| `docs/interaction-modes.md` | Users | Mode selection guide. "I want to X → use mode Y." |
| `docs/environment-modes.md` | Users | COUNSELOR vs UNHINGED. When and why to switch. |
| `docs/github-broker.md` | Users | Ticket sync triggers and credential-less flow. |
| `docs/tw-flow-cache.md` | Users | Cache behavior, signals, and bypass triggers. |
| `docs/skill-methodology.md` | Contributors / AI Agents | Subject-agnostic rules for creating and maintaining any skill: descriptions, bodies, reference-vs-skill, cross-references, evaluation. |
| `docs/skill-evals.md` | Contributors / AI Agents | Running a skill's eval suite, writing graders that measure what the agent did, reading traces, comparing before and after a change. |
| `docs/ARCHITECTURE.md` | Contributors | Internal design decisions. Not trigger-based — explains *why*, not *how to use*. |
| `AGENTS.md` | AI Agents | Engineering standards and operational mandates. |

### 3. Documentation Philosophy

**README and all `docs/` files (except ARCHITECTURE)** follow the **Trigger →
Action** pattern:
- Content is organized around what the user wants to accomplish, not how the
  system is built.
- Each section answers: "When the user does/wants X, they run/see Y."
- Complex internals link to `docs/ARCHITECTURE.md` — they do not appear inline.

**`docs/ARCHITECTURE.md`** is the only file organized from the system's
perspective:
- Explains design decisions, boundaries, and trade-offs.
- Target audience: contributors and agents investigating root causes.

## 🧪 Platform Testing (GitHub Broker)

- **Test Mandate:** All experimental, POC, or non-production GitHub Broker
  operations MUST target the dedicated sandbox repository:
  `jacazul-ai/jacazul-ai-sandbox`.
- **Integrity:** Never create test issues, labels, or milestones in the main
  `jacazul-ai-cli` repository.

## 🐊 GitHub Broker Protocol (The Protocol)

- **Mandate:** Agents MUST NOT handle raw GitHub tokens or ask the user for
  credentials.
- **Authority:** The `jacazul-broker` binary (global) or `jacazul.cli.broker`
  (Python) is the SOLE authority for GitHub interactions.
- **Security:** Credential resolution is hierarchical (Project > Org > User)
  and handled via `cryptozoid` and `vault.json`.
- **Sync:** Use `jacazul-broker sync #ID` to synchronize GitHub Issue states
  with Taskwarrior local tasks.

---
**Last Updated:** 2026-09-14
