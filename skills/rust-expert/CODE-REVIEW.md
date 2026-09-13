# Rust Code Review Directives

Rust-specific review scenarios: the code shape to avoid, the runtime or
compile-time sequence it creates, what can fail, and the evidence or
correction a reviewer should require.

The review method, scenario format, tracks, areas, technical levels,
advisories, and evidence labels are owned by the shared
[Code Review skill](../code-review/SKILL.md). This file adds Rust scenarios
only and never redefines those labels. Before judging version-sensitive code,
read `edition` and `rust-version` in `Cargo.toml` and the active toolchain
(`rust-toolchain.toml`, `rustc --version`).

Scenarios are grouped by [track](../code-review/SKILL.md#tracks). The track
describes the learning path, not the severity: a Foundations pattern can still
create a critical security or availability incident. A review comment must be
tied to the repository's contract or a credible failure mode.

The compiler removes whole classes of defects that a Go or C reviewer hunts by
hand (use after free, data races on plain memory, null dereference). Rust
review therefore concentrates on what the compiler cannot see: panics on
runtime input, runtime borrow checks, async lifecycle, `unsafe` invariants,
public-API contracts, and build-time trust.

## Worked example (full form)

```rust
async fn record(state: Arc<Mutex<Stats>>, client: &Client) -> Result<(), Error> {
    let mut stats = state.lock().unwrap();
    let body = client.get("/metrics").send().await?.text().await?;
    stats.ingest(&body);
    Ok(())
}
```

**Context:** `state` is a `std::sync::Mutex` shared between tasks on a
multi-threaded async runtime.

**Runtime sequence:** The guard is acquired, then the future suspends at
`.await` while still holding it. The runtime may park this task and schedule
another task on the same or another worker. Any task that now calls
`state.lock()` blocks its worker thread, not just its task.

**Failure modes:** Worker threads block on a lock owned by a parked task;
under enough contention every worker blocks and the runtime deadlocks. The
future is also `!Send` because `MutexGuard` is `!Send`, so `tokio::spawn`
rejects it at compile time and the author may "fix" that with an unsafe or a
single-threaded runtime assumption.

**Review directive:** Do not hold a `std::sync::MutexGuard` across an
`.await`. Require either an await-free critical section (fetch first, lock
after) or an async-aware lock when holding across the suspension point is
genuinely part of the design.

**Acceptable correction:** Move the network call before the lock, then lock
only to call `ingest`. Use `tokio::sync::Mutex` only when the critical section
must contain an `.await`. Add a test that runs two tasks concurrently against
the shared state under the multi-threaded runtime.

**Classification:** `BLOCKER` / `FIX-NOW` / `CONCURRENCY` / `TRACE`.

## Foundations: correctness

These are the first checks for almost every Rust implementation and review.

### 1. `unwrap` and `expect` on runtime input

**Problem:** `unwrap()`, `expect()`, or `panic!` is used where the value comes
from user input, the network, the filesystem, parsing, or an external process.

**What can happen:** A request or job crashes the thread or the process. On a
multi-threaded runtime one bad input aborts a whole worker; behind
`catch_unwind` boundaries the failure is hidden but state may be half-updated.

**Review questions:**

- Is the invariant local and documented (`expect("index checked above")`), or
  is it an external condition?
- Does the surrounding function already return `Result`? Then `?` is cheaper
  than a panic.

**Safer shape:** Return `Result` or `Option`; reserve `expect` for invariants
the code itself established, with the message stating the invariant.

### 2. Cloning to silence the borrow checker

**Problem:** `.clone()` or `.to_owned()` is added wherever the compiler
rejects a borrow, without deciding who owns the data.

**What can happen:** Allocation in hot paths, stale copies diverging from the
source, and an API whose ownership story nobody can explain. The code
compiles, which is why the smell survives review.

**Safer shape:** Decide whether the callee borrows, consumes, or shares. Pass
`&T` or `&mut T` for scoped access, move for transfer, `Rc`/`Arc` only when
shared ownership is the actual requirement. A clone whose lifetime purpose
cannot be stated is a design gap, not a fix.

### 3. Indexing with untrusted positions

**Problem:** `slice[i]`, `vec[i]`, `map[&key]`, or string slicing `s[a..b]` is
used with a value that comes from outside the function.

**What can happen:** Out-of-bounds indexing panics. String slicing on a
non-character boundary panics even when the index is in range, because
`str` indices are byte offsets.

**Safer shape:** Use `get`, `get_mut`, `chars()`, `char_indices()`, or
`is_char_boundary` and return an error on absence. Index only with positions
the function itself produced.

### 4. Silent numeric conversion and overflow

**Problem:** `as` casts between integer widths or signedness, arithmetic on
externally sized values, or float-to-int conversion without a range check.

**What can happen:** `as` truncates and wraps without error. Integer overflow
panics in debug builds and wraps in release builds unless the profile sets
`overflow-checks`, so a test that passes in debug can corrupt data in release.

**Safer shape:** Use `TryFrom`/`try_into` at boundaries and the explicit
`checked_*`, `wrapping_*`, or `saturating_*` families when wrapping or
saturation is the intended contract. Treat `as` as a statement that
truncation is acceptable.

### 5. Wildcard arms on your own enums

**Problem:** A `match` over an enum the crate owns uses `_ =>` to skip
variants, or an enum meant to grow is exposed without `#[non_exhaustive]`.

**What can happen:** A new variant compiles straight into the wildcard arm and
is silently mishandled. Conversely, adding a variant to a public exhaustive
enum is a breaking change for downstream crates.

**Safer shape:** List variants explicitly on enums you own so the compiler
reports every site that needs a decision. Mark public enums and structs that
may grow with `#[non_exhaustive]`.

### 6. Lazy iterators that never run

**Problem:** An iterator chain with side effects in `map`, `filter`, or
`inspect` is built but never consumed, or `collect()` is called without a
target type the compiler can infer.

**What can happen:** Nothing executes. The compiler warns through
`unused_must_use` only when the value is dropped immediately; an iterator
stored and forgotten produces no warning and no work.

**Safer shape:** Consume with `for`, `for_each`, `collect::<Vec<_>>()`, `sum`,
or similar. Keep side effects out of adapters; use adapters for transformation
and a terminal operation for effects.

### 7. `RefCell` as a default for mutation

**Problem:** `Rc<RefCell<T>>` or `RefCell<T>` is chosen because a `&mut`
borrow was inconvenient, not because shared mutation is the requirement.

**What can happen:** Borrow checking moves to runtime: a second `borrow_mut()`
while a `Ref` is alive panics with `already borrowed`. The failure appears
only on the code path that overlaps borrows, often under load or in a
callback.

**Safer shape:** Restructure ownership first (split the struct, pass `&mut`,
return new values). Use `RefCell` for genuine single-threaded shared mutation
and keep each borrow scoped to a statement. `RefCell` is `!Sync`; it cannot
migrate to threads later without a rewrite.

### 8. Comparison functions that are not a total order

**Problem:** `sort_by`, `sort_unstable_by`, `binary_search_by`, `max_by`, or a
manual `Ord` impl compares inconsistently: floats containing `NaN`,
`partial_cmp().unwrap()`, or `Ord` that disagrees with `PartialEq`.

**What can happen:** Since Rust 1.81 the standard sort implementations may
panic when the comparison is not a total order; before 1.81 they could return
a wrong order or loop. A manual `Ord` inconsistent with `Eq` breaks `BTreeMap`
and `binary_search` invariants silently.

**Safer shape:** Use `f64::total_cmp` for floats, derive `Ord` together with
`PartialOrd`, `Eq`, and `PartialEq`, and test the comparator with reversed and
duplicated inputs. Read the toolchain version before deciding whether the
failure is a panic or a wrong result.

### 9. Error types that erase the cause

**Problem:** A library returns `Box<dyn Error>`, `String`, or `anyhow::Error`
from its public API; or a `From` conversion (`?` with `#[from]`) collapses
several failure sources into one variant with no context.

**What can happen:** Callers cannot match on the failure and fall back to
string comparison. A retryable network error and a permanent parse error look
identical. The error message becomes an accidental API.

**Safer shape:** Libraries expose an enum error (often via `thiserror`) with
variants callers can act on and `source()` preserved. Applications may use
`anyhow` for propagation when the project accepts it. Never make callers
parse `Display` output.

### 10. `Drop` that must not fail

**Problem:** Cleanup with a result (flush, commit, close, unlock a remote
resource) is left to `Drop`, which cannot return an error.

**What can happen:** `BufWriter` drops silently discard flush errors, so a
"successful" write loses data. A transaction wrapper that commits in `Drop`
cannot report failure and may commit during a panic unwind.

**Safer shape:** Expose an explicit `flush()`, `commit()`, or `close(self)
-> Result<...>` and call it on the success path. Let `Drop` perform only
best-effort rollback or release. Document which one the type does.

## Boundaries: resources and lifecycle

These checks become important as code handles threads, async tasks, external
resources, or a public interface.

### 11. Guard held across `.await`

**Problem:** A `std::sync::MutexGuard`, `RwLockReadGuard`, `RefCell` borrow,
or other `!Send` guard is alive across an `.await` point.

**What can happen:** The future becomes `!Send` and cannot be spawned on a
multi-threaded runtime; if it is polled on a single thread, other tasks that
need the lock block the worker and the runtime can deadlock. See the worked
example above.

**Safer shape:** End the critical section before awaiting, or use an
async-aware lock when the suspension must happen while locked. Clippy's
`await_holding_lock` and `await_holding_refcell_ref` are evidence, not a
substitute for the ownership decision.

### 12. Blocking inside an async task

**Problem:** `std::fs`, `std::net`, `std::thread::sleep`, a CPU-heavy loop, or
a blocking client library runs directly inside an async function.

**What can happen:** The worker thread is occupied and every other task
assigned to it stalls. With a small worker pool, a few blocking calls freeze
the whole service while CPU usage stays low.

**Safer shape:** Use the runtime's async I/O and timers, or hand blocking
work to `spawn_blocking` or a dedicated thread. Measure task poll durations
when the runtime provides metrics.

### 13. Detached tasks and lost panics

**Problem:** `tokio::spawn` (or an equivalent) is called and the `JoinHandle`
is dropped or never awaited.

**What can happen:** Dropping a `JoinHandle` detaches the task; it keeps
running after the caller returned and past shutdown. A panic inside the task
is captured in the `JoinError` that nobody reads, so the failure disappears.
There is no structured parent-child lifetime unless the code builds one.

**Safer shape:** Keep the handle and await it, or use a `JoinSet` or
task-tracker so the owner can wait, cancel, and observe errors. Define what
shutdown does to in-flight tasks.

### 14. Unbounded queues and missing backpressure

**Problem:** `mpsc::unbounded_channel`, an unbounded `VecDeque`, or a growing
`Vec` of pending work is used between a fast producer and a slow consumer.

**What can happen:** Memory grows until the process is killed. Latency climbs
because the queue, not the work, dominates. The system looks healthy until
the first burst.

**Safer shape:** Bound the channel and decide what a full queue means:
await, drop, reject, or shed. Make the bound and the policy explicit in the
type or the constructor.

### 15. Channel ends that keep the pipeline alive or kill it

**Problem:** A `Sender` clone is stored somewhere long-lived, so the receiver
never observes closure; or a `Receiver` is dropped while producers still
`send`, and the `Err` from `send` is ignored.

**What can happen:** A shutdown loop `while let Some(msg) = rx.recv().await`
never ends because one forgotten `Sender` remains. In the other direction,
messages are silently discarded after the consumer is gone.

**Safer shape:** Track who owns each `Sender`; drop the last one deliberately
to signal completion. Handle `send` errors: they are the consumer telling the
producer to stop.

### 16. Cancellation safety in `select!`

**Problem:** A `select!` branch awaits a future that buffers partial state
(`read_exact`, `next_line`, a hand-written combinator) and another branch
completes first.

**What can happen:** The losing future is dropped mid-poll and its buffered
bytes or partially received message are lost. The next iteration starts from
a corrupted stream position.

**Safer shape:** Check the "Cancel safety" section of each awaited API. Keep
non-cancel-safe futures outside `select!` by pinning them once and polling
the same future across iterations, or restructure with a task and a channel.

### 17. Public API surface that cannot evolve

**Problem:** Public structs expose fields, enums are exhaustive, trait methods
are added to public traits, `impl Trait` return types change, or a dependency
type appears in the public signature.

**What can happen:** Any of these is a semver-breaking change for downstream
crates. A patch release breaks builds. Once published, the surface is a
contract.

**Safer shape:** Keep fields private with constructors and accessors, use
`#[non_exhaustive]`, seal traits that are not meant to be implemented
externally, and run `cargo semver-checks` when the crate is published.

### 18. Traits that are not dyn-compatible

**Problem:** A trait intended for `dyn Trait` has generic methods, methods
returning `Self`, associated consts, or `async fn` methods without `Self:
Sized` bounds.

**What can happen:** `Box<dyn Trait>` fails to compile far from the trait
definition, and the author reaches for boxing crates or duplicates the trait.
`async fn` in traits (stable since Rust 1.75) is not dyn-compatible without
boxing.

**Safer shape:** Decide up front whether the trait is for static dispatch or
dynamic dispatch. Put non-object-safe methods behind `where Self: Sized`, or
split the trait. For async, use `Pin<Box<dyn Future>>` returns or the
`async-trait` crate only when the project accepts it.

### 19. Environment mutation in tests

**Problem:** Tests call `std::env::set_var` or `remove_var`, or rely on
process-global state, while the test harness runs tests in parallel threads.

**What can happen:** Tests race on the environment and fail nondeterministically.
Under edition 2024 `set_var` and `remove_var` are `unsafe` because mutating the
environment while other threads read it is undefined behavior on many
platforms. Configuration read once at startup (`OnceLock`, lazy statics) does
not observe the change at all.

**Safer shape:** Pass configuration explicitly so tests do not touch the
environment. When the environment contract itself is under test, run the case
in a child process, serialize those tests, or use a process-level guard. Do
not reach for `unsafe { set_var(..) }` to keep a test green.

### 20. Wall clock and sleep in tests

**Problem:** Tests derive expectations from `SystemTime::now()`, compare
`Instant`s across runs, or synchronize with `thread::sleep` and
`tokio::time::sleep` instead of an observable event.

**What can happen:** `SystemTime` can move backwards (`duration_since` returns
`Err`), sleeps make tests slow and still flaky on loaded CI, and local
timezone assumptions leak in through formatting crates.

**Safer shape:** Inject a clock or pass timestamps explicitly, use `Instant`
only for elapsed time, and prefer the runtime's paused time
(`tokio::time::pause`, `start_paused`) for timer logic. Synchronize on
channels or join handles, not on sleep.

## Systems: contracts and performance

These require reasoning about `unsafe` invariants, the memory model, trust
boundaries, or measured runtime behavior.

### 21. `unsafe` without a stated invariant

**Problem:** An `unsafe` block or `unsafe fn` has no `// SAFETY:` comment, or
the comment restates the operation rather than the invariant that makes it
sound.

**What can happen:** The next edit breaks an invariant nobody wrote down.
Undefined behavior does not fail at the `unsafe` block; it surfaces later as
miscompilation, corruption, or a security hole.

**Safer shape:** Every `unsafe` site names the invariant and who guarantees
it. Keep the unsafe surface minimal and wrap it in the smallest safe API that
enforces the precondition. Enable
`clippy::undocumented_unsafe_blocks` when the project accepts it. Run Miri on
the unsafe paths.

### 22. Aliasing and validity violations through raw pointers

**Problem:** Two live `&mut` to the same memory are created through raw
pointers, a `&T` is turned into `&mut T`, uninitialized memory is read, or a
reference is produced to an invalid or unaligned location.

**What can happen:** Undefined behavior. The compiler assumes references are
valid, aligned, and non-aliasing for `&mut`, so the optimizer can delete or
reorder code in ways that only appear in release builds.

**Safer shape:** Use `MaybeUninit` for uninitialized data, `ptr::read` and
`ptr::write` for raw access, `addr_of!`/`addr_of_mut!` instead of taking a
reference to a possibly invalid place, and keep raw-pointer lifetimes
explicit. Miri with Stacked or Tree Borrows is the evidence tool.

### 23. `static mut` and global state

**Problem:** Mutable global state uses `static mut`, or a global is
initialized lazily without synchronization.

**What can happen:** Data races and aliasing violations. Edition 2024 turns
the `static_mut_refs` lint deny-by-default, so the code stops compiling
unless someone adds `#[allow]`; earlier editions only warn. Lazy
initialization without a guard runs twice or publishes partially built data.

**Safer shape:** Use `OnceLock`, `LazyLock`, `Mutex`, `RwLock`, or atomics.
Keep the initialization function idempotent and return errors explicitly
rather than panicking inside the initializer.

### 24. `transmute` and layout assumptions

**Problem:** `transmute`, pointer casts, or `from_raw_parts` assume the layout
of a `repr(Rust)` type, of an enum, or of a slice of a different element type.

**What can happen:** `repr(Rust)` layout is unspecified and may change between
compiler versions or with field reordering. Reading such memory as another
type is undefined behavior.

**Safer shape:** Use `repr(C)` or `repr(transparent)` where layout is a
contract, prefer safe conversions (`from_ne_bytes`, `bytemuck`-style checked
casts when accepted by the project), and document alignment and size
assumptions with `const` assertions.

### 25. Atomic orderings that do not publish

**Problem:** A flag or pointer is stored with `Ordering::Relaxed` while other
data written before it is expected to be visible to the reader, or acquire
and release sides are mismatched.

**What can happen:** The reader sees the flag but stale data. The bug depends
on the CPU architecture and rarely reproduces on x86, then appears on ARM.

**Safer shape:** Use `Release` on the publishing store and `Acquire` on the
consuming load, or `SeqCst` when the protocol is not clearly a pair. Document
the state machine. Prefer a `Mutex` when the invariant spans several fields.

### 26. Unsound `Send` and `Sync` impls

**Problem:** `unsafe impl Send` or `unsafe impl Sync` is written to make the
compiler accept a type containing raw pointers, `Rc`, `Cell`, or a foreign
handle.

**What can happen:** The type crosses threads without the guarantees the impl
claims, producing data races the borrow checker would have rejected.

**Safer shape:** Justify the impl from the invariants of the wrapped resource
(for example, the foreign library documents thread safety). Otherwise use
`Arc`, `Mutex`, atomics, or confine the value to one thread with channels.

### 27. Panics across the FFI boundary

**Problem:** An `extern "C"` function or a callback passed to foreign code can
panic, or foreign code is expected to unwind through Rust frames.

**What can happen:** Since Rust 1.81 a panic that reaches an `extern "C"`
boundary aborts the process; before that it was undefined behavior. Rust
1.71 only added the `-unwind` ABI variants. Foreign exceptions crossing Rust
frames are undefined behavior unless the `C-unwind` ABI is used on both
sides.

**Safer shape:** Wrap callback bodies in `catch_unwind` and convert panics to
error codes, declare `extern "C-unwind"` only when unwinding across the
boundary is the design, and treat all foreign pointers and lengths as
untrusted input.

### 28. Path joins and traversal

**Problem:** `Path::join` or `PathBuf::push` is used with a user-supplied
component to build a path under a base directory.

**What can happen:** Joining an absolute path replaces the base entirely, and
`..` components escape it. `Path::new("/srv/data").join("/etc/passwd")` is
`/etc/passwd`.

**Safer shape:** Reject absolute paths and parent components, canonicalize
both sides and check the prefix, or map user input to an allowlisted name.
Treat file names from archives and uploads as hostile.

### 29. Deserializing untrusted input without limits

**Problem:** `serde` deserialization, decompression, or a hand-written parser
runs on untrusted bytes with no size, depth, or count limits.

**What can happen:** Memory exhaustion from declared lengths, stack exhaustion
from deep nesting, or CPU exhaustion from decompression bombs. Rust prevents
memory corruption here, not denial of service.

**Safer shape:** Cap input size before parsing, use readers with limits
(`take`), keep the format's recursion limit enabled, and validate lengths
before allocating. Fuzz parsers with `cargo fuzz` when they face the network.

### 30. Build-time code execution in dependencies

**Problem:** A new dependency ships a `build.rs`, a proc macro, or native
code, and is added without inspection; `Cargo.lock` is not committed for a
binary; or a crate is pulled from a git URL without a pinned revision.

**What can happen:** Arbitrary code runs on every developer and CI machine at
build time. A compromised or typosquatted crate becomes a supply-chain
incident before the first test runs.

**Safer shape:** Inspect maintenance, provenance, and build-time behavior
before adding a crate. Commit `Cargo.lock` for binaries, pin git
dependencies by `rev`, and run `cargo audit` or `cargo deny` when the project
adopts them. A clean audit is evidence, not proof.

### 31. Allocation in hot paths without measurement

**Problem:** `to_string()`, `format!`, `collect()` intermediates, or `clone()`
run inside a loop; a `Vec` grows without `with_capacity`; or `#[inline]` and
`Box` decisions are made by taste.

**What can happen:** Throughput and latency regress with no failing test. Or,
in the other direction, an "optimization" that changes ownership makes the
code harder to read for no measured gain.

**Safer shape:** Profile first (`perf`, `flamegraph`, `criterion`), then
change the allocation pattern that the profile names. Keep benchmarks
representative and report allocations alongside time.

### 32. Feature flags that are not additive

**Problem:** Cargo features toggle mutually exclusive backends, change public
types, or remove items, and CI tests only the default set.

**What can happen:** Feature unification across the dependency graph enables
two "exclusive" features at once and the crate fails to build or misbehaves
in a downstream workspace. Combinations nobody tested ship to users.

**Safer shape:** Keep features additive; select backends at runtime or
through separate crates. Test the documented feature sets explicitly rather
than blindly using `--all-features`.

## Cross-cutting directives

### Process-isolated tests for initialization-time environment

**Avoid:** Mutating the environment in the parent test process to exercise
startup behavior that reads it once, or relying on test ordering to keep
those tests apart.

**Context:** The default harness runs tests on multiple threads. Under
edition 2024 `std::env::set_var` is `unsafe` for that reason. Values captured
in `OnceLock`, `LazyLock`, or a `main`-time config struct never change after
first read.

**Runtime sequence:** The parent test spawns the current test binary
(`std::env::current_exe()`) with `std::process::Command`, sets a guard
variable and the case-specific environment, and filters to the helper test by
name with `--exact`. The child starts fresh, runs initialization, prints the
observed value, and exits; the parent asserts on captured stdout or the exit
status.

**Failure modes:** A false pass because the parent already cached the old
value, a nondeterministic failure when two tests mutate the same variable, or
unbounded recursion when the guard is missing.

**Review directive:** Require a dedicated guard variable, `current_exe()`
rather than `args[0]`, a direct `Command` invocation with no shell, an exact
test filter, an explicit child environment, and assertions on the first line
of output rather than the whole harness output (the child prints its own test
summary after the helper returns). When the environment is not part of the
contract, pass configuration explicitly instead.

**Classification:** Usually `WARNING` / `FIX-OR-TECH-DEBT` / `TEST` /
`REPRODUCED`. Promote to `BLOCKER` when the test guards an authentication,
expiration, or merge-gate contract.

## Automated review baseline

The verification commands are defined once in
[`SKILL.md`](SKILL.md#-formatting-and-verification). Repository-configured
gates always take precedence.

Evidence scope for the tools named there:

- `cargo clippy`: lints for many scenarios above (`await_holding_lock`,
  `unwrap_used` when enabled, `undocumented_unsafe_blocks` when enabled).
  A clean run is evidence, not proof.
- `cargo test`: behavior verification including doctests.
- `cargo miri test`: evidence for undefined behavior on exercised unsafe
  paths; not a proof of soundness.
- `cargo audit` and `cargo deny`: dependency advisories and policy.
- `cargo semver-checks`: public API compatibility for published crates.

## Source index

- [The Rust Programming Language](https://doc.rust-lang.org/book/) —
  ownership, error handling, iterators, concurrency foundations.
- [The Rust Reference](https://doc.rust-lang.org/reference/) — language
  semantics, `unsafe`, type layout, behavior considered undefined.
- [The Rustonomicon](https://doc.rust-lang.org/nomicon/) — unsafe Rust,
  aliasing, FFI, atomics.
- [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/) — naming,
  interoperability, future proofing, semver.
- [Cargo Book: SemVer compatibility](https://doc.rust-lang.org/cargo/reference/semver.html)
  — what counts as a breaking change.
- [Cargo Book: features](https://doc.rust-lang.org/cargo/reference/features.html)
  — feature unification and additivity.
- [Rust 2024 edition guide](https://doc.rust-lang.org/edition-guide/rust-2024/)
  — `static mut` references, unsafe `set_var`, temporaries, `impl Trait`
  captures.
- [Rust 1.71 release notes](https://blog.rust-lang.org/2023/07/13/Rust-1.71.0/)
  — `C-unwind` and other `-unwind` ABIs stabilized; plain `"C"` unchanged.
- [Rust 1.81 release notes](https://blog.rust-lang.org/2024/09/05/Rust-1.81.0/)
  — non-unwind ABIs abort on uncaught unwinds; sort implementations may
  panic on non-total orders.
- [`std::io::BufWriter`](https://doc.rust-lang.org/std/io/struct.BufWriter.html)
  — flush errors are ignored on drop.
- [`std::path::Path::join`](https://doc.rust-lang.org/std/path/struct.Path.html#method.join)
  — an absolute argument replaces the base.
- [`std::env::set_var`](https://doc.rust-lang.org/std/env/fn.set_var.html) —
  safety contract for environment mutation.
- [tokio `Mutex`](https://docs.rs/tokio/latest/tokio/sync/struct.Mutex.html)
  and [tokio `select!`](https://docs.rs/tokio/latest/tokio/macro.select.html)
  — guard across await, cancellation safety.
- [tokio `JoinHandle`](https://docs.rs/tokio/latest/tokio/task/struct.JoinHandle.html)
  — dropping a handle detaches the task.
- [Clippy lint index](https://rust-lang.github.io/rust-clippy/master/) —
  `await_holding_lock`, `unwrap_used`, `undocumented_unsafe_blocks`.
- [Miri](https://github.com/rust-lang/miri) — undefined-behavior detection
  for unsafe code.
