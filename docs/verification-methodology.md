# Jacazul Verification Methodology

This document defines the high-integrity verification protocols used by the Jacazul AI agent to ensure behavioral correctness and structural integrity, even in tool-restricted environments.

## 🚀 The 5-Step Verification Flow

When a technical request is received, the agent follows this sequence to ensure success and visibility:

### 1. REQUISIÇÃO (Request)
- The user issues a command or describes a goal.
- **Goal:** Identify the ultimate objective and any explicit constraints.

### 2. ANÁLISE DE ESCOPO (Scope Analysis)
- The agent checks available tools (e.g., `bash`, `view`, `skill`).
- **Detection:** "Do I have high-level tools (`create`, `edit`)? No. Do I have `bash`? Yes."
- **Decision:** Select the most resilient execution path (Direct tool vs. Bash workaround).

### 3. EXECUÇÃO DIRETA (Direct Execution)
- Apply the change or perform the action.
- **Workaround Protocol:** If specialized tools are missing, use standard bash redirection (`cat >`, `echo >>`, `touch`) to achieve the result.

### 4. VERIFICAÇÃO (Verification)
- **Mandatory:** Never assume a command succeeded just because it didn't return an error.
- **Action:** Use exploration tools (`ls -la`, `cat`, `grep`, `view`) to confirm the state change on the filesystem or database.

### 5. RESPOSTA (Response)
- Present the result to the user using the active persona (Jacazul/Cortana).
- **Signal:** Clear confirmation of what was done and where the system stands.

---

## 🏥 Health-Check Philosophy

The environment must not "fail silently." Every critical path must have a gatekeeper.

1.  **Binary Verification:** Before executing a workflow, check if the required binaries (`tw-flow`, `taskp`) exist and are executable in their expected locations.
2.  **Path Integrity:** Verify that symbolic links point to valid targets within the current project root.
3.  **Horizontal Resilience:** Avoid cascading skill dependencies. Activate required experts directly to ensure that a failure in one subsystem does not blind the entire agent.

## 🛠️ Execution vs. Delegation

| Scenario | Strategy |
| :--- | :--- |
| Simple Filesystem Task | Direct execution via `bash` workaround. |
| Complex Logic / Refactoring | Delegate to specialized skill (e.g., `python-expert`). |
| Database / Workflow Change | Delegate to `taskwarrior-expert` via `tw-flow`. |

---
**Core Mandate:** *Validation is the only path to finality. Verify first, respond second.*
