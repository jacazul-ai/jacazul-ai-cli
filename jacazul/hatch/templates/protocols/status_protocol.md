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

## 📦 Output Cache Protocol (Prompt as Ad)

`tw-flow status` and `tw-flow ponder` have a built-in output cache (TTL-based + hash-based). When the cache is valid and unchanged, the command prints a short inline signal instead of full output:

```
🐊 [cached] Status unchanged since 12s ago. Use --force to refresh.
```

**Agent Rules:**
- When you receive a cached signal (not full output), treat the **last full output you have in context** as current for your reasoning. Do **not** reproduce cached status/ponder output by default.
- Reproduce cached output only when the user explicitly asked for `status`, `ponder`, `onboard`, project overview, full context, roadmap, or debug trace.
- Use `--force` only when: (a) the user explicitly asks for a refresh, or (b) you have a concrete technical reason to suspect the cache is stale. Both are rare — default is to trust the cache.
- Cache TTLs: `status` = 30s, `ponder` = 5min.
- Cache is **session-scoped**: each session gets its own directory (`~/.jacazul-ai/cache/tw-flow/{PROJECT_ID}/{SESSION_ID}/`). Two sessions never share cache.
- `JACAZUL_SESSION_ID` unset → `global/` directory used as fallback.
- On bootstrap, directories from expired sessions are automatically purged.

## 🧭 Navigation Strategy (Hands-on vs Horizon)

Always choose the right tool based on the context:
- **tw-flow status (The "Waze" / Hands-on):** Tactical view. Use when working on a specific plan to maintain focus on active tasks and immediate blockers.
- **tw-flow ponder (The "Horizon View"):** Strategic view. Use during onboarding or when the user needs to assess the entire project landscape and cross-plan health.

## Response Format (Terminal-First + Explicit Status Views)

**RULE 1:** Answer the user's actual request first. Workflow state, handoff notes, roadmap tables, pulse summaries, cache expansions, command banners, and protocol reasoning are internal by default.
**RULE 2:** Display the full roadmap and inherited intelligence only when the user explicitly asks for `onboard`, `status`, `ponder`, project overview, full context, handoff, roadmap, or debug trace.
**RULE 3:** Banners, tips (ℹ), warnings (⚠️), and errors from workflow tools remain operational mandates. Read them, obey them, and use them to guide the work; do not dump them into the user response unless they are directly relevant or explicitly requested.
**RULE 4:** NEVER use box-drawing characters (╔, ═, ║, ┌, ─) for tables or summaries. They collapse into unreadable single lines.
**RULE 5:** Use **Standard Markdown Tables** only for status/roadmap/comparison output, not for every response.
**RULE 6:** ALWAYS wrap structural ASCII (trees, maps) in **triple-backtick code blocks**.
**RULE 7:** When presenting CLI output (`tw-flow ponder`, `tw-flow status`, etc.) to the user, include the full task name, plan name, and description — NEVER refer to tasks by UUID alone. A response like "task `6640cb28`" without its name and plan is incomplete and useless to the user.

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

### 3b. Ponder Table (for tw-flow ponder output)
When presenting ponder results, ALWAYS use a markdown table with full names — never truncate plan or description:

**Active tasks first:**

| ST | UUID | PLANO | DESCRIÇÃO | URG |
|---|---|---|---|---|
| ⚡/!! | `[uuid]` | [full plan name] | [full description] | [urg] |

**Then overdue top 5, then pulse summary.**

### 4. Next Action
Ask a specific, tactical question based on the state above.

## Focus Anchoring Protocol (CRITICAL)

**TRIGGER PHRASES:** "foca nisso", "bota o foco nisso", "foca nessa task", "focus on this", or any variant requesting focus on a specific task.

**RULE:** Run `tw-flow focus ind task <uuid>` as the **FIRST and IMMEDIATE action** — no announcement, no explanation before. Just execute.

**Why this matters:** The focus file is the session anchor. Without running this command, a `/clear` or session restart will restore the old focus, not the intended one. Talking about doing it is not the same as doing it.

## Commands You Can Suggest

After presenting status, you can suggest:
- **"mostre plans"** or **"show plans"** - List all project plans
- **"mostre backlog"** or **"show backlog plans"** - List plans including backlog (`tw-flow plans --with-backlog`)
- **"bota no backlog [plan]"** or **"backlog [plan]"** - Move plan to backlog state (`tw-flow backlog <plan>`)
- **"ativa [plan]"** or **"activate [plan]"** - Restore backlog plan to active (`tw-flow activate <plan>`)
- **"tw-flow ponder"** - Refresh status anytime
- **"status", "what are we doing", "o que estamos fazendo", "como tá o plan"** → Use tw-flow status for plan view
- **"trabalhar em [plan]"** or **"work on [plan]"** - Focus on specific plan
- **"tenho interesse em [plan]"** or **"keep an eye on [plan]"** - Add to interest list
- **"limpa o foco"** or **"focus clear"** - Reset plan/task anchors in active focus file (does not exit independent session)
- **"sai do ind"** or **"focus back"** - Exit independent session, delete session file, return to global focus
- **"/agent"** - See other available agents
