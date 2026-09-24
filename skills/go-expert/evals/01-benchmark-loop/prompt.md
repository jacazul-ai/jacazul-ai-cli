---
max_turns: 12
timeout_seconds: 300
allowed_tools: [Skill, Read, Glob, Grep]
---

Our module declares `go 1.26` in go.mod. Write a Go benchmark for this
function, which lives in package codec:

```go
func Encode(p []byte) []byte
```

The input is a 4 KB payload built by a helper `makePayload()` that is slow
to run. Reply with the benchmark code and the exact command you would use
to compare it before and after a change.
