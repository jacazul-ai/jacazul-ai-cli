# Go Engineering Playbook

Implementation guidance for writing clear, idiomatic, safe, and maintainable
Go. This file answers **how to build the change**. Scenario-based review
directives live separately in [`CODE-REVIEW.md`](CODE-REVIEW.md).

These are defaults, not automatic repository policy. Read the repository's
`go.mod`, CI, Makefile, scripts, and package conventions before adopting an
optional gate or changing an established contract.

## Before writing code

1. Read the module's `go` directive and identify the supported toolchain.
2. Read the target package and its tests before introducing an abstraction.
3. Define the API contract: valid input, absence, errors, timeouts, retries,
   partial success, ownership, and shutdown behavior.
4. Identify trust boundaries: users, network payloads, files, subprocesses,
   databases, dependencies, generated data, and logs.
5. Decide who owns every mutable value, resource, goroutine, channel, lock,
   transaction, and cancellation signal.

## Package and API design

- Prefer short, lowercase package names that describe behavior or a domain.
- Prefer concrete types and package functions until a real consumer needs an
  interface or a test seam.
- Define small interfaces near the consumer; name them by behavior (`Reader`,
  `Writer`, `Handler`) rather than implementation (`Manager`, `Service`).
- Keep the public API small and keep implementation details unexported.
- Use explicit types for units, identifiers, states, and values whose invalid
  combinations would otherwise be easy to construct.
- Preserve compatibility deliberately: exported types, errors, wire formats,
  and serialization details are contracts once consumers depend on them.

## Values and ownership

- Remember that assignments copy values, while slices, maps, pointers,
  interfaces, channels, and function values can still refer to shared state.
- Document whether a function borrows, consumes, mutates, or returns ownership
  of a slice, buffer, map, or pointer.
- Clone data at an ownership boundary when later mutation or retention would be
  surprising. Avoid copying synchronization values after first use.
- Decide whether nil and empty mean the same thing. Make the distinction
  explicit when it reaches JSON, storage, or another wire boundary.
- Do not retain a large backing allocation merely to return a small subset;
  measure and copy when the lifetime justifies it.

## Errors and failure contracts

- Return errors for ordinary operational failures; reserve panic for broken
  invariants or unrecoverable initialization.
- Add context at the layer that can explain or act on the failure.
- Wrap with `%w` only when callers should be able to inspect the cause.
- Use `errors.Is` for sentinel values and `errors.As` for error types. Never
  make callers parse error strings as a protocol.
- Decide whether an error is retryable, terminal, transient, or safe to expose.
- Handle errors from `Close`, `Flush`, `Commit`, `Sync`, and `Rollback` when
  they can change the durability or transaction contract.
- Log an error once at the boundary that owns the decision; avoid logging and
  returning the same event at every layer.

## Control flow and readability

- Keep the happy path visible and left-aligned.
- Handle invalid input and failures with early returns; avoid unnecessary
  `else` blocks and deep nesting.
- Make loop bounds, mutation, ownership, and ordering explicit.
- Do not depend on map iteration order. Sort keys when order is part of output
  or behavior.
- Remember that a `range` value is a copy when mutating slice, array, or map
  elements; use an index or deliberate pointer ownership when needed.
- Treat numeric conversions as validation boundaries: check range, sign, unit,
  and precision before converting external or calculated values.

## Context, concurrency, and lifecycle

- Pass `context.Context` explicitly as the first parameter after a receiver.
- Propagate cancellation, deadlines, and request-scoped credentials to every
  operation that needs them. Do not store a reusable request context in a
  long-lived struct.
- Every goroutine needs an owner, a completion or cancellation path, and an
  observable error path. A `go` statement schedules work; it does not wait.
- Keep resource cleanup inside the lifetime of the owner. A parent that returns
  before child goroutines finish cannot safely clean up resources those
  children still borrow unless it first waits or transfers ownership.
- Close channels only from the component that owns the sending side and knows
  no more values will arrive. Use context cancellation when channel-close
  ownership is not clear.
- Call `WaitGroup.Add` before starting work and pair it with `defer Done()` in
  the goroutine. Bound queues and define backpressure instead of adding
  unbounded goroutines or buffers.
- Prefer a mutex for a clear shared-state invariant. Use atomics only when the
  state transition and publication protocol are explicit.
- Use `exec.CommandContext` for cancellable subprocesses and call
  `cancel()` after `context.WithTimeout`/`WithCancel` when the scope ends.

## Resource and standard-library boundaries

- Close HTTP response bodies, database rows, statements, files, and other
  owned resources at the narrowest reliable lifetime boundary.
- Check HTTP errors before dereferencing the response, validate status codes,
  and configure operation-appropriate timeouts.
- Parameterize SQL values. Never build SQL by concatenating external input.
- Make JSON presence semantics explicit: `omitempty`, nil pointers, nil slices,
  zero values, and false booleans can change the wire contract.
- Use `crypto/rand` for secrets, tokens, nonces, and security decisions;
  `math/rand` is not a cryptographic source.
- Avoid finalizers as deterministic cleanup. Make `Close`, cancellation, and
  shutdown explicit.

## Security boundary

Treat external input as hostile by default:

- validate size, shape, encoding, and allowed values before expensive work;
- pass subprocess arguments directly instead of constructing shell syntax;
- constrain paths, URLs, regular expressions, decompression, and allocations;
- redact credentials and personal data from logs, errors, tests, and traces;
- use least-privilege credentials and reviewed dependencies;
- run vulnerability analysis when dependency or release risk is in scope.

Do not introduce `unsafe`, reflection, or cgo to bypass a design problem. If
one is required, isolate it behind a small boundary and document lifetime,
alignment, aliasing, layout, and foreign-memory ownership invariants.

## Tests and validation

Write tests around the contract, not only the happy path:

- invalid input and returned errors;
- cancellation, timeout, retry, and shutdown;
- ownership, aliasing, nil/empty, and serialization behavior;
- concurrent completion, failure propagation, and bounded resources;
- security boundaries and resource cleanup.

Run repository-configured checks first. If no stronger gate exists, use this
conventional baseline and label it as such:

```bash
gofmt -d path/to/touched.go
goimports -d path/to/touched.go
go test ./...
go vet ./...
```

For concurrent changes, add `go test -race ./...` when the module supports it.
Use `staticcheck ./...` and `govulncheck ./...` when available and relevant;
they complement tests and review rather than proving correctness alone.

## Version and runtime awareness

Check release notes when behavior depends on the toolchain:

- Go 1.22 changed loop-variable semantics for modules using the newer language
  version.
- Go 1.23 changed timer and ticker garbage-collection and channel behavior.
- Runtime, compiler, architecture, and experiment changes can alter CPU,
  allocation, and latency profiles.

Measure with representative benchmarks, runtime metrics, traces, and CPU/heap
profiles before changing architecture to explain a performance regression.

## References

- [Effective Go](https://go.dev/doc/effective_go)
- [Go specification](https://go.dev/ref/spec)
- [Go memory model](https://go.dev/ref/mem)
- [Go security](https://go.dev/security/)
- [Go release history](https://go.dev/doc/devel/release)
- [Go Code Review Directives](CODE-REVIEW.md)
