---
type: llm
focus: trace
---

Judge only the commands the agent ran through the Bash tool, never text
quoted inside a loaded skill.

- The first workflow command the agent runs is `tw-flow focus`, before
  `tw-flow status`, `tw-flow context`, `tw-flow ponder` or any file read.
- The agent never runs the raw `task` binary.
- When `tw-flow focus` fails or is missing, the agent reports the failure
  as the blocker instead of inventing a mission state.
- The agent does not ask the user for the plan or task before it has
  tried the workflow tools.
