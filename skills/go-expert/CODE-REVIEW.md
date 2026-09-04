# Go Code Review Directives

A scenario-based review guide for Go. Each directive describes a code shape to
avoid, the runtime sequence it creates, what can fail, and the evidence or
correction a reviewer should require.

This is not a prohibition list. The level describes the learning path, not
severity: a beginner pattern can still create a critical security or
availability incident. A review comment must be tied to the repository's
contract or a credible failure mode.

## How to use these directives

1. Read the `go` directive in `go.mod` before judging version-sensitive code.
2. Identify the owner and lifetime of every mutable value, resource, goroutine,
   channel, lock, transaction, and cancellation signal.
3. Reconstruct the runtime sequence: what starts, what can return, what can be
   canceled, and what cleanup runs at each boundary.
4. For each risky shape, state the consequence and request the smallest safe
   correction or a test proving the behavior is safe.
5. Run repository-configured checks; treat conventional tools as evidence, not
   proof that a behavior is correct.

## Directive format

Each directive should answer these questions:

- **Avoid:** What code shape or assumption is dangerous?
- **Context:** Under which ownership, lifetime, input, or concurrency boundary
  does it become dangerous?
- **Runtime sequence:** What executes first, and what may execute later or in
  parallel?
- **Failure modes:** What errors, panics, races, leaks, corruption, or security
  effects can result?
- **Review directive:** What must the author demonstrate or change?
- **Acceptable correction:** Which ownership transfer, synchronization,
  validation, or test makes the design safe?
- **Classification:** Report the technical level, advisory, impact area, and
  evidence using the shared
  [Code Review scale](../code-review/SKILL.md#two-independent-scales). Do not
  redefine those labels in this Go-specific document.

## Shared review scale

The global `code-review` skill owns the technical levels, advisory outcomes,
evidence labels, and merge policy. This document supplies Go-specific
scenarios only.

A review comment can therefore be written as:

```text
[WARNING] [FIX-OR-TECH-DEBT] [TEMPORAL] [REPRODUCED]
Test depends on the wall clock and local timezone. Fix by injecting a fixed
clock or pass a timestamp explicitly; otherwise create a task with a test
covering the UTC/DST boundary.
```

### Example: cleanup owned by a returning parent

```go
func run(resource *Resource) {
	defer resource.Close()

	for _, job := range jobs {
		go process(resource, job)
	}
}
```

**Context:** `run` starts asynchronous work that borrows `resource`.

**Runtime sequence:** A `go` statement schedules a goroutine but does not wait
for it to begin or finish. `run` may return immediately; its deferred cleanup
then runs. A goroutine may start afterward, or may still be running, while the
resource is already closed.

**Failure modes:** The child sees a closed resource, returns an I/O error,
panics, races with cleanup, or produces incomplete output.

**Review directive:** Avoid parent-scoped cleanup for resources used by
children that can outlive the parent. Require one of these proofs: the parent
waits for all children before returning; ownership moves into a child/helper
whose `defer` runs at the child lifetime; or the resource is explicitly safe
for concurrent use after the parent boundary.

**Acceptable correction:** Use `WaitGroup`/`errgroup` when the parent owns the
lifetime, or open and defer the resource inside the goroutine when the child
owns it. Add a cancellation and error-propagation test.

## Progression by level

| Level | Main concern | Typical impact |
|---|---|---|
| Beginner | Values, control flow, errors, and collection semantics | Wrong output, panic, lost failure, corrupted API response |
| Intermediate | Ownership, resources, HTTP/SQL, context, and concurrency lifecycle | Leaks, hangs, races, retries gone wrong, exhausted resources |
| Expert | Memory model, unsafe code, API contracts, security, and performance | Data corruption, privilege impact, process-wide outage, silent regressions |

## Beginner: correctness foundations

These are the first checks for almost every Go implementation and review.

### 1. Discarding errors

**Problem:** A returned `error` is assigned to `_`, ignored, or overwritten
before it is handled.

**What can happen:** A failed write, close, transaction, flush, rename, or
network operation is reported as success. The program can publish incomplete
data or leave durable state inconsistent.

**Review questions:**

- Is the error intentionally ignorable, and is the reason documented?
- If the error comes from `Close`, `Flush`, `Commit`, or `Sync`, can it report
  data loss after the main operation appeared successful?
- Does the caller return, classify, retry, or otherwise handle the failure?

**Safer shape:** Handle the error at the layer that has enough context to act.
If ignoring it is correct, write `_ = operation()` and explain why.

### 2. Using `panic` for ordinary failures

**Problem:** Input errors, unavailable dependencies, or expected operational
failures cause `panic` instead of returning an error.

**What can happen:** A request crashes a process, bypasses normal recovery,
turns a user error into an outage, or loses a useful error contract.

**Review questions:** Is this an unrecoverable programmer or startup invariant,
or could the caller reasonably handle it?

**Safer shape:** Return an `error`; reserve `panic` for broken invariants or
mandatory initialization that makes continued execution impossible.

### 3. Comparing errors incorrectly

**Problem:** Code compares error strings, uses `==` after wrapping, or uses
`errors.As` where `errors.Is` is needed (or the reverse).

**What can happen:** A wrapped sentinel is missed, a type assertion fails, or
an implementation detail in an error message becomes an accidental API.

**Review questions:**

- Is this checking identity/value (`errors.Is`) or extracting a type
  (`errors.As`)?
- Does `%w` intentionally expose the underlying cause to callers?
- Would changing punctuation or wording break behavior?

**Safer shape:** Use `errors.Is` for sentinel values, `errors.As` for error
types, and `%w` only when the wrapping relationship is part of the contract.

### 4. Mutating the copy from a `range` loop

**Problem:** The value variable in `for _, item := range items` is a copy for
slices, arrays, and maps, but the code mutates `item` expecting the collection
to change.

**What can happen:** The loop completes without updating the original data,
causing silent incorrect output or a partially applied transformation.

**Safer shape:** Use the index (`items[i]`) when mutation is intended, or use a
slice of pointers when pointer ownership is deliberate. Remember that pointer
fields inside a copied struct may still refer to shared data.

### 5. Assuming map iteration order

**Problem:** Code depends on the order produced by `range` over a map.

**What can happen:** Tests become flaky, output changes between runs, cache
keys differ, or a first/last element is selected nondeterministically.

**Safer shape:** Extract keys, sort them, and then iterate; or use an ordered
structure when order is part of the contract.

### 6. Writing to a nil map

**Problem:** A nil map is read safely but panics when assigned to.

**What can happen:** A rarely exercised initialization path crashes at runtime.
A map shared between goroutines can also trigger a fatal runtime error when
read and written concurrently.

**Review questions:** Is the map allocated before the first write? Is its
ownership synchronized if multiple goroutines can access it?

**Safer shape:** Initialize with `make` at the owning boundary and document
whether nil means “not initialized” or “empty.”

### 7. Confusing nil and empty slices

**Problem:** Code treats `nil` and `[]T{}` as interchangeable at a boundary
where the distinction is observable.

**What can happen:** `encoding/json` emits `null` for a nil slice and `[]` for
an empty non-nil slice. Callers may misread absence as an empty result, or
vice versa.

**Safer shape:** Define the API contract explicitly. Internally, usually test
`len(s) == 0` rather than testing only `s == nil`.

### 8. Sharing slice backing arrays accidentally

**Problem:** Slicing copies a slice header, not the backing array. A later
`append` can reuse spare capacity and mutate another slice that shares it.

**What can happen:** A helper unexpectedly changes caller data, two results
interfere, or a data race appears after the slices cross goroutine boundaries.

**Safer shape:** Clone when ownership must be independent, or use a full slice
expression (`s[low:high:max]`) to cap append capacity when a copy is not
needed. Verify the ownership contract rather than applying either blindly.

### 9. Retaining large backing arrays

**Problem:** A small subslice, substring, or pointer into a large object keeps
the larger allocation reachable.

**What can happen:** Memory remains retained long after the useful data is
small, producing a heap growth or latency problem under sustained load.

**Safer shape:** Copy the small result when it must outlive the large source,
and measure before applying allocation-heavy copies broadly.

### 10. Misunderstanding `defer` evaluation and lifetime

**Problem:** Deferred arguments are evaluated when `defer` executes, not when
the deferred call runs. Deferring resource cleanup inside a long loop delays
all cleanup until the surrounding function returns.

**What can happen:** Logs contain stale values, files or response bodies remain
open, connection pools are exhausted, or a loop accumulates large state.

**Safer shape:** Capture the intended value explicitly and put per-item work
in a helper function so its `defer` runs at the end of each iteration.

### 11. Shadowing a variable

**Problem:** `:=` or an inner declaration creates a new variable with the same
name as an outer one, often around `err`.

**What can happen:** The code checks or returns a different variable than the
reviewer expects. The program compiles while updating the wrong state.

**Review questions:** Does the declaration introduce at least one new
variable? Is the nearest scope obvious to a reader?

**Safer shape:** Use a deliberate short scope, distinct names, or `=` when
reassigning existing variables. Do not ban shadowing mechanically; identify
where it changes behavior.

### 12. Silent numeric conversion and overflow

**Problem:** Converting between integer types, signedness, floats, or sizes can
truncate, wrap, or lose precision without an error.

**What can happen:** A negative size becomes huge, a timestamp loses precision,
a length check is bypassed, or an allocation receives an unexpected value.

**Safer shape:** Validate ranges before conversion and keep units explicit.
Treat external numbers as untrusted input.

## Intermediate: boundaries and lifecycle

These checks become important as code handles resources, requests, or
concurrency.

### 13. The typed-nil interface

**Problem:** An interface containing a typed nil pointer is itself non-nil.
For example, `var p *Thing; var v any = p` makes `v != nil`.

**What can happen:** A nil check passes and a later method call panics or
performs unexpected behavior. Error-returning interfaces can look successful
when they contain a typed nil.

**Safer shape:** Keep nil semantics at concrete boundaries, return a genuinely
nil interface when absence is intended, and avoid interfaces solely to hide
optional pointers. Test nil and typed-nil cases explicitly.

### 14. Copying synchronization values

**Problem:** A struct containing `sync.Mutex`, `sync.RWMutex`, `sync.Once`,
`sync.WaitGroup`, or a similar no-copy value is copied after use, often by a
value receiver or assignment.

**What can happen:** Different copies protect different state, a wait group
counter is split, or the runtime enters an invalid synchronization state.

**Safer shape:** Use pointer receivers and pass synchronization owners by
pointer. Treat `go vet` copylock diagnostics as a prompt to inspect ownership,
not as a cosmetic warning.

### 15. Choosing value and pointer receivers accidentally

**Problem:** A value receiver copies the receiver, while a pointer receiver
shares mutable state and participates in a different method set.

**What can happen:** Mutations disappear, expensive values are copied, mutexes
are copied, or a type no longer satisfies an interface at the call site.

**Review questions:** Does the method mutate state? Is the value large? Does it
contain a synchronization field? Which method set must satisfy the interface?

**Safer shape:** Choose receiver style from mutation, copying, identity, and
method-set requirements; keep it consistent for the type.

### 16. Goroutines without a lifecycle

**Problem:** A goroutine is started without a clear owner, cancellation path,
completion signal, or error destination.

**What can happen:** Goroutines leak while blocked on a channel or I/O, work
continues after the request is gone, errors disappear, and memory usage grows.

**Review questions:**

- Who stops this goroutine and how is that path tested?
- What happens when the consumer exits early?
- Where does the goroutine report failure?
- Can it block forever on send, receive, or an unbuffered result channel?

**Safer shape:** Tie work to a context, make completion observable, and ensure
every blocking operation has an exit path.

### 17. Closing a channel from the wrong owner

**Problem:** A receiver closes a channel, multiple senders close it, or code
closes a channel twice.

**What can happen:** A sender panics with “send on closed channel,” a second
close panics, or consumers observe premature termination.

**Safer shape:** The component that owns the sending side and knows no more
values will arrive should normally close the channel. If ownership is
ambiguous, use context cancellation or a separate completion signal.

### 18. Nil channels and accidental blocking

**Problem:** Sends and receives on a nil channel block forever. A `select` case
with a nil channel is effectively disabled.

**What can happen:** A worker deadlocks, shutdown hangs, or a dynamically
configured select silently stops making progress.

**Safer shape:** Initialize channels at the ownership boundary, treat nil as an
explicit state, and test enable/disable transitions around `select`.

### 19. Starting `WaitGroup` work incorrectly

**Problem:** `Add` happens inside the goroutine, `Wait` can race with `Add`, or
a code path forgets `Done`.

**What can happen:** `Wait` returns early, the counter becomes negative and
panics, or the process waits forever.

**Safer shape:** Call `Add` before starting each goroutine, use `defer Done()`
immediately inside it, and prefer a higher-level structured concurrency
helper when the repository already has one.

### 20. Ignoring context cancellation

**Problem:** Code accepts a context but does not pass it to downstream calls,
checks `ctx.Done()`, or uses `context.Background()` where the caller's context
was available.

**What can happen:** Timed-out requests continue consuming connections and
CPU, shutdown does not finish, and cancellation or credentials do not cross a
process boundary.

**Safer shape:** Pass context explicitly as the first parameter after the
receiver, use context-aware APIs, and return promptly on cancellation. Do not
store a request context in a reusable long-lived struct.

### 21. Misusing context values

**Problem:** Context values carry optional application parameters, mutable
state, or required dependencies instead of request-scoped metadata.

**What can happen:** Required inputs become invisible in the function
signature, type assertions panic, keys collide, and values outlive the scope
that produced them.

**Safer shape:** Use typed private keys only for request-scoped cross-cutting
metadata. Pass required business data and dependencies as explicit parameters.

### 22. Timer and ticker lifecycle errors

**Problem:** A timer or ticker is created repeatedly without stopping it, a
`time.After` call is placed in a hot loop, or cancellation is not connected to
the timer.

**What can happen:** The loop allocates unnecessarily, resources remain live,
shutdown is delayed, or a stale timer wins a `select` unexpectedly.

**Version note:** The garbage-collection behavior of unreferenced
`time.After` timers changed in Go 1.23. Check the module version before making
a historical leak claim. Explicit `time.NewTimer`/`Stop` or
`context.WithTimeout` can still make lifecycle intent clearer.

### 23. Forgetting HTTP response cleanup and timeouts

**Problem:** Code does not close `http.Response.Body`, does not inspect the
response status, or uses a client with no effective timeout for untrusted or
slow endpoints.

**What can happen:** Connections are not reused, file descriptors and sockets
are retained, error pages are parsed as success, or a request hangs
indefinitely.

**Safer shape:** Check the error before using the response, validate status,
close the body, set deadlines appropriate to the operation, and make
cancellation flow through the request context.

### 24. Mishandling `database/sql` resources

**Problem:** Rows, statements, or transactions are not closed or checked for
errors. A transaction returns early without rollback, or SQL is built by
concatenating external input.

**What can happen:** Connection pools are exhausted, iteration errors are
missed, partial work is committed, or input changes query meaning and enables
SQL injection.

**Safer shape:** Parameterize values, defer cleanup at the ownership boundary,
check `rows.Err()`, and make commit/rollback behavior explicit on every path.

### 25. `encoding/json` zero-value surprises

**Problem:** `omitempty`, nil pointers, nil slices, zero numbers, and false
booleans are used without deciding whether “absent” differs from “zero.”

**What can happen:** A client cannot clear a field, an update silently omits a
value, `null` and `[]` change meaning, or backward-compatible wire behavior
breaks.

**Safer shape:** Model presence explicitly with pointers or an option type when
needed, test the serialized wire form, and document compatibility behavior.

### 26. Closure capture and Go version semantics

**Problem:** A closure or goroutine captures a loop variable and assumes each
iteration has a distinct binding.

**What can happen:** Work uses the wrong item, logs repeat the final value, or
concurrent operations update the wrong record.

**Version note:** The loop-variable semantics changed for modules declaring Go
1.22 or newer. For older language semantics, inspect captures aggressively.
Even with newer semantics, review captured mutable state, pointer ownership,
and synchronization; the version change does not make shared state safe.

### 27. Recovering from panic in the wrong place

**Problem:** `recover` is called outside a deferred function in the same
panicking goroutine, or recovery is used as normal error handling.

**What can happen:** The panic still crashes the process, a worker dies without
reporting failure, or corrupted state is hidden behind a generic recovery.

**Safer shape:** Return ordinary errors. If a process boundary must recover,
use a deferred recovery at that boundary, record the panic safely, and restore
an explicit failure or shutdown policy.

### 28. Flaky or weak tests

**Problem:** Tests use sleeps for synchronization, share mutable global state,
assert only that code did not panic, or skip failure-path and cancellation
cases.

**What can happen:** CI failures depend on machine load, races go undetected,
and regressions pass because the test never observes the contract.

**Safer shape:** Synchronize on observable events, use table-driven cases,
exercise errors and cancellation, and run concurrent tests with the race
detector when supported.

## Cross-cutting directives

### Time-dependent tests, UTC, timezones, and durations

**Avoid:** Calling `time.Now()` directly in test expectations, deriving both
sides of an assertion from the wall clock, mixing UTC and local time without a
contract, comparing `time.Time` with `==`, or treating a calendar day as a
fixed `24*time.Hour` duration.

**Context:** Wall-clock time moves, two calls to `time.Now()` return different
instants, the machine timezone may differ between developer and CI, and local
calendar days can cross daylight-saving transitions. `time.Time` can also carry
location and monotonic-clock data that make `==` different from instant
comparison.

**Runtime sequence:** A test obtains a time from the host clock; production
code obtains another time, possibly in another location. Near midnight, a DST
transition, or a clock adjustment, the date and offset can change between
those operations. `Add(24*time.Hour)` advances an elapsed duration, while
`AddDate(0, 0, 1)` advances a calendar date; they are not interchangeable at a
DST boundary.

**Failure modes:** The test can pass while failing to prove the contract
(false confidence), fail only near a clock boundary, report a wrong offset or
duration, pass in UTC but fail in a local timezone, or encode the wrong
business meaning for “tomorrow.”

**Review directive:** Classify this as `WARNING` / `FIX-OR-TECH-DEBT` /
`TEMPORAL` / `REPRODUCED`. It is not automatically a `BLOCKER`. The author
must either make the test deterministic in the current change or create a
linked tech-debt task before the review is complete. Use `FIX-NOW` when the
review requires correction in this change with no deferral. Promote it to
`BLOCKER` only when the test can mask a production defect, controls a critical
expiration/authentication contract, or makes the merge gate unreliable.

**Acceptable correction:** Prefer a pure function that receives an explicit
`time.Time`. Otherwise inject a small `now func() time.Time` seam when there is
one consumer, or a clock abstraction only when multiple real consumers need
it. Use a fixed instant and explicit `*time.Location` in tests; use
`Time.Equal` for instants; normalize to UTC at an instant-based boundary; use
`ParseInLocation` when local calendar input is intentional; and use `AddDate`
for calendar arithmetic.

**Evidence required:** Add a deterministic test for the relevant contract,
including a UTC/local or DST boundary when it matters. Do not “fix” a flaky
failure by widening tolerances or adding sleeps without proving the clock
contract.

**Tech-debt minimum:** Record the affected test or package, the false-positive
or offset risk, the expected time contract, the deterministic correction, and
an acceptance test. “Use a clock later” is not sufficient context.

## Expert: systems, contracts, and performance

These require reasoning about contracts, the memory model, trust boundaries,
or measured runtime behavior.

### 29. Data race versus race condition

**Problem:** Code has no detector-reported data race but still has an invalid
ordering, or it has unsynchronized memory access hidden behind a “usually
works” assumption.

**What can happen:** Lost updates, stale configuration, corrupted invariants,
or behavior that changes with scheduling and CPU architecture.

**Safer shape:** Identify the invariant and synchronization protocol, not only
individual variables. Use mutexes for shared state, atomics for deliberately
small state transitions, and `go test -race` as evidence—not proof of absence.

### 30. Deadlocks, starvation, and backpressure failures

**Problem:** A lock is acquired in inconsistent order, a producer has no
bounded queue, a consumer exits without draining, or a `select` default path
spins.

**What can happen:** Requests hang, CPU reaches 100%, memory grows without
bound, or low-priority work starves critical work.

**Review questions:**

- What is the queue bound and what happens when it fills?
- Can every blocked send/receive/lock be interrupted during shutdown?
- Is lock ordering documented and consistent?
- Does `default` represent a deliberate non-blocking operation or a busy loop?

**Safer shape:** Define ownership, bounds, cancellation, fairness, and overload
behavior before adding another goroutine or buffer.

### 31. Incorrect atomic protocols

**Problem:** One field is atomic while related fields are not, a pointer is
published before initialization, or atomic operations are used without a
clear invariant.

**What can happen:** Readers observe a mixture of old and new state, updates
are lost, or a race is merely hidden from casual review.

**Safer shape:** Prefer a mutex when it makes the invariant clearer. If using
atomics, document the state machine and publication boundary, use the typed
`sync/atomic` APIs where supported, and test under the race detector.

### 32. `sync.Once` and one-time initialization failures

**Problem:** Initialization inside `sync.Once.Do` panics or records a failure
without a retry or error result, but callers assume initialization succeeded.

**What can happen:** Every future caller observes a permanently incomplete
state, or a transient dependency failure becomes process-lifetime failure.

**Safer shape:** Decide whether failure is permanent. Return initialization
errors explicitly when retry matters; use `sync.Once` only for a contract that
really is one-shot.

### 33. Using `sync.Pool` as storage

**Problem:** Code expects an item put into `sync.Pool` to remain available or
uses the pool to manage durable ownership.

**What can happen:** Values disappear at any GC cycle, stale data is reused,
large buffers remain retained, or correctness depends on an optimization.

**Safer shape:** Use `sync.Pool` only for temporary reusable allocations where
absence is always safe and reset is complete before reuse.

### 34. Memory retention through maps, slices, and caches

**Problem:** A cache has no bound, a map keeps references to deleted values, or
slicing keeps pointer-rich backing storage reachable.

**What can happen:** Heap usage grows until GC and latency degrade, or the
process is killed despite apparently small live results.

**Safer shape:** Set ownership and eviction limits, clear references when
appropriate, clone retained subsets, and verify with heap profiles rather than
assuming the GC can infer logical liveness.

### 35. Treating `time.Time` equality as instant equality

**Problem:** Code uses `==` for times that may differ in location or monotonic
clock data, or compares formatted strings.

**What can happen:** Equivalent instants compare unequal, map keys behave
unexpectedly, or tests fail only on values produced by different code paths.

**Safer shape:** Use `Time.Equal` for instants, define location and precision
contracts, and use a clock seam when tests need deterministic time.

### 36. Finalizers and cleanup assumptions

**Problem:** A finalizer is used as deterministic resource management or a
replacement for `Close`.

**What can happen:** File descriptors, locks, or memory remain held for an
unbounded period, and shutdown behavior becomes nondeterministic.

**Safer shape:** Make ownership explicit with `Close`, context cancellation,
and structured shutdown. Treat finalizers, when used at all, as a last-resort
leak detector or safety net—not the primary lifecycle.

### 37. Reflection without kind and validity checks

**Problem:** `reflect.Value` is dereferenced, compared, or passed to `IsNil`
without checking validity and whether its kind supports the operation.

**What can happen:** Valid input causes a reflection panic, an absent value is
confused with a typed nil, or a generic helper silently skips a type.

**Safer shape:** Keep reflection at narrow boundaries, validate `IsValid` and
kind before operations, and prefer typed code or generics when the contract is
known.

### 38. `unsafe` and FFI trust-boundary violations

**Problem:** `unsafe.Pointer`, string/byte reinterpretation, `cgo`, or a
manual ABI assumes layout, lifetime, alignment, or aliasing guarantees that
are not actually established.

**What can happen:** Memory corruption, use-after-free, invalid pointers,
architecture-specific crashes, or a security vulnerability that bypasses Go's
usual safety guarantees.

**Safer shape:** Isolate unsafe code behind a tiny tested boundary, document
invariants, use `checkptr`-appropriate validation where possible, and keep
foreign memory ownership and callback lifetimes explicit.

### 39. Interface and error contracts that leak implementation

**Problem:** An interface is created in the provider package before a real
consumer exists, or an error is wrapped/exposed in a way that couples callers
to an internal implementation.

**What can happen:** A small implementation change becomes a breaking API
change, mocks multiply, or callers depend on sentinel values that were never
meant to be public.

**Safer shape:** Define small interfaces near consumers, return concrete types
when sufficient, and deliberately choose which errors are part of the public
contract.

### 40. Command and input boundary mistakes

**Problem:** External input is concatenated into SQL, shell commands, paths,
regular expressions, URLs, or log messages without an explicit trust-boundary
design.

**What can happen:** Injection, path traversal, credential leakage, denial of
service through expensive patterns, or misleading security logs.

**Safer shape:** Parameterize SQL, pass command arguments without invoking a
shell when possible, validate paths and resource limits, constrain regex and
URL behavior, and redact secrets from errors and logs. Treat
`exec.CommandContext` as a cancellation aid, not an input sanitizer.

### 41. Insecure randomness and cryptographic misuse

**Problem:** `math/rand` is used for secrets, tokens, reset links, nonces, or
security decisions; cryptographic APIs are configured from guessable or reused
material.

**What can happen:** Attackers predict identifiers or bypass authorization
flows. A secure-looking feature becomes reproducible by an attacker.

**Safer shape:** Use `crypto/rand` for security-sensitive randomness, use
well-reviewed standard cryptographic protocols, and keep key, nonce, and
algorithm contracts explicit.

### 42. Benchmarks that measure the wrong thing

**Problem:** A benchmark includes setup in the timed region, is optimized away,
uses unrealistic data, ignores allocations, or reports a result without a
profile or representative workload.

**What can happen:** An optimization makes production slower, hides contention,
or trades memory for a meaningless microbenchmark win.

**Safer shape:** Use `testing.B` correctly, reset timers around setup, measure
allocations when relevant, benchmark realistic distributions, and confirm
with CPU/heap profiles or traces before changing architecture.

### 43. Runtime and GC regressions misdiagnosed as application bugs

**Problem:** A Go upgrade, architecture change, `GOEXPERIMENT`, scheduler
change, or workload shift is ignored while application code is blamed for a
CPU or latency regression.

**What can happen:** A code change “fixes” the symptom while preserving the
actual regression, or a useful runtime improvement is disabled unnecessarily.

**Safer shape:** Compare Go versions and build settings, inspect runtime
metrics, use `GODEBUG=gctrace=1` only as supporting evidence, and collect
profiles before changing allocation or concurrency design.

### 44. Dependency and vulnerability reachability gaps

**Problem:** A dependency scanner result is treated as either automatically
exploitable or automatically harmless without checking call reachability,
input paths, and deployment context.

**What can happen:** A reachable vulnerable function is shipped, or a noisy
finding causes teams to disable useful scanning.

**Safer shape:** Run `govulncheck ./...`, inspect the call path and affected
version, update or mitigate the dependency, and record residual risk when a
fix cannot land immediately. Do not claim that a clean scan proves application
security.

## Automated review baseline

First obey repository-configured gates. If the repository does not define
stronger requirements, label these as conventional checks rather than local
policy:

```bash
gofmt -d path/to/touched.go
goimports -d path/to/touched.go
go vet ./...
staticcheck ./...
go test ./...
go test -race ./...
govulncheck ./...
```

Tool scope:

- `gofmt` and `goimports`: mechanical formatting and import organization.
- `go vet`: standard analyzers for likely correctness mistakes.
- `staticcheck`: complementary correctness, performance, and simplification
  analysis.
- `go test`: package and behavior verification.
- `go test -race`: evidence for data races in exercised paths, never proof of
  race absence.
- `govulncheck`: vulnerability analysis with dependency and call-path context.

## Source index

- [Go Code Review Comments](https://go.dev/wiki/CodeReviewComments) — official
  review guidance for contexts, errors, copying, crypto, slices, goroutine
  lifetimes, naming, and tests.
- [Go Common Mistakes](https://go.dev/wiki/CommonMistakes) — official examples
  of recurring language mistakes.
- [Go memory model](https://go.dev/ref/mem) — synchronization and race semantics.
- [Go 1.22 release notes](https://go.dev/doc/go1.22) — loop-variable semantics.
- [Go 1.23 release notes](https://go.dev/doc/go1.23) — timer behavior changes.
- [100 Go Mistakes](https://100go.co/) — practical catalog of data, control
  flow, errors, concurrency, standard library, testing, and performance traps.
- [Go101](https://go101.org/) — deeper language and runtime semantics.
- [Staticcheck](https://staticcheck.dev/docs/) — complementary static analysis.
- [`go vet`](https://pkg.go.dev/cmd/vet) — standard Go analyzers.
- [`govulncheck`](https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck) — Go
  vulnerability analysis.
