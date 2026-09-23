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

Inside `pprof`, five commands carry most of the work:

| Command | Answers |
| --- | --- |
| `top` | which functions hold the most self time |
| `top -cum` | which call paths hold the most total time |
| `list <regexp>` | which *lines* inside a function cost |
| `peek <regexp>` | who calls it and what it calls, one hop each way |
| `web` | the call graph, when the shape is the question |

`go tool pprof -http=:8080 cpu.out` serves the same data as a browsable UI
with a flame graph, which is the faster read on an unfamiliar call tree.

### Reading `top`

Every row carries two costs. **flat** is time spent in the function's own
code; **cum** adds everything it called. The gap between them is the
diagnosis:

| Shape | Meaning | Next move |
| --- | --- | --- |
| flat high, cum high | the function's own work is the cost | its algorithm or data structure |
| flat low, cum high | a coordinator whose callees cost | `peek` or `list` into the callees, or call them less often |

`top` without `-cum` is the usual first mistake: a function that calls the
expensive thing shows almost no self time, so the real path is invisible
until the cumulative view is read.

Runtime frames at the top of a CPU profile are symptoms, never targets. Each
one names a different cause, and `top -cum` finds the application frame that
triggers it:

| Hot frame | It means | Look at |
| --- | --- | --- |
| `runtime.mallocgc` | allocation rate, not computation | the `alloc_objects` heap view |
| `runtime.memmove` | large copies, usually a slice outgrowing its capacity | preallocation, buffer reuse — [data-structures](data-structures.md) |
| `runtime.scanobject` | the collector tracing a pointer-dense heap | values instead of pointers in hot slices and maps |

Optimizing `runtime.mallocgc` is not possible; allocating less in the
function above it is.

### Heap sample types

A heap profile has four sample types, and picking the wrong one answers a
different question:

| Sample | Question |
| --- | --- |
| `inuse_space` | what is retained right now — the leak view |
| `inuse_objects` | how many live objects — fragmentation and overhead |
| `alloc_space` | total bytes ever allocated — the churn view |
| `alloc_objects` | total allocations ever — what feeds the collector |

Select with `-sample_index`, for example
`go tool pprof -sample_index=alloc_objects mem.out`. The default is
`inuse_space`, which is why a churn problem hides in a first look.

The pair is what gets read, not either number alone. `alloc_objects` high
with `inuse_space` low is churn: cheap short-lived values, each one
harmless, together feeding the collector. `inuse_space` that keeps growing
is retention. A single snapshot cannot tell a leak from a large working
set; two can:

```bash
go tool pprof -base heap-before.out heap-after.out
```

With `-base`, every value is the delta, so what grew between the snapshots
is all that is left on screen. A running service can produce the delta
itself: `/debug/pprof/heap?seconds=60` returns the difference over the
window.

The usual retainers are an unbounded cache, a goroutine that never exits
and holds its references, and a map that once grew large: deleting entries
does not release the map's memory, even in the Swiss-table implementation.
Replacing the map with a fresh one does.

### Labels

A profile of a server blends every request type into one tree. Labels keep
them apart without a separate build:

```go
pprof.Do(ctx, pprof.Labels("endpoint", "/orders"), func(ctx context.Context) {
	handle(ctx)
})
```

Goroutines started inside `f` inherit the labels. Filter afterwards with
`-tagfocus=endpoint=/orders`, or break the tree down by label with
`-tagroot=endpoint`.

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

A hot mutex or block profile means the goroutines are waiting, not working:
narrow the critical section or split the lock before touching the code
inside it — see [concurrency](concurrency.md).

Goroutine counts that only climb are read from two profiles:

- `/debug/pprof/goroutine?debug=2` dumps every stack in the format of an
  unrecovered panic, with the creating call site. Hundreds of goroutines
  parked on the same line is the leak, located.
- `goroutineleak` runs a collection that proves which goroutines are
  blocked on a channel or `sync` primitive that nothing runnable can still
  reach. A goroutine blocked on network I/O is never a candidate, so an
  empty report is not proof of a clean program. It is listed by
  `go doc runtime/pprof.Profile` on Go 1.27; check that list before relying
  on it with an older toolchain.

Pick the profile from the symptom before capturing anything:

| Symptom | Profile |
| --- | --- |
| high CPU, one slow path | CPU |
| collector busy, allocation-heavy | heap, `alloc_objects` |
| memory climbing over hours | heap, `inuse_space` with `-base` |
| lock contention | mutex |
| goroutines stuck on channels or locks | block |
| goroutine count climbing | goroutine, then `goroutineleak` |
| OS thread count climbing | threadcreate — usually cgo or blocking syscalls |
| latency high, CPU low | none of these: a trace |

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
CPU profile. From a service, `/debug/pprof/trace?seconds=5` captures one.
Keep it to seconds: a trace records every state transition, so a busy
process produces a file that is slow to open and hard to navigate.

### Reading one

What a goroutine was doing instead of running is the whole answer:

| State | Means | Direction |
| --- | --- | --- |
| runnable, not running | ready, waiting for a `P` | CPU saturation, or a `GOMAXPROCS` that does not match the container quota — [runtime](runtime.md) |
| waiting | blocked on I/O, a channel, a lock, a timer | what it waits on; many on one object is a serialization point |
| mark assist | drafted to help the collector, in proportion to its allocation | allocation rate — the heap profile |
| syscall | pinned to an OS thread | blocking syscalls or cgo |

Idle processors while goroutines sit runnable is the scheduler's problem;
idle processors with nothing runnable is the program's. The goroutine
analysis page groups goroutines by where they start, with their running,
scheduling and blocked totals, which is the fastest way from "slow" to a
line of code.

The trace also converts to a pprof profile of where goroutines *waited*,
readable with every command above:

```bash
go tool trace -pprof=sched trace.out > sched.out   # also: net, sync, syscall
go tool pprof -top sched.out
```

`sched` is the time between becoming runnable and running; `net`, `sync`
and `syscall` are time blocked on each.

### Annotating

A trace of a server is every request interleaved. `runtime/trace`
annotations name the work and follow a context across goroutines. They are
cheap while nothing is recording, and `trace.IsEnabled` guards any message
that is expensive to build:

```go
ctx, task := trace.NewTask(ctx, "processOrder")
defer task.End()

trace.WithRegion(ctx, "charge", func() {
	charge(ctx, order)
})
trace.Log(ctx, "orderID", order.ID)
```

A task is one logical operation, a region is a phase inside it, and a log
is a point. Add them where a latency question is open, not on every
function — an annotation nobody filters by is noise in the viewer.

### Flight recorder

The problem with tracing a production latency spike is that by the time it
is noticed, it is too late to call `trace.Start`. `trace.FlightRecorder`
(Go 1.25+) keeps a moving window of recent trace data in memory, and
`WriteTo` snapshots it after the fact:

```go
fr := trace.NewFlightRecorder(trace.FlightRecorderConfig{
	MinAge:   10 * time.Second, // about twice the window being debugged
	MaxBytes: 8 << 20,          // wins over MinAge; a hint, not a guarantee
})
if err := fr.Start(); err != nil {
	return err
}
```

Snapshot on the trigger — a request over its budget, a failed health
check — and guard it so a burst of slow requests writes one file, not a
hundred: only one `WriteTo` may run at a time, and a concurrent call
returns an error. At most one flight recorder can be active in a process;
it can run alongside `trace.Start`. An endpoint that serves the snapshot
exposes the same material as `net/http/pprof` and gets the same admin-only
listener.

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
