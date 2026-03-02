# Gemini CLI Internal Directives & Core Mandates

This document captures the foundational operational rules, safety protocols, and engineering standards inherent to the Gemini CLI ("The Core"). Understanding these directives is critical for maintaining technical integrity and alignment with the CLI's internal "firmware."

## 🔒 1. Core Mandates (Technical Integrity)

The CLI operates under a set of non-negotiable mandates defined in its system prompt (SYSTEM.md).

-   **Security & System Integrity:** Rigorous protection of credentials, `.env` files, and `.git` configurations. Never stage or commit changes unless explicitly requested.
-   **Context Efficiency:** Strategic use of tools to minimize context usage while maximizing signal. Prefer parallel searching and reading.
-   **Engineering Standards:** Strict adherence to existing workspace conventions, naming formatting, and architectural patterns.

## 🛡️ 2. Policy Engine (Security Rules)

All tool executions are governed by a Policy Engine that evaluates permissions based on a priority hierarchy:

1.  **Admin Tier:** Top-level overrides.
2.  **User Tier:** User-defined preferences.
3.  **Workspace Tier:** Project-specific rules.
4.  **Default Tier:** The baseline safety protocol.

The engine can `allow`, `deny`, or `ask_user` for each tool execution, ensuring a "Security First" environment.

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
