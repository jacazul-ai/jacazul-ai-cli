# Performance: Patterns After Measurement

Owner of: what to change once a bottleneck is proven. Proving it belongs to
[benchmarks](benchmarks.md) and [profiling](profiling.md); toolchain and
collector behavior belongs to [runtime](runtime.md).

Every pattern here is conditional. None of them is a default, and applying
one without a measurement in hand trades readable code for a number nobody
checked. If there is no profile, the correct optimization is the one
[`SKILL.md`](../SKILL.md#-philosophy-idiomatic-go-not-java) already
prescribes: simple, explicit, boring.

## Rule out the boring answer first

Most Go services are not CPU bound. Before optimizing a function, confirm
the time is in the process at all: a missing database index, a chatty
network call in a loop, a synchronous write, or an unpooled connection
dwarfs anything won by removing allocations. A CPU profile that looks flat
while the wall clock is long is the signature — read the trace.

## Allocation is the usual finding

Allocation feeds the collector, so allocations per operation is the number
that moves service latency most often.

- **Preallocate** when the size is known, and **reuse the buffer** across
  iterations with `s = s[:0]` instead of allocating a fresh slice. Capacity
  survives; length does not. The mechanics are in
  [data-structures](data-structures.md).
- **Watch interface boxing.** Passing a small value where `any` is expected
  allocates to put it on the heap. It is invisible in the source and obvious
  in an `alloc_objects` profile.
- **Prefer a sentinel error to a formatted one** on a path that fails often:
  `fmt.Errorf` allocates and formats every time, while a package-level
  `errors.New` value is created once — see [errors](errors.md) for when the
  sentinel is part of the contract rather than a micro-optimization.
- **Compile patterns once.** `regexp.MustCompile` at package level, not
  inside the handler. The same holds for templates and any other
  parse-then-use object.
- **Convert once.** Each `string`↔`[]byte` conversion copies, and shows up
  as `runtime.slicebytetostring` or `runtime.stringtoslicebyte` in an
  allocation profile. Keep the data in one form; the `bytes` package
  mirrors most of `strings` so the conversion is rarely needed.
- **Drop reflection from the hot path.** `reflect.DeepEqual` is a test
  helper; `slices.Equal`, `maps.Equal` and `bytes.Equal` are typed and
  cheap.
- **A small piece of a large string retains all of it**, the same as a
  subslice — see [data-structures](data-structures.md). `strings.Clone`
  (Go 1.18+) copies the piece out. Its own documentation warns that overuse
  costs memory, so it belongs where a profile shows the retention.

### Escape analysis tells you where it happens

```bash
go build -gcflags='-m' ./...
```

The compiler reports what moved to the heap; `-gcflags='-m -m'` adds the
chain of reasons, which is what to read when the answer is a surprise. A
value escapes when
the compiler cannot prove its lifetime ends with the function — returning a
pointer to a local, storing it in an interface, or capturing it in a closure
that outlives the call. Reading that output is faster than guessing, and it
is the only way to know whether a change actually kept the value on the
stack.

## `sync.Pool` for temporary objects, never for storage

A pool reduces allocation for objects with a short, bounded life that are
reconstructed on every use — a scratch buffer, an encoder. The collector may
drop any pooled item at any cycle, so anything that must still be there
later does not belong in a pool. Reset the object on `Get`, because a pool
returns whatever the last user left in it.

Pool pointers, not slices. `Put` takes an `any`, and a slice header is
three words, so `pool.Put(buf)` allocates to box it — the pool then costs
one allocation per use, which is what it was meant to remove. Store a
`*[]byte` and reslice through it:

```go
bp := bufPool.Get().(*[]byte)
buf := (*bp)[:0]
// ... fill buf ...
*bp = buf
bufPool.Put(bp)
```

Never return pooled memory to a caller: once it goes back into the pool,
the next `Get` hands the same bytes to someone else.

## Layout and the CPU

- **Field order changes struct size.** The compiler aligns fields and pads
  the gaps, so ordering from widest to narrowest can shrink a struct that is
  allocated millions of times. Verify with `unsafe.Sizeof`; the
  `fieldalignment` analyzer from `x/tools` finds candidates. Do not reorder
  fields for a struct that is not hot — it costs readability and the
  grouping that explained the type.
- **A zero-size field goes first, not last.** A trailing `struct{}` field
  gets padded so that its address cannot point past the end of the object:
  `struct{ v int64; f struct{} }` is 16 bytes, the same fields in the other
  order are 8.
- **Contiguous beats pointer-chasing.** A `[]T` walks memory in order; a
  `[]*T` follows a pointer per element and can miss cache on each one. This
  is a real effect at scale and noise below it. The same holds for a matrix
  built as `[][]T` with one allocation per row: one `make([]T, rows*cols)`
  sliced into rows keeps it contiguous, and a tree stored as a `[]Node`
  with integer children beats one of `*Node` for the same reason.
- **False sharing is contention without a lock.** Two counters written by
  different goroutines that sit on the same cache line make each core
  invalidate the other's copy, so adding goroutines makes the loop
  *slower*. That symptom, confirmed by a benchmark, is the only reason to
  pad — with `_ cpu.CacheLinePad` from `golang.org/x/sys/cpu` or a
  byte array sized to the line — because padding everything wastes the
  cache it was meant to protect.
- **Inlining removes call overhead** and enables further optimization.
  `-gcflags='-m'` reports what the compiler could and could not inline; it
  works to a cost budget, so a function grows out of eligibility silently.
  This is a reason to read the output, not a reason to write short functions
  — function scope is still contract, not size.

A loop with no function calls no longer starves the scheduler:
asynchronous preemption interrupts it with a signal, and
`GODEBUG=asyncpreemptoff=1` is what brings the old starvation back. Advice
to add a `//go:noinline` call as a "preemption point" predates that and
costs throughput for nothing.

## Work avoidance beats faster work

The largest wins are usually algorithmic, not idiomatic: a map lookup
replacing a linear scan, an early return before an expensive branch, a
result computed once instead of per iteration. A quadratic loop that got 20%
faster is still quadratic.

The inverse also holds and is worth stating, because it is where premature
optimization lands: for a handful of elements a linear scan over a slice
beats a map, which has to hash before it can look anything up.

## I/O boundaries

- **Connection reuse is configuration, not luck.** The default
  `http.Transport` keeps very few idle connections per host, so a client
  under load can open and close a connection per request while the profile
  shows nothing but TLS. Configure the transport, and reuse one client
  rather than constructing one per call.
- **Drain before closing.** A response body that is closed without being
  read to completion cannot return its connection to the pool:
  `io.Copy(io.Discard, resp.Body)` before `Close` — see
  [resources](resources.md).
- **Stream instead of buffering.** `io.ReadAll` on a large payload
  materializes the whole thing in memory; `json.Decoder` over the body, or
  `io.Copy` to the destination, holds a window instead.
- **Batch across a boundary.** One round trip carrying a hundred rows beats
  a hundred round trips, and the win is the latency, not the CPU.

## The gate

A change made here is finished when a `benchstat` comparison says it worked
— see [benchmarks.md](benchmarks.md). "It should be faster" is a
hypothesis. Without the second measurement, an optimization is just a
rewrite with worse readability.
