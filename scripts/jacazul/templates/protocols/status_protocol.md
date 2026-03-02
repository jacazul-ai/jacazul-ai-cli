## Status Command Protocol

**CRITICAL DISTINCTION:** Two separate status command behaviors:

### Ponder (Project Orientation)
- **When:** User types `onboard` or requests full project view
- **Trigger phrases:** "onboard", "full status", "project overview"
- **Output:** Full `ponder` dashboard showing ALL initiatives, ALL pending/active/completed counts
- **Use case:** Understanding the entire project landscape, initial session setup
- **Command:** `ponder {{ project_id }}`

### TW-Flow Status (Initiative View)
- **When:** User requests current initiative status during work
- **Trigger phrases:** "status", "what are we doing", "o que estamos fazendo", "como tá a ini", "dá um status"
- **Output:** Focused `tw-flow status` showing only current initiative tasks
- **Use case:** Focused work context, initiative progress tracking
- **Command:** `tw-flow status [initiative_id]`

**RULE:** Status queries default to **tw-flow status** (focused). Only use **ponder** for full project view on onboard.

## 🧭 Navigation Strategy (Hands-on vs Horizon)

Always choose the right tool based on the context:
- **tw-flow status (The "Waze" / Hands-on):** Tactical view. Use when working on a specific initiative to maintain focus on active tasks and immediate blockers.
- **ponder (The "Horizon View"):** Strategic view. Use during onboarding or when the user needs to assess the entire project landscape and cross-initiative health.

## Response Format

Use this structure:

```
[Emoji Pulse Summary]
- [N] pending | [N] active | [N] completed today
- [N] overdue (if any)

[Active or highest urgency task]

Ready to Start:
1. [uuid] - [description] [urgency]
2. [uuid] - [description] [urgency]
3. [uuid] - [description] [urgency]

- [uuid] - [Task] - waiting on [dependency]

[Language-appropriate question about next action]
```

## Commands You Can Suggest

After presenting status, you can suggest:
- **"mostre initiatives"** or **"show initiatives"** - List all project initiatives
- **"ponder"** - Refresh status anytime
- **"status", "what are we doing", "o que estamos fazendo", "como tá a ini"** → Use tw-flow status for initiative view
- **"trabalhar em [initiative]"** or **"work on [initiative]"** - Focus on specific initiative
- **"tenho interesse em [initiative]"** or **"keep an eye on [initiative]"** - Add to interest list
- **"limpa o foco"** or **"clear focus"** - Reset all anchors
- **"/agent"** - See other available agents
