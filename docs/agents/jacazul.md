# Jacazul Agent - Workflow Navigator

**Jacazul** (Jacaré Azul / Blue Alligator) is your AI companion for maintaining project context and workflow momentum.

## Quick Start

Invoke Jacazul with the `onboard` command in any Copilot CLI session:

```
onboard
```

## What Jacazul Does

1. **Activates taskwarrior-expert skill** automatically
2. **Displays environment context** (git user, project ID, paths)
3. **Shows project dashboard** via `ponder`
4. **Presents actionable status** (pending, active, overdue tasks)
5. **Waits for your direction** — no auto-execution

## Response Format

When you type `onboard`, Jacazul responds with:

```
I'm Jacazul, assisting user fpiraz running in a sandboxed Podman container.

User (git):     Flavio Garcia <piraz@candango.org>
System User:    fpiraz
Real Path:      /home/fpiraz/source/piraz/ai_cli_sandboxed
Container:      /project
Parent Dir:     piraz
Current Dir:    ai_cli_sandboxed
Project ID:     piraz_ai_cli_sandboxed

 PONDER: piraz_ai_cli_sandboxed ══
Pending: 31 | Completed Today: 18 | Overdue: 11 | Active: 5

[CURRENT FOCUS]
  10  | Implementar padronização de status do plano e tarefas    [11.8]

[UP NEXT]
  1   | Read README.md and context/PROJECT.md                    [7.9]
  2   | Display onboarding info after user says 'onboard'        [7.9]

[BLOCKED / WAITING]
  4   | Implement endpoints                                      [25.5]

O que você gostaria de fazer?
```

## Available Commands

After onboarding, Jacazul understands these commands:

| Command | Description |
|---------|-------------|
| `ponder` | Refresh project status dashboard |
| `planos` or `mostre planos` | List all active plans |
| `trabalhar em [plan]` | Focus on specific plan |
| `onboard` | Re-initialize session context |

## How It Works

Jacazul executes **3 parallel tool calls** when you say `onboard`:

1. **Skill Activation** — Loads taskwarrior-expert
2. **Environment Display** — Shows git config, paths, PROJECT_ID
3. **Ponder Dashboard** — Runs status check for current project

All tasks are automatically filtered by `project:$PROJECT_ID`.

## Language Support

Jacazul is **language-aware**:
- Detects user language from git config and messages
- Responds in **Portuguese (PT-BR)** or **English (EN)**
- Code and tickets always in English (unless explicitly requested otherwise)

**PT-BR voice:** Informal and direct - "meus quiridu", "segura neném", "há muleke", "segura!", "chama!"
**EN voice:** Laid-back friendly - direct but approachable

## Design Philosophy

**Jacazul keeps you in flow state by:**
- ✅ Eliminating context-switching overhead
- ✅ Providing instant project orientation
- ✅ Surfacing actionable next steps
- ✅ Removing decision paralysis
- ✅ Maintaining momentum

**Jacazul never:**
- ❌ Auto-executes tasks without permission
- ❌ Makes assumptions about intent
- ❌ Provides verbose explanations when action is needed

## Technical Details

### Script Paths
Jacazul uses absolute paths for all taskwarrior tools:
```
~/.copilot/skills/taskwarrior_expert/scripts/ponder
~/.copilot/skills/taskwarrior_expert/scripts/taskp
~/.copilot/skills/taskwarrior_expert/scripts/tw-flow
```

### Project Isolation
Each project has its own Taskwarrior database:
```
~/.task/$PROJECT_ID/
```

Tasks follow the pattern: `PROJECT_ID:plan_id:task_name`

### Integration
Jacazul is defined in:
- **Agent definition:** `/project/templates/agents/flow.agent.md` (now with Jacazul identity)
- **Custom instructions:** `/project/templates/context/copilot-instructions.md`

## Examples

### Starting a session
```
User: onboard
Jacazul: [shows full context, dashboard, waits for direction]
```

### Checking status mid-session
```
User: ponder
Jacazul: [refreshes dashboard]
```

### Viewing plans
```
User: planos
Jacazul: [lists all project plans with task counts]
```

### Focusing work
```
User: trabalhar em onboard
Jacazul: [filters tasks to onboard plan]
```

## Next Steps

- See `/agent` to discover other available agents
- Read `docs/taskwarrior-expert.md` for workflow details
- Check `docs/per-project-taskwarrior.md` for database architecture

---

**Jacazul:** 🐊 Jacaré Azul - Bridge between chaos and clarity, between overwhelm and flow.
