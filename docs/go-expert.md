# Go Expert Skill

Guide for the go-expert skill: idiomatic Go, explicit quality-gate boundaries,
`gofmt` then `goimports` formatting, and Line of Sight readability.

## Trigger → Action

### When the user asks for Go formatting

Run `gofmt` first, then run `goimports` if available. This is the preferred
operational sequence even though `goimports` is `gofmt`-compatible: normalize
formatting first, then organize imports.

If `goimports` is unavailable, use `gofmt` alone and say that the import
organization pass was skipped. In COUNSELOR mode, ask for authorization before
installing missing tools. When authorized, install with:

```bash
go install golang.org/x/tools/cmd/goimports@latest
```

Use write-mode commands for correction: `gofmt -w` and `goimports -w`.
Use `goimports -l` only to list files whose formatting/imports differ, and
`goimports -d` only to inspect the diff. These check modes do not replace the
correction baseline.

### When the user asks whether a Go check is mandatory

Separate repository policy from convention:

- Repository mandates come from CI, Makefiles, scripts, docs, task context, or
  the skill itself.
- Go conventions are expert guidance, not proof that the repository enforces a
  gate.
- Optional gates such as `golangci-lint`, race checks, coverage thresholds, or
  fuzzing are mandatory only when configured, requested, or documented.

### When Go code changes and no stronger gate exists

Use the conventional baseline:

1. Run `gofmt` on touched Go files, then `goimports` if available.
2. Run `go test ./...`.
3. Run `go vet ./...` when the module layout supports it.

## Package design

Go is package-first. Keep package names short, lowercase, and meaningful. Name
packages by the behavior or domain they provide, not by artificial layers.

Avoid grab-bag packages such as `util`, `common`, or `helpers` unless the
repository already uses that convention and the package has a clear boundary.
Do not split code into Java-style layers just to look architectural. Prefer a
small public API and keep unexported details inside the package that owns them.

## Error handling

Errors are part of the API contract. Return errors with enough context for the
caller to act, but do not spam redundant context at every layer.

- Wrap underlying errors with `%w` when callers may need `errors.Is` or
  `errors.As`.
- Use `errors.Is` and `errors.As` for error matching and extraction.
- Do not compare error strings.
- Use sentinel errors only when they are a deliberate part of the package
  contract.
- Prefer direct `if err != nil { return ... }` handling that preserves Line of
  Sight.

## Line of Sight

The skill uses Mat Ryer's **Line of Sight** readability principle.

Definition: "a straight line along which an observer has unobstructed vision."

In Go, this means:

- Keep the happy path aligned to the left.
- Make a function easy to scan for expected flow.
- Handle errors and edge cases early with guard clauses or early returns.
- Keep error handlers and edge cases indented.
- Avoid deep nesting and unnecessary `else` blocks.
- Prefer the happy successful return as the last statement when possible.
- Flip conditionals to handle failure first.

Reference: Mat Ryer talk, https://www.youtube.com/watch?v=yeetIgNeIkc

- `04:18-06:02`: introduces Line of Sight and keeping the main flow visible.
- `06:05`: prefer the happy return as the final statement when possible.
- `06:20`: flip logic to handle failures first and avoid unnecessary `else`.

## Idiomatic Go, not Java

The skill should challenge Java-style ceremony in Go code:

- Avoid class terminology; Go has types, structs, and interfaces.
- Prefer concrete types and package-level functions when they are enough.
- Keep interfaces small and behavior-based.
- Define interfaces near consumers unless the repository has a clear boundary.
- Avoid `IThing`, `ThingInterface`, `AbstractThing`, and `BaseThing`.
- Treat generic `Manager` or `Service` suffixes as suspect unless they express
  real domain behavior.

## Standard library as design compass

When unsure, prefer standard-library patterns:

- `io` for small behavior interfaces.
- `net/http` for handler and middleware shape.
- `context` for cancellation and deadlines.
- `errors` for wrapping and matching.
- `testing` for table tests, benchmarks, and fuzzing conventions.
- `database/sql` for explicit boundaries and error handling.

## Concurrency and lifecycle

Concurrency must justify its complexity. Sequential code is the default; use
goroutines, channels, and synchronization only when the behavior needs parallel
I/O, cancellation, timeouts, fan-out, or explicit coordination.

Every goroutine needs an owner and an exit path. The code that starts it should
make clear how it finishes, how errors are observed, and how cancellation is
propagated.

Use the simplest primitive that matches the behavior:

- Channels transfer values, ownership, or completion signals.
- `sync.Mutex` protects small shared state when clearer than a channel.
- `sync.WaitGroup` waits for fan-out work.
- `sync.Once` handles one-time initialization.

Use `context.Context` for cancellation, deadlines, and request-scoped values.
For functions that accept context, it should be the first parameter after the
receiver. Prefer passing context explicitly to each operation that needs it. Do
not store `context.Context` in long-lived or reusable structs because it obscures
lifetime, prevents per-call cancellation/deadlines, and intermingles scopes.

Storing context is acceptable only when the struct is operation-scoped, not
reused, and its lifetime is clearly tied to the context lifetime, or when
preserving API compatibility requires it. Rare compatibility retrofits include
cases such as `net/http.Request`; prefer Context-suffixed methods when
practical. When in doubt, pass context as an argument.

For external commands, prefer `exec.CommandContext(ctx, ...)` when the command
must respect cancellation or timeout. When creating a timeout with
`context.WithTimeout`, call the returned cancel function, usually with
`defer cancel()`.

For Go versions before 1.23, unreferenced timers created by `time.After` were
not garbage collected until they fired. In modern Go, prefer lifecycle clarity:
use `context.WithTimeout` for cancellation/deadlines, and use `time.NewTimer`
or `time.Ticker` with explicit `Stop()` when timer control matters.

Use a buffered channel as a simple semaphore when limiting concurrency is enough:

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

For Go versions before 1.22, shadow the loop variable inside the loop
(`job := job`) before starting the goroutine to avoid closure-capture bugs.

When concurrent code changes, `go test -race ./...` is a conventional baseline
check if the module supports it. Treat it as a project mandate only when the
repository configures or documents it.

## Runtime and GC diagnostics

Do not blame application logic for CPU or latency changes after a Go upgrade
without checking runtime changes first. Compare Go version, `GOEXPERIMENT`,
architecture, allocation profile, runtime metrics, and `pprof` data.

Green Tea GC was introduced as an experiment in Go 1.25 with
`GOEXPERIMENT=greenteagc` and became the default garbage collector in Go 1.26.
Go 1.26 still allows opting out at build time with
`GOEXPERIMENT=nogreenteagc`, but the Go 1.26 release notes state this opt-out is
expected to be removed in Go 1.27.

Green Tea can reduce GC overhead for allocation-heavy workloads, especially
small-object workloads, but some workloads may not benefit or may regress. If a
CPU increase appears after moving to Go 1.26 or enabling Green Tea, compare with
and without `GOEXPERIMENT=nogreenteagc` while that opt-out exists, then validate
with `runtime/metrics`, `GODEBUG=gctrace=1`, and CPU/heap profiles before
changing application code.

References:
- https://go.dev/blog/greenteagc
- https://go.dev/doc/go1.26#runtime

## Logging and output

Follow the repository-local output and logging convention. Do not introduce
`log`, `slog`, `fmt`, or a new logger abstraction as a cosmetic preference.

If the project defines a logging interface or output contract, program against
that contract and keep concrete logger implementations swappable.

For simple CLI output, stdout/stderr writes may be enough. For services or
observability-heavy code, structured logging may be required by the repository.
Read the local pattern first.

## Testing and mocks

Prefer designing testable code over adding mocks. Use small interfaces, explicit
dependencies, and simple seams so behavior can be tested without a mocking
framework whenever possible.

Do not force an interface solely because code shells out to an external process.
Direct shell-out can be tested through controlled external-process resources:
temporary filesystem fixtures, environment variables, PATH shims or fake
executables, local URLs or `httptest.Server`, captured stdout/stderr, and
controlled exit codes.

Choose the least artificial reliable boundary for the behavior under test.
Extract a seam or interface when shell-out logic becomes complex, expensive,
unsafe, hard to reproduce, or has multiple real consumers; do not extract one
for architectural purity alone.

When a mock is necessary, prefer a function-field mock struct pattern:

- Define a struct with function fields matching the interface methods.
- Implement each method by calling the corresponding function field.
- Customize return values, errors, and argument capture per test.
- Do not implement behavior the test does not care about.
- Treat a nil panic from an unexpected method call as useful signal that the
  code did something the test did not anticipate.

## Generated code

Do not edit generated Go files manually when they contain a marker such as
`// Code generated ... DO NOT EDIT.` Change the generator, template, schema, or
source input instead, then regenerate. If a generated file lacks a standard
marker, inspect repository conventions before editing.

---

**Version:** 0.1.0
**Last Updated:** 2026-07-07
