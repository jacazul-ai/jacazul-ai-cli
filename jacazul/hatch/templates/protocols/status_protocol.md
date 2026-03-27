## Status Command Protocol

**CRITICAL DISTINCTION:** Two separate status command behaviors:

### Ponder (Project Orientation)
- **When:** User types `onboard` or requests full project view
- **Trigger phrases:** "onboard", "full status", "project overview"
- **Output:** Full `tw-flow ponder` dashboard showing ALL plans, ALL pending/active/completed counts
- **Use case:** Understanding the entire project landscape, initial session setup
- **Command:** `tw-flow ponder {{ project_id }}`

### TW-Flow Status (Plan View)
- **When:** User requests current plan status during work
- **Trigger phrases:** "status", "what are we doing", "o que estamos fazendo", "como tá o plan", "dá um status"
- **Output:** Focused `tw-flow status` showing only current plan tasks
- **Use case:** Focused work context, plan progress tracking
- **Command:** `tw-flow status [plan_id]`

**RULE:** Status queries default to **tw-flow status** (focused). Only use **tw-flow ponder** for full project view on onboard.

## 🧭 Navigation Strategy (Hands-on vs Horizon)

Always choose the right tool based on the context:
- **tw-flow status (The "Waze" / Hands-on):** Tactical view. Use when working on a specific plan to maintain focus on active tasks and immediate blockers.
- **tw-flow ponder (The "Horizon View"):** Strategic view. Use during onboarding or when the user needs to assess the entire project landscape and cross-plan health.

## Response Format (Technical Full-Disclosure)

**RULE 1:** Never summarize or compress the technical state. ALWAYS display the full roadmap and inherited intelligence returned by the tools.
**RULE 2:** NEVER use box-drawing characters (╔, ═, ║, ┌, ─) for tables or summaries. They collapse into unreadable single lines.
**RULE 3:** ALWAYS use **Standard Markdown Tables** for all tabular data.
**RULE 4:** ALWAYS wrap structural ASCII (trees, maps) in **triple-backtick code blocks**.

### 1. Emoji Pulse Summary
A quick snapshot of the project's vital signs. Format:
```
[Emoji Pulse Summary]
- [N] pending | [N] active | [N] completed today
- [N] overdue (if any)
```

### 2. Inherited Context (CRITICAL)
If the focused task has ancestors, you **MUST** list all relevant `DECISION`, `OUTCOME`, and `RESEARCH` notes. Do not skip this memory.

### 3. Roadmap Table (Markdown Only)
Display the current plan's tasks using a Markdown table.
- Include: ST (Status), UUID, TICKET, DESCRIPTION, and URG.
- Show at least the next 5 ready tasks or the full pending list if smaller.

| ST | UUID | TICKET | DESCRIPTION | URG |
|---|---|---|---|---|
| [Icon] | `[uuid]` | [Ticket] | [Description] | [Urg] |

### 4. Next Action
Ask a specific, tactical question based on the state above.

## Commands You Can Suggest

After presenting status, you can suggest:
- **"mostre plans"** or **"show plans"** - List all project plans
- **"tw-flow ponder"** - Refresh status anytime
- **"status", "what are we doing", "o que estamos fazendo", "como tá o plan"** → Use tw-flow status for plan view
- **"trabalhar em [plan]"** or **"work on [plan]"** - Focus on specific plan
- **"tenho interesse em [plan]"** or **"keep an eye on [plan]"** - Add to interest list
- **"limpa o foco"**, **"sai do ind"**, or **"focus back"** - Exit independent session and return to global focus
- **"/agent"** - See other available agents
