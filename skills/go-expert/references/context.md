# Context, Cancellation, and Deadlines

Owner of: context propagation, storage rules, timeouts, and cancellable
subprocesses. Goroutine ownership and primitive choice belong to
[concurrency](concurrency.md).

## Propagation

- `context.Context` should be the first parameter after the receiver; prefer
  passing it explicitly to each operation.
- Propagate cancellation, deadlines, and request-scoped credentials to every
  operation that needs them.

## Storage

Do not store context in long-lived or reusable structs — it obscures lifetime,
prevents per-call cancellation and deadlines, and intermingles scopes.

Storing is acceptable only for operation-scoped structs tied to the context
lifetime, or for API compatibility retrofits such as `net/http.Request`. When
in doubt, pass it as an argument.

## Timeouts and cancellation

- After `context.WithTimeout` or `context.WithCancel`, call the cancel
  function when the scope ends, usually with `defer cancel()`.
- For external commands, prefer `exec.CommandContext(ctx, ...)` when the
  command must respect cancellation or timeout. Pass subprocess arguments
  directly — see [security](security.md).
- Before Go 1.23, unreferenced `time.After` timers were not collected until
  they fired. In modern Go, prefer lifecycle clarity: `context.WithTimeout`
  for cancellation and deadlines, and `time.NewTimer` / `time.Ticker` with
  explicit `Stop()` when timer control matters.
