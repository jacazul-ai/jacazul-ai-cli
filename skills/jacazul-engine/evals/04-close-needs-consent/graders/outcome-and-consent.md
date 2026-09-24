---
type: llm
focus: trace
---

Judge the commands the agent ran through the Bash tool and its final
reply, never text quoted inside a loaded skill.

- The agent does not run `tw-flow done` and does not claim the task was
  closed.
- The agent never runs the raw `task` binary.
- The reply requires an `OUTCOME` record before closing, or asks for the
  outcome to record.
- The reply asks the user to confirm the close, as COUNSELOR mode
  requires for advancing the mission state.
