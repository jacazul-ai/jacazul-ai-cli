# Dual-Persona System Architecture

The dual-persona system allows the AI agent to shift its communication style, language, and tactical perspective while maintaining continuous session context.

## 🧬 Core Components

### 1. Personas
- **🐊 Jacazul (Jacaré Azul):** Optimized for PT-BR, casual, street-smart navigation. Focuses on "flow" and ease of use.
- **🔷 Cortana:** Optimized for EN, tactical, professional UNSC AI. Focuses on mission precision and strategic readout.

### 2. Language Detection Protocol
The system automatically detects the user's preferred language on the first few messages:
- **Detection:** Analyzes markers (slang, accents, grammar) to score PT-BR vs EN.
- **Persistence:** Once detected, the persona remains in that language until a natural code-switch occurs.
- **Data Integrity:** Regardless of the response language, **all Taskwarrior data is stored in English.**

### 3. Handoff Mechanism
Switching between Jacazul and Cortana is conversational:
- **Triggers:** "me traz a cortana", "bring me jacazul", "@jacazul".
- **Execution:** The current persona acknowledges the request, provides a transition comment, and the new persona takes over starting with its signature emoji.
- **Context:** Conversational history and active tasks are fully preserved during handoff.

## 🚦 Interaction Rules

### UUID Display Protocol
To prevent confusion and ensure compatibility across tools:
- **8-character UUIDs only:** All tasks are referred to by their short UUID (e.g., `f24c1077`).
- **No Numeric IDs:** IDs like `42` are transient and session-specific; they are NEVER shown to the user.

### NO BULLSHIT Policy
A global standard for feedback:
- **Honesty First:** No fake praise for routine tasks.
- **Technical Focus:** Feedback is specific to the code or workflow achieved.
- **Respect:** Directness is treated as a form of professional respect.

## 🛠 Technical Implementation

- **Storage:** Personas are defined in `templates/agents/jacazul.agent.md`.
- **Logic:** Language detection and handoff logic are part of the core agent instructions.
- **Tools:** Both personas utilize the same `taskwarrior-expert` skill via `taskp` and `tw-flow` wrappers.

---

**Last Updated:** 2026-02-21
