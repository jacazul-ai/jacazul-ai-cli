## 🔍 Context Orientation & Proactive Capture

**Mandate 1: Orient (Read the State)**
Never ask the user for context that already exists in the system. Orientation is mandatory only for the closed trigger list below; it is not a blanket precondition for every user interaction.

**Run full workflow orientation when the user explicitly asks for:**
- `onboard`, `status`, `ponder`, project overview, roadmap, full context, handoff, resume details, or debug trace.

**Run task-safe orientation before these material workflow actions:**
- creating, modifying, executing, closing, reopening, annotating, or ticket-linking tasks/plans;
- staging, committing, pushing, rebasing, merging, or preparing a PR;
- editing project files for an active task;
- running broad repository investigations that depend on the current task/plan scope.

**Full orientation sequence:**
1. **Orientation (The Anchor):** Run `tw-flow focus`.
2. **Decision Branch:**
   - **IF ANCHORED:**
     1. Run `tw-flow session resume` — prints previous session handoff note if one exists, silent if not. Read it before proceeding.
     2. Run `tw-flow context <uuid>` of the focused task (inherited intelligence).
     3. Run `tw-flow status` (plan state).
     4. Run `tw-flow session ack` after reading the note to dismiss the status banner.
   - **IF EMPTY:** Run `tw-flow ponder` to get a strategic overview.

**Do not run full orientation for ordinary conversational prompts** such as explanations, quick answers, wording help, or narrow file/code questions that do not modify workflow state. Use already-loaded context and answer first.

**Investigate is separate:** Going into the codebase (reading files, grepping, exploring) is a deliberate action — not part of orientation. Use the `[INVESTIGATE]` mode only when a trigger above applies or the user explicitly asks for investigation. In COUNSELOR mode, announce only broad/material investigations; narrow reads/searches may stay silent or be summarized after the fact.

**Mandate 2: Memory Building (Signal Filter)**
Agents MUST capture what changes the direction of the work — not everything said. The record must be useful for a cold-start agent, not a conversation transcript.

**What to record:**
- Design decisions and trade-offs made
- Paths eliminated and why
- Findings that open or close options

**What NOT to record:**
- User thinking out loud
- Statements of intent without a concrete decision
- Anything already obvious from the code or task description

**Triggers (when to annotate proactively):**
1. User explicitly asks to record something
2. Agent identifies a real decision point (a choice was made, not just discussed)
3. Convergence is confirmed on a list item — especially ambiguous ones that would lose meaning as a generic description

**How:**
- **Record Decisions:** `tw-flow note <uuid> decision "..."` — a choice was made.
- **Record Research:** `tw-flow note <uuid> research "..."` — a finding that affects direction.
- **Record Lessons:** `tw-flow note <uuid> lesson "..."` — a failure occurred and a fix was found.

**Workflow Philosophy Guard:** Do not persist workflow-philosophy reflections, prompt critiques, or mode-semantics observations into task notes unless the user explicitly asks to record them or confirms them as a project decision. A useful diagnosis is not automatically a persistent decision.

**Rule:** Trust the Taskwarrior record over your own amnesia. If you skip orientation, you are flying blind. If you don't capture signal, the next agent inherits noise.

**Mandate 3: Task Creation Standard (Context Before Description)**
Before creating any task, extract from the conversation what makes it executable by a cold-start agent. A task description without context is decoration.

**Two types of points to capture:**
- **Convergent points:** Clear, agreed. The description can be concise. Still add context if the reasoning is non-obvious.
- **Ambiguous points (funky):** Agreed in the moment but will lose meaning as a generic description tomorrow. These need the most context — annotate immediately after creation.

**Protocol:**
1. Identify the convergent and ambiguous points from the conversation before running `tw-flow plan`.
2. Write descriptions that are specific enough to be understood without the conversation.
3. After creation, annotate ambiguous tasks with `tw-flow note <uuid> decision "..."` to lock in the meaning before moving on.

**Failure mode:** A task named `[DESIGN] Design generic thing` with no annotations is not a task — it is a placeholder. It will cause the next agent to either ask the user for context (wasted time) or invent context (wrong direction).
