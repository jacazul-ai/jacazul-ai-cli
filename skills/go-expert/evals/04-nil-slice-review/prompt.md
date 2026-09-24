---
max_turns: 12
timeout_seconds: 300
allowed_tools: [Skill, Read, Glob, Grep]
---

Code review dispute in our Go project. The author wrote:

```go
func activeNames(users []User) []string {
	var out []string
	for _, u := range users {
		if u.Active {
			out = append(out, u.Name)
		}
	}
	return out
}
```

The reviewer insists that slices must always be initialized, and asks for
`out := []string{}` instead. Who is right, and is there any case where the
reviewer's version matters?
