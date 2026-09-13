# Zig Code Review Directives

Zig-specific review scenarios: the code shape to avoid, the runtime or
compile-time sequence it creates, what can fail, and the evidence or
correction a reviewer should require.

The review method, scenario format, tracks, areas, technical levels,
advisories, and evidence labels are owned by the shared
[Code Review skill](../code-review/SKILL.md). This file adds Zig scenarios
only and never redefines those labels. Before judging version-sensitive
code, run `zig version`, read `.minimum_zig_version` in `build.zig.zon`,
run `zig-era <root>` to name the era the code was written for (old names
are read through [`VERSIONS.md`](VERSIONS.md)), and remember that Zig is
pre-1.0: names in this file were verified on
**0.16.0** and are marked where they moved recently.

Scenarios are grouped by [track](../code-review/SKILL.md#tracks). The track
describes the learning path, not the severity: a Foundations pattern can
still create a critical security or availability incident. A review comment
must be tied to the repository's contract or a credible failure mode.

The compiler enforces explicit allocation and explicit errors, and the
safety modes catch a long list of mistakes in Debug and ReleaseSafe. Review
therefore concentrates on what survives to ReleaseFast: cleanup on the
error path, ownership across the allocator boundary, invariants asserted
with `unreachable` or a cast, `undefined` read before write, foreign memory,
and tasks nobody awaits.

## Worked example (full form)

```zig
const Pair = struct { a: []u8, b: []u8 };

fn makePair(gpa: Allocator) Allocator.Error!Pair {
    const a = try gpa.alloc(u8, 8);
    const b = try gpa.alloc(u8, 8);
    return .{ .a = a, .b = b };
}
```

**Context:** A function that performs two allocations and hands both to the
caller on success.

**Runtime sequence:** The first `alloc` succeeds. The second fails and `try`
returns the error immediately. Nothing frees `a`. The caller never receives
the pair, so it cannot free `a` either.

**Failure modes:** A leak on every out-of-memory or quota failure between the
two allocations. Under `std.testing.checkAllAllocationFailures` the test
reports the leak (verified on 0.16.0); in production it is silent.

**Review directive:** Every allocation that is handed to the caller on
success is protected by `errdefer` until the function returns. Require the
`errdefer` on the line after the allocation and a
`checkAllAllocationFailures` test for functions with more than one
allocation.

**Acceptable correction:** `errdefer gpa.free(a);` after the first
allocation. Add the allocation-failure test.

**Classification:** `WARNING` / `FIX-NOW` / `RESOURCE` / `REPRODUCED`.

## Foundations: correctness

### 1. Allocation without a paired release

**Problem:** An `alloc`, `create`, `dupe`, `ArrayList` growth, or
`toOwnedSlice` has no `defer`, `errdefer`, or documented transfer of
ownership.

**What can happen:** Leaks in normal or error paths; `std.testing.allocator`
fails the test run (exit 1, verified), production leaks quietly.

**Safer shape:** Pair each allocation on the next line: `defer` when the
function owns it, `errdefer` when the caller receives it on success. Say
in the doc comment who frees and with which allocator.

### 2. Freeing with a different allocator

**Problem:** Memory allocated with an arena is freed with the general
purpose allocator, or a slice from `toOwnedSlice(gpa)` is freed with
another allocator instance.

**What can happen:** Undefined behavior or an immediate panic under
`DebugAllocator`; corruption elsewhere.

**Safer shape:** Carry the allocator with the data (a field, or a parameter
on every call) and free only with it. Arenas free everything at once;
nothing allocated from an arena is freed individually.

### 3. `unreachable` and `catch unreachable` on expected input

**Problem:** `unreachable`, `catch unreachable`, or `orelse unreachable` on
a value that comes from input, the network, a file, or a computation the
author did not prove.

**What can happen:** A panic in Debug and ReleaseSafe; undefined behavior in
ReleaseFast where the compiler assumes the branch never runs.

**Safer shape:** Return an error or an optional for anything external;
`unreachable` only states an invariant the code established, with a
comment naming it.

### 4. Reading `undefined`

**Problem:** A variable or array initialized with `undefined` is read before
every element is written, often after a loop that exits early.

**What can happen:** In Debug and ReleaseSafe memory holds `0xaa` and bugs
look deterministic; in ReleaseFast the value is anything.

**Safer shape:** Initialize with a real value unless the write-before-read
is obvious and local; for buffers, track the written length and slice to
it.

### 5. Casts that assert without checking

**Problem:** `@intCast`, `@truncate`, `@intFromFloat`, `@enumFromInt`,
`@errorCast`, or `@alignCast` applied to a value from outside the
function.

**What can happen:** Safety panic in Debug and ReleaseSafe; silent
truncation, invalid enum, or misaligned pointer in ReleaseFast.

**Safer shape:** `std.math.cast` or an explicit range check that returns an
error; `@intCast` only after the check, or on values the code itself
bounded.

### 6. Overflow operators chosen by accident

**Problem:** `+`, `-`, `*` on values that may overflow, or wrapping
operators (`+%`) used where overflow is a bug.

**What can happen:** Panic in safe modes; wrap in ReleaseFast (verified:
`u8` 255 + 1 becomes 0 under `-OReleaseFast`).

**Safer shape:** Decide the contract: `+%` for wrapping, `+|` for
saturating, `@addWithOverflow` to detect, or a wider type. Test the edge.

### 7. Slices that outlive their backing memory

**Problem:** A function returns a slice into a local array, an
`ArrayList.items` slice is kept across an `append`, or a slice into an
arena is used after the arena is reset.

**What can happen:** Dangling pointer; `append` may reallocate and move
`items`; the arena reuses the memory.

**Safer shape:** Return owned slices (`toOwnedSlice`) or copies; re-read
`items` after any growth; document lifetimes tied to an arena.

### 8. Optional and sentinel confusion

**Problem:** A sentinel value (`0`, `-1`, `maxInt`) models absence where an
optional (`?T`) exists; or a `[*:0]u8` is passed where the callee expects
a length.

**What can happen:** The sentinel collides with a real value; a many-item
pointer is read past its end.

**Safer shape:** `?T` for absence, `[]T` slices for lengths, `std.mem.span`
to convert sentinel-terminated pointers at the boundary.

### 9. Error sets that hide the cause

**Problem:** `catch |_| return error.Failed`, `anyerror` in a public
signature, or errors converted to `bool`/`null`.

**What can happen:** Callers cannot switch on the cause; error return
traces stop at the conversion; retryable and terminal failures look alike.

**Safer shape:** Explicit error sets on public functions, `try` to
propagate, `catch` only where the handling differs by error.

### 10. Comptime that buys nothing

**Problem:** A `comptime` parameter, an `inline for`, or a generated type
where a runtime value or a plain struct would do; comptime string
building for messages.

**What can happen:** Longer compile times, one instantiation per call site,
harder debugging, and no behavioral gain.

**Safer shape:** Ask what the comptime value decides (a size, a type, a
table). If nothing, make it runtime.

## Boundaries: resources and lifecycle

### 11. Tasks nobody awaits (0.16)

**Problem:** `group.async` or `io.async` started without an `await` or
`cancel` before the owner returns; a `Future` dropped.

**What can happen:** Work continues past its owner's lifetime, writes into
freed memory (the result slot was a local), errors are lost.

**Safer shape:** `defer group.cancel(io)` as the net, `try group.await(io)`
on the success path; results live at least as long as the group.

### 12. `io.async` assumed concurrent

**Problem:** Code relies on two `io.async` calls making progress at the
same time (a producer and consumer waiting on each other).

**What can happen:** `io.async` may run the function inline before
returning; the pair deadlocks under `Io.Threaded` when threads are
exhausted or under a single-threaded `Io`.

**Safer shape:** `io.concurrent` when concurrency is required by the
contract, and handle its error; design so that `async` running inline is
still correct.

### 13. Synchronization primitives from the wrong era

**Problem:** `std.Thread.Mutex` and friends in code targeting 0.16, or a
mutex held across an `Io` operation that can block.

**What can happen:** Compile failure on 0.16 (`Mutex` moved to
`std.Io.Mutex`); blocking a worker thread of `Io.Threaded` while holding a
lock other tasks need.

**Safer shape:** `std.Io.Mutex` / `Condition` / `RwLock` with the `io`
instance; keep critical sections free of I/O.

### 14. Files, sockets, and processes not closed

**Problem:** `openFile`, `createFile`, a socket, or a spawned child without
`defer close` / `wait`.

**What can happen:** Descriptor exhaustion; zombie processes; buffered
output never flushed.

**Safer shape:** `defer file.close(io)` on the line after opening;
`process.run` for collect-and-wait; explicit `flush()` on writers before
exit.

### 15. Writers to global stdio

**Problem:** Library code prints with `std.debug.print` or grabs
`Io.File.stdout()` directly instead of receiving an `*Io.Writer`.

**What can happen:** Untestable output, interleaved writes, no way for the
caller to redirect; `std.debug.print` is unbuffered stderr.

**Safer shape:** Accept `*Io.Writer`; the entry point decides the sink and
the buffer. `std.debug.print` for debugging only.

### 16. Format specifiers on custom types

**Problem:** `{}` or `{s}` used for a type with a `format` method (0.15+
requires `{f}`), or `{s}` on a non-string slice.

**What can happen:** Compile error, or a debug dump where the formatted
form was intended.

**Safer shape:** `{f}` for types with `format`, `{s}` for `[]const u8`,
`{d}` for integers, `{any}` for a debug dump.

### 17. Build graph that runs the world

**Problem:** `build.zig` performs I/O or heavy work at graph construction
time instead of declaring steps; test steps that do not depend on the
modules they should cover.

**What can happen:** Slow `zig build --help`, no caching, tests that never
run.

**Safer shape:** Declare steps and dependencies; `b.addTest(.{ .root_module
= mod })` per module; `test_step.dependOn` for each run step.

### 18. Dependencies without identity

**Problem:** A dependency in `build.zig.zon` with a `url` but no `hash`, a
`path` dependency that is not part of the repository, or a changed
`.fingerprint`.

**What can happen:** The build fetches whatever the URL serves today; the
package identity is hijacked.

**Safer shape:** `zig fetch --save <url>` to pin `hash`; `path` only for
in-repo packages; `.fingerprint` untouched except in a deliberate fork.

### 19. Tests that pass by not running

**Problem:** A `test` block in a file the build never references; a test
that returns `error.SkipZigTest` unconditionally; assertions on
`undefined` values.

**What can happen:** Green suites over untested code.

**Safer shape:** Reference test files from the root module (`_ =
@import("x.zig")` in a `test` block or `std.testing.refAllDecls`), run
`zig build test` and check the count, skip conditionally.

## Systems: contracts, safety, and interop

### 20. ReleaseFast assumed as safe

**Problem:** Code that is only correct because a safety check catches a
bad value, shipped in ReleaseFast.

**What can happen:** Every safety-checked behavior in the language
reference becomes undefined: out-of-bounds, overflow, invalid enum,
unwrapping null, wrong union field.

**Safer shape:** Validate inputs explicitly; run the suite under
`-Doptimize=ReleaseSafe` and, for the hot paths that ship as
ReleaseFast, add tests that do not rely on a panic to fail.

### 21. `@ptrCast` and layout assumptions

**Problem:** `@ptrCast` between unrelated types, between slices of
different element sizes, or on `packed`/`extern` structs whose layout was
not pinned.

**What can happen:** Undetectable illegal behavior through the resulting
pointer (the reference's own words); misaligned access; wrong element
count.

**Safer shape:** `extern struct` or `packed struct` when layout is a
contract; `std.mem.bytesAsSlice` and `sliceAsBytes` for byte views;
isolate the cast behind one function with the invariant in a comment.

### 22. Foreign memory trusted

**Problem:** A `[*c]T` from C dereferenced without a null check; a length
from a header trusted over the received bytes; a C string used without
verifying termination.

**What can happen:** Null dereference, over-read, injection of
attacker-controlled lengths.

**Safer shape:** Check for null, bound with `[0..len]` from a validated
length, `std.mem.span` only when termination is guaranteed by the
producer, and `std.math.cast` for every foreign integer.

### 23. Errors and panics crossing the C boundary

**Problem:** An `export` or `callconv(.c)` function that can `try`, panic,
or hit a safety check.

**What can happen:** Unwinding does not exist for C callers; a panic aborts
the process; an error union is not a C type.

**Safer shape:** Return status codes; catch everything at the boundary;
keep safety-checked operations validated before the call.

### 24. Thread and data race protocols

**Problem:** Shared state mutated from several threads with no `Mutex` or
`atomic.Value`, or an atomic flag published without an ordering that
covers the data it guards.

**What can happen:** Torn reads, lost updates, stale data on weakly
ordered architectures.

**Safer shape:** One owner per mutable value; `std.Io.Mutex` for compound
state; `std.atomic.Value(T)` with `.release`/`.acquire` pairs for
publication; test under multiple threads.

### 25. Arena misuse

**Problem:** An arena used as a general-purpose allocator for a
long-running loop, or memory from an arena returned to a caller who frees
it individually.

**What can happen:** Unbounded growth (arenas never free until reset), or
a free with the wrong allocator.

**Safer shape:** Arenas for one lifetime (a request, a parse, the process);
reset or deinit at its end; document that the caller must not free arena
memory.

### 26. Build-time trust

**Problem:** A third-party `build.zig` or translate-c step executes without
review; a dependency's `.paths` pulls in scripts that run at build time.

**What can happen:** Arbitrary code on every developer and CI machine at
build time.

**Safer shape:** Read the dependency's `build.zig` before adding it; pin by
hash; vendor when the source is small; treat `zig build` as running the
dependency's code.

### 27. `@cImport` in new code (0.16)

**Problem:** New code adds `@cImport` where the project already uses the
translate-c build step, or a migration mixes both for the same header.

**What can happen:** `@cImport` is deprecated in 0.16; two translations of
one header drift; removal in a later release breaks the build.

**Safer shape:** `b.addTranslateC` in `build.zig` and `@import` of the
resulting module; keep `@cImport` only in legacy code until its migration
step.

### 28. Performance claims without measurement

**Problem:** `inline` everywhere, `@setRuntimeSafety(false)` on a hunch,
manual SIMD without a benchmark, arenas "for speed" without a profile.

**What can happen:** No gain, lost safety, harder code.

**Safer shape:** Benchmark with representative input in the shipped
optimize mode; profile (`perf`, `valgrind`, `--cpu-prof` equivalents for
the target); apply the one change the profile names.

## Cross-cutting directives

### Version-sensitive names

**Avoid:** Copying a snippet from a blog, a book, or an older project
without checking the Zig version it targets.

**Context:** Between 0.11 and 0.16 the language removed async keywords,
changed pointer casts, split `@Type`, made `ArrayList` unmanaged, rewrote
`Io`, moved `std.fs` and `std.Thread.Mutex` into `std.Io`, renamed the
general-purpose allocator, and deprecated `@cImport`.

**Failure modes:** Compile errors at best; at worst a snippet that compiles
with different semantics (`io.async` inline versus concurrent).

**Review directive:** Every version-sensitive claim in a review or a doc
names the release it was verified on. When the project floor differs from
the reviewer's toolchain, the project floor wins.

**Classification:** `SUGGESTION` / `FIX-NOW` / `POLICY` / `TRACE`; promote
to `WARNING` when the snippet changes concurrency or memory semantics.

### Safety mode coverage

**Avoid:** A test suite that runs only in Debug for code shipped as
ReleaseFast or ReleaseSmall.

**Review directive:** Require at least one CI run under
`-Doptimize=ReleaseSafe`, and for ReleaseFast shipments, tests whose
assertions do not depend on a safety panic.

**Classification:** `WARNING` / `FIX-OR-TECH-DEBT` / `TEST` / `TRACE`.

## Automated review baseline

The verification commands are defined once in
[`SKILL.md`](SKILL.md#-conventional-verification-baseline).
Repository-configured gates always take precedence.

Evidence scope:

- `zig fmt --check`: mechanical formatting only.
- `zig build`: the graph compiles for the default target and mode.
- `zig build test`: `test` blocks reachable from the declared test steps;
  leak detection through `std.testing.allocator`.
- `zig build test -Doptimize=ReleaseSafe`: the same behavior with
  optimizations and safety checks on.
- `zig build test --fuzz`: `std.testing.fuzz` cases; evidence for parsers
  and state machines, never proof.

## Source index

- [Zig Language Reference 0.16.0](https://ziglang.org/documentation/0.16.0/)
  — undefined behavior list, `undefined`, `errdefer`, pointers, casts.
- [Zig 0.16.0 release notes](https://ziglang.org/download/0.16.0/release-notes.html)
  — `std.Io`, `std.process.Init`, moved and removed APIs.
- [Zig standard library 0.16.0](https://ziglang.org/documentation/0.16.0/std/)
  — `std.testing`, `std.heap`, `std.Io`, `std.Build`.
- [Zig Build System guide](https://ziglang.org/learn/build-system/)
- `/usr/lib/zig/std` on the installed toolchain — the final word when the
  docs and the code disagree.
