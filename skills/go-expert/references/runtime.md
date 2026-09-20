# Runtime, GC, and Version Awareness

Owner of: toolchain-dependent behavior, garbage collector changes, and
diagnosing a performance shift that is not application logic.

## Diagnose the runtime before blaming the code

Do not blame application logic for CPU or latency changes after a Go upgrade
without checking runtime changes first: compare Go version, `GOEXPERIMENT`,
architecture, allocation profile, runtime metrics, and `pprof` data.

Measure with representative benchmarks, runtime metrics, traces, and CPU/heap
profiles before changing architecture to explain a performance regression.

## Green Tea GC

Experimental in Go 1.25 (`GOEXPERIMENT=greenteagc`), default since Go 1.26.
The Go 1.26 notes announced that the build-time opt-out
`GOEXPERIMENT=nogreenteagc` was expected to go away in 1.27, but Go 1.27.0
still accepts it and its release notes do not mention it. Do not assume either
way: check `go doc internal/goexperiment` or the release notes of the
installed toolchain before relying on the opt-out.

Green Tea can reduce GC overhead for allocation-heavy, small-object workloads,
but some workloads may not benefit or may regress. If CPU rises after Go 1.26
or enabling Green Tea, compare with and without `GOEXPERIMENT=nogreenteagc`
while the installed toolchain accepts it, then validate with
`runtime/metrics`, `GODEBUG=gctrace=1`, and CPU/heap profiles before changing
application code.

## Version-sensitive behavior

Check release notes when behavior depends on the toolchain:

- Go 1.22 changed loop-variable semantics for modules using the newer language
  version — see [concurrency](concurrency.md) for the closure-capture
  consequence.
- Go 1.23 changed timer and ticker garbage-collection and channel behavior —
  see [context](context.md).
- Runtime, compiler, architecture, and experiment changes can alter CPU,
  allocation, and latency profiles.

Always read the `go` directive in `go.mod` before judging version-sensitive
behavior.

**Sources:**

- https://go.dev/blog/greenteagc
- https://go.dev/doc/go1.26#runtime
