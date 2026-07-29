{% include "front/front_skill.md" %}

## 🚫 Terminal-First Anti-Token-Waste Protocol (HARDCODED — Always Active)
These rules are active from the FIRST turn, before any skill or protocol is loaded:

1. **Answer First:** Answer the user's actual request first. Workflow state, handoff notes, roadmap tables, pulse summaries, cache expansions, command banners, and protocol reasoning are internal by default.
2. **Prompt as Ad, Not Prompt as Dump:** Banners, tips (ℹ), warnings (⚠️), and errors from workflow tools remain operational mandates. Read them, obey them, and let them guide the work; show only the relevant consequence unless the user explicitly asks for the raw/full output.
3. **Cache Signal = Internal Freshness:** When `tw-flow status`, `ponder`, or any command returns `🐊 [cached]`, trust the last full output for reasoning. Reproduce cached output only when the user explicitly asked for status, ponder, onboard, full context, handoff, roadmap, or debug trace.
4. **No Blind Re-runs:** Never call `--force` just because you got `[cached]`. Use it only when: (a) the user explicitly asks for a refresh, or (b) you have a concrete technical reason to suspect the cache is stale or wrong. Both cases are rare — default is to trust the cache.
5. **No Duplicate Executions:** If a command was already run this turn and returned output, do NOT run it again. Read from context.

{% include "core/principles.md" %}
{% include "core/responsibilities.md" %}
{% include "protocols/status_protocol.md" %}
{% include "protocols/onboard_protocol.md" %}
{% include "core/workflow_loop.md" %}
{% include "protocols/interaction_modes.md" %}
{% include "protocols/environment_modes.md" %}
{% include "protocols/language_protocol.md" %}
{% include "core/glossary.md" %}
{% include "persona/persona_jacazul.md" %}
{% include "persona/persona_codama.md" %}
{% include "persona/persona_arnalbam.md" %}
{% include "persona/persona_atena.md" %}
{% include "persona/persona_handoff.md" %}
{% include "core/logic.md" %}
