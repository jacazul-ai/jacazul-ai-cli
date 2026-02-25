# Gemini CLI Sandboxed Manifesto

This document defines the foundational engineering standards, architectural patterns, and operational philosophies for the Gemini CLI Sandboxed project.

## 🏛 Architectural Boundaries

### Structure vs. Dynamics (Setup vs. Runtime)
- **Setup (Structure - `scripts/configure`):** One-time environment preparation. Handles immutable filesystem changes: directory creation, symbolic links in `~/bin`, and initial template deployment. It sets the stage but does not run the show.
- **Runtime (Dynamics - `scripts/bootstrap/`):** Session-specific initialization. Handles mutable configuration and dynamic environment detection: injecting environment variables, surgical updates to settings JSONs (e.g., `experimental.enableAgents`), and locating system resources (e.g., finding the real `task` binary).

## 🔊 Logging Philosophy

The project adheres to a "Silent by Default" logging policy to maintain CLI usability and focus.

- **Standard Execution:** Silence is mandatory if the environment is healthy and checks pass.
- **State Changes:** Output MUST be emitted when the system state is modified (e.g., "Creating directory X").
- **Verification:** Verification of existing resources MUST stay silent unless `DEBUG=true`.
- **Debug Mode:** Enabled via `DEBUG=true`. Provides full verbosity for troubleshooting.
- **Dry Run:** Enabled via `DRY=true`. Allows verifying the entire bootstrap process (Dynamics) without executing the final CLI binary.
- **Error Handling:** Errors MUST be emitted to `stderr` with clear instructional context.

## 🔒 Engineering Mandates

### 1. Taskwarrior Abstraction
- **Mandate:** Agents and tools MUST NOT invoke the raw `task` binary directly.
- **Protocol:** All operations MUST go through the `taskp` project-aware wrapper or the `tw-flow` workflow manager.
- **Isolation:** Project isolation via `TASKDATA` MUST be preserved at all costs.

### 2. Context Preservation
- **Mandate:** Closing a task without documentation is FORBIDDEN.
- **Protocol:** The `tw-flow done` command requires an `OUTCOME:` annotation. Discarded tasks MUST include an automatic audit record.

## 🧬 Interaction Standards
- **UUID Priority:** Tasks MUST be referenced by their 8-character UUID. Numeric Task IDs are transient and MUST NOT be shown to users.
- **Persona Voice:** Responses MUST align with the active persona (Jacazul/Cortana) and the detected user language, while persistent data (tasks, commits) remains in English.

---
**Last Updated:** 2026-02-21
