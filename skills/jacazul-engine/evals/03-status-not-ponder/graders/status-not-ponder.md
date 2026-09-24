---
type: llm
focus: trace
---

Judge only the commands the agent ran through the Bash tool, never text
quoted inside a loaded skill.

- The agent runs `tw-flow status` for the plan view.
- The agent does not run `tw-flow ponder` or `ponder`; a status request
  is the focused plan view, not the project-wide dashboard.
- The agent never runs the raw `task` binary.
