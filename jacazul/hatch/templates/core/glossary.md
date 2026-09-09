# Jacazul Trigger Glossary

Operational language shortcuts that map to workflow actions. Some are Brazilian slang, some are project-specific shorthand, and some are conversational triggers that emerged from real usage. They are not rigid commands; they are how the user naturally asks the agent to shift mode or run a workflow.

## Onboard / Start the Corre

Phrases that mean "get going", "stop staring, do the thing", "we're on":

| Trigger | Origin | Vibe |
|---|---|---|
| `cuida` | Nordeste | "tá olhando pra minha cara por quê? Avia." |
| `rala` | Rio de Janeiro | "bora, se vira, corre" |
| `avia` | Nordeste | "acelera, não enrola" |
| `atividade` | General BR | "tô aqui, pode começar" |

**Action:** Run the explicit onboard flow only when the user clearly asks to start/orient the workflow.

---

## I&D / Introspection and Diagnosis

Phrases that mean "trace how we got here and diagnose why the current behavior happened":

| Trigger | Origin | Vibe |
|---|---|---|
| `i&d` | Jacazul shorthand | introspecção e diagnóstico |
| `I&D` | Jacazul shorthand | same trigger, loud casing |
| `ied` | phonetic shorthand | quick typed form of I&D |
| `i&d de task` | workflow shorthand | introspecção focada numa task/ini específica |
| `i&d dessa task` | conversational trigger | reconstruir o histórico e o estado da task atual |

**Action:** Run an introspection-and-diagnosis pass. Reconstruct the sequence of steps that led to the current behavior, then identify the likely cause.

**Default output shape:** conclusion → evidence → mechanism → impact → fix.

**Scope:** Inspect the relevant chain instead of guessing:
- scripts and CLI wrappers;
- runtime bootstraps;
- hatch templates and generated skill/agent artifacts;
- active skills and persona instructions;
- session handoff, task notes, and history when the issue depends on previous state;
- staged/unstaged repository state when behavior may come from an in-flight patch.

**Levels:**
- **I&D leve:** conclusion + short evidence trail.
- **I&D completo:** scripts, bootstraps, templates, skills, session/task context, and repo state as needed.
- **I&D forense:** compare harnesses, generated artifacts, sessions, or agents to explain divergence.

**Task-focused usage:** When the user asks for an "I&D de task", center the diagnosis on the current or specified task/plan: task notes, decisions, outcomes, related ticket links, staged diff, and the execution trail that led to the current state.

**Output:** Start with the conclusion, then show the evidence path: source → mechanism → impact → fix. Keep workflow dumps internal unless the user asks for raw/full context.

---

## Consensus Review / Review de Consenso

Phrases that mean "run a multi-persona convergent review — cross-check findings across personas before locking a decision":

| Trigger | Origin | Vibe |
|---|---|---|
| `consensus review` | EN shorthand | full phrase, formal |
| `review de consenso` | PT-BR shorthand | full phrase, formal |
| `manda um consensus` | conversational trigger | "roda a revisão cruzada agora" |
| `revc` | typed shorthand | quick-fire trigger |
| `crev` | typed shorthand | alt quick-fire trigger |

**Action:** Run the persona consensus review protocol: each relevant persona reviews with its own lens (e.g. Jacazul: workflow/policy, Codama: technical precision), findings are cross-checked, disagreements are resolved explicitly, and claims are verified against authoritative sources before closing. Present the result as a verdict table and record it as a signed `DECISION` note (`— <Persona(s)> (<Model>)`) on the active task.

**Current mechanism:** in-context persona handoff within the same conversation (single agent, shared context window), not a separate subagent spawn. Whether consensus reviews should move to isolated agents is still an open SPIKE (plan `multi-agent-loop`) — until that resolves, this trigger stays in-context only.

**Scope:** Use for design reviews, technical audits, or contested decisions where a single-persona pass risks blind spots — not for routine task execution.

---

> This glossary is a living document. Add new triggers as they emerge naturally in conversation.
