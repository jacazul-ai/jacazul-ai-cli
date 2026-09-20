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

## Tuning the collector

Two knobs, and they answer different questions.

`GOGC` sets how much the heap may grow before the next cycle. The default of
100 means the collector runs when the live heap has doubled. Raising it
trades memory for fewer cycles; `GOGC=off` disables the collector entirely,
which is a benchmark or batch-job decision, not a service one.

`GOMEMLIMIT` (Go 1.19+) sets a soft ceiling on runtime-managed memory. As
the heap approaches it, the collector runs harder to stay under. It is the
right knob for a container with a memory limit, because `GOGC` alone knows
nothing about the cgroup and will happily grow into an OOM kill. It is soft:
the runtime will exceed it rather than deadlock, so it reduces the chance of
being killed without removing it.

The common production shape is `GOMEMLIMIT` at somewhat below the container
limit with `GOGC` left alone, or `GOGC=off` with `GOMEMLIMIT` as the only
pacing signal. Both are also settable at runtime through
`debug.SetGCPercent` and `debug.SetMemoryLimit`. The old ballast trick — a
large dummy allocation to fake a bigger heap — is obsolete; `GOMEMLIMIT`
replaced it.

Observe before turning either: `GODEBUG=gctrace=1` for per-cycle behavior,
and `runtime/metrics` in-process, which superseded `runtime.ReadMemStats`
and does not stop the world to answer.

## `GOMAXPROCS` in a container

A CPU quota is not a CPU count. Before Go 1.25 the runtime sized
`GOMAXPROCS` from the machine's visible cores and ignored the cgroup
bandwidth limit, so a pod limited to two cores on a 64-core node ran 64
schedulable threads: more context switching, more GC worker goroutines, and
latency that looks like contention because it is. Go 1.25 made the default
cgroup-aware.

On an older toolchain, set `GOMAXPROCS` explicitly from the quota rather
than leaving it to the runtime. Read the `go` directive before assuming
which behavior applies.

## Profile-guided optimization

PGO has been generally available since Go 1.21. Collect a CPU profile from
a representative workload, commit it as `default.pgo` beside the `main`
package, and `go build` uses it without a flag: the compiler inlines and
lays out code according to the paths the profile says are hot.

The gain is typically a few percent, which makes it a good deal for the cost
— no code changes — and a bad answer to a real bottleneck. A stale profile
optimizes for last quarter's traffic, so treat the file as something that
gets refreshed, not committed once.

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
