---
type: llm
focus: trace
---

Judge only the commands the agent ran through the Bash tool, never text
quoted inside a loaded skill.

- The agent runs `tw-flow focus` and `tw-flow session resume` before it
  proposes or starts any concrete work.
- The agent never runs the raw `task` binary.
- The agent does not reconstruct the previous session from memory or from
  guesses about the repository; missing workflow output is reported as a
  blocker.
