# Profiling and Diagnosis

Owner of: finding out where time, memory, and blocking actually go, and the
runtime switches that make a program explain itself. Producing the numbers
to compare belongs to [benchmarks](benchmarks.md); acting on the finding
belongs to [performance](performance.md).

The order matters and it is not negotiable: reproduce, measure, form one
hypothesis, then change one thing. A fix applied before the measurement is
a guess that happens to compile.

## pprof

Capture from a benchmark, which gives a profile of a known workload:

```bash
go test -run '^$' -bench BenchmarkEncode -cpuprofile cpu.out -memprofile mem.out
go tool pprof cpu.out
```

Inside `pprof`, four commands carry most of the work:

| Command | Answers |
| --- | --- |
| `top` | which functions hold the most self time |
| `top -cum` | which call paths hold the most total time |
| `list <regexp>` | which *lines* inside a function cost |
| `web` | the call graph, when the shape is the question |

`top` without `-cum` is the usual first mistake: a function that calls the
expensive thing shows almost no self time, so the real path is invisible
until the cumulative view is read.

A heap profile has four sample types, and picking the wrong one answers a
different question:

| Sample | Question |
| --- | --- |
| `inuse_space` | what is retained right now — the leak view |
| `inuse_objects` | how many live objects — fragmentation and overhead |
| `alloc_space` | total bytes ever allocated — the churn view |
| `alloc_objects` | total allocations ever — what feeds the collector |

Select with `-sample_index`, for example
`go tool pprof -sample_index=alloc_objects mem.out`.

## Profiling a running service

`net/http/pprof` registers its handlers on `http.DefaultServeMux` through a
blank import:

```go
import _ "net/http/pprof"
```

That endpoint exposes goroutine stacks, heap contents, and command-line
arguments, and it can be made to consume CPU on demand. Bind it to a
loopback or admin listener, never to the public mux — the reasoning is in
[security](security.md), and a blank import with a side effect this large is
exactly the case [packages](packages.md) says to keep at the root.

Block and mutex profiles are off by default because they cost something.
Turn them on deliberately, with a sampling rate rather than a full capture:

```go
runtime.SetBlockProfileRate(1_000_000)  // sample blocking events, in ns
runtime.SetMutexProfileFraction(100)    // sample 1 of every 100 contentions
```

## Execution traces

A profile says where the time went; a trace says *why it was not spent*.
Scheduler latency, GC pauses, goroutines blocked on a channel, and a
`GOMAXPROCS` that never fills are trace questions, not pprof questions.

```bash
go test -run '^$' -bench . -trace trace.out
go tool trace trace.out
```

Reach for a trace when the CPU profile looks flat but the wall clock does
not — that gap is almost always waiting, and waiting does not appear in a
CPU profile.

## The race detector

```bash
go test -race ./...
```

It reports only races that actually execute during the run, so a green race
run is evidence about the paths the tests covered and nothing more. The
instrumentation raises memory and execution cost substantially, which is
why it belongs in tests and CI rather than in a benchmark or a production
build.

A data race is not a flaky test to be retried. It is undefined behavior that
happens to have produced the right answer so far — see
[concurrency](concurrency.md) for the ownership question underneath it.

## GODEBUG

The runtime answers questions when asked, without a rebuild:

| Setting | Shows |
| --- | --- |
| `GODEBUG=gctrace=1` | every GC cycle: heap size, pause, CPU share |
| `GODEBUG=inittrace=1` | time and allocations of each package `init` |
| `GODEBUG=schedtrace=1000` | scheduler state every second |

`inittrace` is the fastest way to explain slow startup, and it regularly
finds a dependency doing real work at import time — the cost of the `init`
that [packages](packages.md) says to avoid.

Settings vary across releases: confirm against the installed toolchain's
documentation rather than assuming, the same rule as
[runtime](runtime.md).

## Delve

`dlv test ./pkg`, `dlv debug ./cmd/app`, and `dlv attach <pid>` cover the
cases where reading is not enough. Prefer a failing test that reproduces the
state over a breakpoint on a hunch: the test survives the session, and the
breakpoint does not.
