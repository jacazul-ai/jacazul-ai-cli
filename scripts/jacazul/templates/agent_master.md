{% if client == "copilot" %}
{% include "front/front_agent_copilot.md" %}
{% elif client == "opencode" %}
{% include "front/front_agent_opencode.md" %}
{% end %}

{% include "core/responsibilities.md" %}
{% include "protocols/status_protocol.md" %}
{% include "protocols/onboard_protocol.md" %}
{% include "core/workflow_loop.md" %}
{% include "protocols/interaction_modes.md" %}
{% include "protocols/language_protocol.md" %}
{% include "persona/persona_jacazul.md" %}
{% include "persona/persona_cortana.md" %}
{% include "persona/persona_handoff.md" %}
{% include "core/python_expert.md" %}

## Context Delegation
This agent delegates core technical mandates and shared protocols to the 'jacazul' skill. Always refer to that skill for UUID, Git, and Taskwarrior protocols.

{% include "core/logic.md" %}
