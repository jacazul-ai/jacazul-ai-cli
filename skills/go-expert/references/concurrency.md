# Concurrency and Lifecycle

Owner of: goroutine ownership, synchronization primitive choice, channel
ownership, and bounded parallelism. Cancellation and deadlines belong to
[context](context.md); read both when cancelling a goroutine through a
context.

## When concurrency is justified

Concurrency must justify its complexity. Sequential code is the default; use
goroutines, channels, and synchronization only when the behavior needs
parallel I/O, cancellation, timeouts, fan-out, or explicit coordination.

## Ownership

- Every goroutine needs an owner, a completion or cancellation path, and an
  observable error path. A `go` statement schedules work; it does not wait.
- Leaks come from sends or receives on channels with no remaining counterpart.
- Keep resource cleanup inside the lifetime of the owner. A parent that
  returns before child goroutines finish cannot safely clean up resources
  those children still borrow unless it first waits or transfers ownership.
- Close channels only from the component that owns the sending side and knows
  no more values will arrive. Use context cancellation when channel-close
  ownership is not clear.

## Choosing the primitive

Use the simplest primitive that matches the behavior:

- channels transfer values, ownership, or completion signals;
- `sync.Mutex` protects small shared state when clearer than a channel;
- `sync.WaitGroup` waits for fan-out;
- `sync.Once` handles one-time initialization.

Call `WaitGroup.Add` before starting work and pair it with `defer Done()` in
the goroutine. Bound queues and define backpressure instead of adding
unbounded goroutines or buffers.

Prefer a mutex for a clear shared-state invariant. Use atomics only when the
state transition and publication protocol are explicit.

## Closed channels

Closing is a broadcast, not a cleanup, and the asymmetry is where the
panics come from.

| Operation on a closed channel | Result |
| --- | --- |
| Receive | the zero value, immediately, forever |
| Send | panic: send on closed channel |
| Close again | panic: close of closed channel |

A receive that returns immediately is what turns a `select` in a `for` into
a busy loop burning a core: the closed case is always ready. Set the
channel variable to `nil` once drained — a nil channel blocks forever, which
removes that case from the `select`.

The same shape appears with `default`: a `select` with a `default` branch
inside a tight loop never blocks, so it spins. `default` means "do not
wait", and something in the loop has to.

## `recover` only covers its own goroutine

A deferred `recover` catches a panic in the goroutine that deferred it.
A panic in a goroutine started by that function crashes the whole process,
and no amount of recovering in the parent changes it. Whatever spawns a
goroutine owns recovering inside it — which is the ownership rule above,
arriving as a crash instead of a leak.

## The primitives, and what bites with each

| Primitive | Use for | What to watch |
| --- | --- | --- |
| `sync.Mutex` | A clear shared-state invariant | Keep the critical section short; never hold it across I/O |
| `sync.RWMutex` | Many readers, rare writers | An `RLock` cannot be upgraded to a `Lock`; attempting it deadlocks |
| `sync/atomic` | Counters and flags | Prefer the typed forms (`atomic.Int64`, `atomic.Bool`, `atomic.Pointer[T]`) over the loose functions |
| `sync.Map` | Concurrent map, read-heavy | A plain map behind an `RWMutex` wins when writes are frequent |
| `sync.Once` | One-time initialization | `OnceFunc`, `OnceValue` and `OnceValues` (Go 1.21+) remove the surrounding boilerplate |
| `sync.WaitGroup` | Waiting for fan-out | `wg.Go(func(){...})` (Go 1.25+) pairs `Add` and `Done` so neither can be forgotten |

Holding a lock across I/O is the one worth repeating. A mutex held while a
request is in flight turns a slow dependency into a queue on your own
process, and it does not look like a concurrency bug in a profile — it
looks like the dependency being slow.

## Waiting for work that can fail

`sync.WaitGroup` waits; it does not carry errors, so the first failure
either gets dropped or needs a channel bolted on beside it.

The standard library has no group-with-errors primitive.
`golang.org/x/sync/errgroup`, a Go team subrepository, is the usual
answer: `errgroup.WithContext` cancels the siblings on the first failure,
and `SetLimit(n)` replaces a hand-rolled worker pool. It is still a
dependency, so adopting it is a project decision — but hand-rolling
first-error-plus-cancel correctly is harder than it looks, which is why
that decision usually goes the same way.

## Bounding parallelism

Use a buffered channel as a simple semaphore when limiting concurrency is
enough:

```go
sem := make(chan struct{}, 4)

var wg sync.WaitGroup
for _, job := range jobs {
	sem <- struct{}{}
	wg.Add(1)

	go func() {
		defer wg.Done()
		defer func() { <-sem }()

		run(ctx, job)
	}()
}

wg.Wait()
```

Before Go 1.22, shadow the loop variable (`job := job`) before starting the
goroutine to avoid closure-capture bugs.

## Validation

When concurrent code changes, `go test -race ./...` is a conventional baseline
check if the module supports it — a project mandate only when the repository
configures or documents it.
