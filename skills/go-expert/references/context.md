# Context, Cancellation, and Deadlines

Owner of: context propagation, storage rules, timeouts, and cancellable
subprocesses. Goroutine ownership and primitive choice belong to
[concurrency](concurrency.md).

## Propagation

- `context.Context` should be the first parameter after the receiver; prefer
  passing it explicitly to each operation.
- Propagate cancellation, deadlines, and request-scoped credentials to every
  operation that needs them.

## Where a context comes from

`context.Background()` belongs at entry points: `main`, `init`, a test, the
top of a request. Creating one deeper in the chain silently detaches that
work from the caller's deadline and cancellation, so the request the client
abandoned keeps running against the database. That break is invisible in
review unless you look for the word itself.

`context.TODO()` is the marker for "a context belongs here and nobody has
wired it yet". It behaves identically to `Background`, and it differs in
what it tells the next reader: `Background` looks deliberate, `TODO` looks
unfinished, and one of those is true.

Never pass a nil `Context`. It compiles and panics on the first `Done()` or
`Value()`, far from the call that passed it.

## Storage

Do not store context in long-lived or reusable structs — it obscures lifetime,
prevents per-call cancellation and deadlines, and intermingles scopes.

Storing is acceptable only for operation-scoped structs tied to the context
lifetime, or for API compatibility retrofits such as `net/http.Request`. When
in doubt, pass it as an argument.

## Values carry metadata, not arguments

A value key must be an unexported named type, never a bare string. With a
string, two packages that both choose `"user"` overwrite each other and
neither can tell.

```go
type ctxKey struct{}

ctx = context.WithValue(ctx, ctxKey{}, requestID)
id, ok := ctx.Value(ctxKey{}).(string)
```

What travels this way is request-scoped metadata: a request ID, a trace
span, an authenticated identity. A function parameter does not belong here.
Moving an argument into the context removes it from the signature and from
the compiler's reach, and the failure arrives as a failed type assertion at
runtime.

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


## Work that must outlive the request

`context.WithoutCancel` (Go 1.21+) derives a context that keeps the values
but drops the cancellation. It is the honest way to start an audit write or
a cleanup that must finish after the handler returns — the alternative,
passing `context.Background()`, also drops every value the request carried.

Give that detached work its own timeout. Without cancellation it has no
deadline at all, which trades a cancelled write for one that never ends.

## Why it was cancelled

A cancelled context reports `context.Canceled` or
`context.DeadlineExceeded`, which says what happened and not why.
`context.Cause(ctx)` returns the reason when the context was created with
`WithCancelCause`, `WithDeadlineCause` or `WithTimeoutCause`, and falls back
to the generic error otherwise.

```go
ctx, cancel := context.WithCancelCause(parent)
cancel(fmt.Errorf("upstream returned 503"))

// ctx.Err()          -> context.Canceled
// context.Cause(ctx) -> upstream returned 503
```

Confirm the `go` directive supports these before using them — see
[runtime](runtime.md).
