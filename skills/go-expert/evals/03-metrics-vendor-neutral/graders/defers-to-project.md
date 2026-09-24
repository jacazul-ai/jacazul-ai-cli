---
type: llm
---

- The answer does not choose a metrics vendor or library on the team's
  behalf. It either asks which instrumentation the project already uses,
  or shows a solution that plugs into whatever the project has, for
  example a small interface or a middleware with an injected recorder.
- Any code shown uses only the standard library plus that injected
  dependency.
- The timing uses `time.Since` or an equivalent monotonic measurement
  around the handler work.
