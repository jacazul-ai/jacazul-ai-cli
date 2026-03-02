# Copilot CLI Behavior & Diagnostics

This document captures internal diagnostics and behavioral patterns of the Jacazul agent within the GitHub Copilot CLI environment.

## 🐊 Session Initialization

When starting a session with `jacazul-copilot`, the environment is bootstrapped and the custom agent is selected.

```text
● Environment loaded: 3 custom instructions, 4 skills
● Selected custom agent: jacazul

❯ The anchored persona for this session is Jacazul (Jacaré Azul). 
  Activate the 'jacazul-engine' and 'taskwarrior-expert' skills immediately. 
  Wait for the 'onboard' command to enter the workflow.

● skill(jacazul-engine)
● skill(taskwarrior-expert)
● 🐊 Jacazul aqui. Skills ativadas e prontas. Esperando o comando onboard pra entrar no fluxo.
```

## ⚠️ Tool Availability & Sandboxing

The Copilot CLI environment may dynamically change available tools (e.g., `<tools_changed_notice>`). If tools like `bash`, `read_file`, or `write_file` are removed, the agent enters a "technical limbo" where it can provide orientation but cannot execute commands.

### Diagnostic Matrix

| Status | State | Impact |
| :--- | :--- | :--- |
| ✅ Skills | Loaded | Full access to protocols and task data. |
| ⚠️ Tools | Removed | Blocked from technical execution (no bash/write). |
| ❌ Result | Limbo | Limited to static analysis and status readout. |

## 🛠️ Key Concepts & Commands

| Term | Meaning |
| :--- | :--- |
| **onboard** | Gateway to the 7-phase workflow (initialized context). |
| **ponder** | ASCII Tactical Dashboard for initiative overview. |
| **taskp** | The primary **Project-Aware Wrapper** for Taskwarrior. |
| **rtask** | **Administrative Bypass** to the real binary (Manual Use Only). |

## 🧠 Skill Architecture: Horizontal vs. Vertical

The project transitioned from a **Cascading (Vertical)** architecture to a **Horizontal (Direct)** one to ensure resilience and context efficiency.

- **Legacy (Cascade):** `Jacazul` -> `jacazul-engine` -> `taskwarrior-expert`. (Fragile, high memory overhead).
- **Modern (Horizontal):** `Jacazul` activates `jacazul-engine` and `taskwarrior-expert` **directly and simultaneously**.

This ensures independence: if one skill fails, the agent maintains access to the other specialized mandates.

---
**Last Updated:** 2026-03-02
