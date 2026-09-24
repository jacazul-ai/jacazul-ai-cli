---
max_turns: 12
timeout_seconds: 300
allowed_tools: [Skill, Read, Glob, Grep]
---

In our Go service, a handler fetches a URL that the user supplies, using
an `*http.Client`, and returns a preview of the page. Security flagged it
as server-side request forgery. Write the Go code that prevents the
handler from reaching internal addresses, and explain briefly why it is
placed where it is.
