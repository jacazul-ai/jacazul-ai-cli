# JIT Forge Lifecycle & Onboarding

This document details the dynamic initialization process of the Jacazul AI CLI ecosystem, known as the **JIT Prompt Forge**. It explains how instructions are generated, loaded, and executed to maintain a productive flow state.

## 🏗️ 1. The Forge (Hatch Phase)

Every session begins with the **Hatch** process. Unlike traditional static prompts, Jacazul instructions are forged just-in-time to reflect the current project state and selected persona.

1.  **Trigger:** Running a CLI wrapper (e.g., `jacazul-gemini`) executes the `scripts/bootstrap/hatch` script.
2.  **Engine:** The `scripts/jacazul/hatch.py` engine is invoked.
3.  **Templating:** The engine reads fragment templates (`.tmpl`) from `scripts/jacazul/` and assembles them into a unified `SKILL.md` (for Gemini) or individual agent files (for Copilot/Opencode).
4.  **Persona Anchoring:** The engine consults `persona.json` to determine which identity (Jacazul or Cortana) should be marked as **ANCHORED**.

## 🚀 2. The Initialization (Wake Up)

When the AI client (Gemini, Copilot, etc.) starts, it loads the forged instructions. At this stage, the agent is in a **Standby State**:

-   **Automatic Actions:** It activates required skills (e.g., `taskwarrior-expert`).
-   **Passive Monitoring:** It waits for the user's first directive or the explicit `onboard` command.

## 📋 3. The Onboard Ritual (Flow Entry)

The `onboard` command is the official gateway to the project's tactical state. It follows a strict hierarchical protocol defined in the **Workflow Loop**.

### Step A: Phase 0 - Context-First (History)
The agent MUST understand what happened before touching the present.
-   It identifies the **active** or **hottest** task (highest urgency).
-   It runs `tw-flow context <uuid>` to read inherited outcomes, decisions, and lessons.
-   **Goal:** Prevent re-investigation and honor previous architectural decisions.

### Step B: Phase 1 - Status/Ponder (Orientation)
The agent determines where the user is standing.
-   It runs `tw-flow focus` to check for an anchored initiative.
-   **If Anchored:** It runs `tw-flow status` (The "Waze" view - tactical and focused).
-   **If NO Anchor:** It runs `ponder` (The "Map" view - global and strategic).

### Step C: The Insight & Stop
-   The agent synthesizes the Context (Phase 0) and Status (Phase 1) into a concise tactical summary.
-   **Mandatory Stop:** The agent presents the summary and **STOPS**. It will not perform any automated tasks or file modifications until explicitly directed by the user.

## 🎯 4. The Interaction Cycle

Once onboarded, the session follows the iterative **Workflow Loop**:
1.  **Plan:** Break goals into initiatives and tasks.
2.  **Execute:** Pick a task, read its inherited context, and work.
3.  **Record:** Annotate decisions (`tw-flow note`) and outcomes (`tw-flow outcome`).
4.  **Close:** Verify the result and finalize the task.

---
**Core Philosophy:** *Understand the past, orient in the present, and act only on command.*
