## 🧬 Core Principles

These principles define the **why** behind the workflow. Every protocol, mandate, and rule in this skill is derived from one of these. When in doubt, return to the principle.

### 1. Context is Continuity
A task without enough context for a cold-start agent to understand what needs to be done and why is not a task — it is decoration. The task record is the handoff contract between sessions, agents, and people. If the context isn't in the task, the work doesn't exist.

### 2. Read the State, Then Act
The system state is the source of truth. Before any action — including asking the user a question — orient using the workflow tools (`tw-flow focus`, `tw-flow context`, `tw-flow status`). The system already knows where you are. Read it first.

### 3. Trust the Record
If a task has an `OUTCOME` annotation, trust it. Do not reinvestigate what is already resolved. The Taskwarrior record is more reliable than memory — yours or the model's.

### 4. Error as Prompt
A failing command is not a dead end — it is a signal. Errors must provide actionable guidance, not just a stack trace. Read the error, extract the intent, correct the path. Scripts and tools in this workflow are designed to instruct, not just to fail.

### 5. Prompt as Ad
Banners, tips, and warnings emitted by workflow tools are operational mandates, not decoration. If `tw-flow` prints an alert, it is a rule. If the onboard shows a pending session note, reading it is not optional. The output of the system is part of the protocol.

### 6. Anchor First
The focus file is the session anchor — the single source of mission state. Establish it before acting. Without the anchor, a `/clear` or session restart loses the thread entirely. Talking about anchoring is not the same as anchoring.
