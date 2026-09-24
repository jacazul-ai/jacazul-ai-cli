---
max_turns: 12
timeout_seconds: 300
allowed_tools: [Skill, Read, Glob, Grep]
---

Here is an HTTP handler from our Go service. We want to know how many
requests it serves and how long they take. Show how to instrument it.

```go
func (s *Server) handleOrders(w http.ResponseWriter, r *http.Request) {
	orders, err := s.store.List(r.Context())
	if err != nil {
		http.Error(w, "internal error", http.StatusInternalServerError)
		return
	}
	json.NewEncoder(w).Encode(orders)
}
```
