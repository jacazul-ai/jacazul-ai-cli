# Benchmarks: Measuring Before Deciding

Owner of: writing, running, and comparing benchmarks. Reading a profile
belongs to [profiling](profiling.md); what to do with the finding belongs to
[performance](performance.md). Correctness tests belong to
[testing](testing.md) — a benchmark is not a test and proves nothing about
behavior.

A benchmark exists to answer a question that was asked first. Writing one
before there is a number to compare it against produces a ritual, not
evidence.

## Shape

A benchmark lives beside the code in `_test.go` and takes `*testing.B`.

```go
func BenchmarkEncode(b *testing.B) {
	payload := makePayload()   // setup: outside the measured loop
	b.ReportAllocs()

	for b.Loop() {
		Encode(payload)
	}
}
```

`b.Loop()` (Go 1.24+) is the current form and replaces
`for i := 0; i < b.N; i++`. It is worth the migration for two reasons that
have nothing to do with style:

- the compiler keeps the loop body's call arguments and results alive, so a
  pure function whose result is discarded is no longer optimized away into a
  benchmark that measures nothing;
- the body outside the loop runs once per `-count` rather than once per
  `b.N` retry, so expensive setup stops inflating the result.

Before Go 1.24, the same protections were manual: assign the result to a
package-level sink so it cannot be eliminated, and bracket the setup with
`b.ResetTimer()`.

```go
var sink []byte

func BenchmarkEncode(b *testing.B) {
	payload := makePayload()
	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		sink = Encode(payload)
	}
}
```

`b.ReportAllocs()` on the benchmark, or `-benchmem` on the command line,
adds allocations per operation. For most Go work that column decides more
than nanoseconds do, because allocation is what feeds the collector.

Use `b.Run` for variants, so one function covers a dimension and the names
stay comparable:

```go
for _, size := range []int{1, 100, 10_000} {
	b.Run(strconv.Itoa(size), func(b *testing.B) { ... })
}
```

## Running

```bash
go test -run '^$' -bench . -benchmem -count 10 ./...
```

`-run '^$'` skips the tests so their time does not mix in. `-count 10` is
not decoration: one run is a sample of one, and the first number Go prints
is the one most likely to be wrong.

Never benchmark with `-race`. The detector adds a large, uneven overhead and
the result measures the instrumentation.

Two more sources of lies worth naming: a laptop that changes clock frequency
under load, and a machine doing anything else. A result that cannot be
reproduced twice is not a result.

## Comparing

Eyeballing two outputs is how a 2% regression gets shipped and a 2%
improvement gets celebrated. `benchstat` does the statistics:

```bash
go install golang.org/x/perf/cmd/benchstat@latest

go test -run '^$' -bench . -benchmem -count 10 > old.txt
# change the code
go test -run '^$' -bench . -benchmem -count 10 > new.txt
benchstat old.txt new.txt
```

`benchstat` prints the change with a confidence signal. When it reports `~`,
the difference is not statistically significant — the honest conclusion is
that the change did nothing measurable, not that it helped a little.

Record the result where the decision lives. A commit that claims a
performance win states the benchmark name, the machine, the `-count`, and
the `benchstat` line; a claim without those is an opinion with a number
attached.

## What a benchmark cannot tell you

It measures the code you wrote against the input you chose on the machine
you own. Production has different input distributions, cache pressure from
neighbours, and a scheduler with other work to do. A microbenchmark that
improves while the service does not is the normal outcome when the
bottleneck was never in that function — see [profiling](profiling.md) for
finding out where the time actually goes.
