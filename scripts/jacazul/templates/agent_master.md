{% if client == "copilot" %}
{% include "front_agent_copilot.md" %}
{% elif client == "opencode" %}
{% include "front_agent_opencode.md" %}
{% end %}

{% include "responsibilities.md" %}
{% include "status_protocol.md" %}
{% include "onboard_protocol.md" %}
{% include "workflow_loop.md" %}
{% include "interaction_modes.md" %}
{% include "language_protocol.md" %}
{% include "persona_jacazul.md" %}
{% include "persona_cortana.md" %}
{% include "persona_handoff.md" %}
{% include "python_expert.md" %}

## Context Delegation
This agent delegates core technical mandates and shared protocols to the 'jacazul' skill. Always refer to that skill for UUID, Git, and Taskwarrior protocols.

{% include "logic.md" %}
