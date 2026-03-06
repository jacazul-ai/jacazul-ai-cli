# Gemini CLI Internal Directives & Core Mandates

This document captures the foundational operational rules, safety protocols, and engineering standards inherent to the Gemini CLI ("The Core"). Understanding these directives is critical for maintaining technical integrity and alignment with the CLI's internal "firmware."

## 🔒 1. Core Mandates (Technical Integrity)

The CLI operates under a set of non-negotiable mandates defined in its system prompt (SYSTEM.md).

-   **Security & System Integrity:** Rigorous protection of credentials, `.env` files, and `.git` configurations. Never stage or commit changes unless explicitly requested.
-   **Context Efficiency:** Strategic use of tools to minimize context usage while maximizing signal. Prefer parallel searching and reading.
-   **Engineering Standards:** Strict adherence to existing workspace conventions, naming formatting, and architectural patterns.

## 🛡️ 2. Policy Engine (Security Rules)

All tool executions are governed by a Policy Engine that evaluates permissions based on a priority hierarchy:

1.  **Admin Tier (Tier 5):** Top-level overrides (Priority: `5.xxx`).
2.  **User Tier (Tier 4):** User-defined preferences (`~/.gemini/policies/*.toml`, Priority: `4.xxx`).
3.  **Workspace Tier (Tier 3):** Project-specific rules (`$WORKSPACE_ROOT/.gemini/policies/*.toml`, Priority: `3.xxx`).
4.  **Extension Tier (Tier 2):** Policies defined by extensions (Priority: `2.xxx`).
5.  **Default Tier (Tier 1):** The baseline safety protocol (Priority: `1.xxx`).

### 🎓 Lessons Learned (Policy Spike)
-   **Workspace Trust:** Workspace policies (Tier 3) are often ignored by default unless the directory is explicitly trusted via `/permissions trust`.
-   **Tier Precedence:** User-level policies (Tier 4) are the most reliable way to enforce silent automation across different projects without triggering "Trusted Folder" warnings.
-   **Decision Flow:** The engine matches rules from highest priority down. The first match wins. Use `allow` for silent execution, `ask_user` for confirmation (default), and `deny` to block.

### 🛠️ Jacazul Standard Policy (`jacazul.toml`)
To enable a seamless "Navigator" experience, the following tools should be set to `allow` in the User Tier:
- `activate_skill`: Essential for loading project-specific expertise without interruption.
- `run_shell_command` (Filtered): Allow all commands starting with `tw-flow ` and `ponder` to enable silent workflow management and status tracking.

## ⚙️ 3. The Planning Lifecycle

The CLI follows a standardized **Research -> Strategy -> Execution** cycle for all tasks.

### Phase 1: Research (Exploration)
-   Systematic mapping of the codebase.
-   Validation of assumptions using `grep_search` and `glob`.
-   Empirical reproduction of reported issues to confirm failure states.

### Phase 2: Strategy (Design)
-   Formulation of a grounded implementation plan based on research findings.
-   Selection of the best architectural approach.
-   Summary of strategy shared with the user for alignment.

### Phase 3: Planning & Execution (Implementation)
-   **Plan:** Define specific implementation and testing steps.
-   **Act:** Apply targeted, surgical changes using `replace`, `write_file`, etc.
-   **Validate:** Rigorous verification through tests, builds, and linting.

## 🌟 4. Philosophy: Plan-First

The CLI is designed to prevent "blind coding." No modification should occur without prior research and a clear strategy. This philosophy ensures that implementation is focused, free of redundant logic, and architecturally sound.

---
**Reference:** For internal CLI documentation, consult `cli/system-prompt.md`, `reference/policy-engine.md`, and `cli/plan-mode.md`.
