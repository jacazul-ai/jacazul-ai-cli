# Rust Engineering Playbook

Implementation guidance for writing natural, safe, and sustainable Rust:
ownership that reads, errors callers can match on, types that make invalid
states unrepresentable, async and unsafe with explicit contracts. This
file answers **how to build the change**. Scenario-based review directives
live separately in [`CODE-REVIEW.md`](CODE-REVIEW.md).

Verified on **rustc 1.97.1**, edition 2024: every example below lives in
[`examples/`](examples/) and compiled, ran, and passed `clippy -D warnings`
on that toolchain (`tests/test_rust_examples.py` reruns them).
Version-sensitive claims name the release that introduced them.

These are defaults, not automatic repository policy. Read `Cargo.toml`
(`edition`, `rust-version`, features, `[lints]`), `rust-toolchain.toml`,
CI, and the workspace layout before adopting an optional gate or changing
an established contract.

## Before writing code

1. Read the edition, the MSRV (`rust-version`), and the toolchain the
   project pins. Never use syntax or APIs above the MSRV.
2. Read the target crate, its public API, and its tests before introducing
   an abstraction.
3. Define the contract: ownership of every argument and return value
   (borrow, move, shared), the error type callers will match on, panics
   the function may raise, cancellation and shutdown for async code.
4. Identify trust boundaries: deserialization, FFI, `unsafe`, file and
   network input, build scripts of dependencies.
5. Decide who owns every task, lock, and resource, and where it is dropped.

## Project shape

- One binary or library per crate; a workspace when crates share a
  version and a lockfile; `[workspace.dependencies]` to declare versions
  once.
- `edition` and `rust-version` declared; `rust-toolchain.toml` when the
  project pins a channel; `Cargo.lock` committed for binaries and
  applications, and for libraries too when reproducible CI matters.
- Features are additive; exclusive backends are separate crates or
  runtime choices; `--all-features` only when the feature graph is
  compatible.
- `[lints]` in `Cargo.toml` (Rust 1.74+) is the decision log for Clippy
  opinions: `warn` first, `deny` in a dedicated commit that records why.
- `src/lib.rs` holds the API, `src/main.rs` a thin CLI over it; `examples/`
  compile in CI; `benches/` when performance is a contract.

## Ownership and borrowing

Transfer ownership when the callee must retain responsibility; borrow for
scoped access; clone on purpose, never to silence the borrow checker.

```rust
//! Ownership: borrow for scoped access, move for transfer, clone on purpose.

/// Borrows the list; the caller keeps ownership.
fn longest(words: &[String]) -> Option<&str> {
    words.iter().map(String::as_str).max_by_key(|w| w.len())
}

/// Consumes the list and returns owned data the caller now owns.
fn into_upper(words: Vec<String>) -> Vec<String> {
    words.into_iter().map(|w| w.to_uppercase()).collect()
}

fn main() {
    let words = vec!["zig".to_string(), "rust".to_string()];
    let best = longest(&words).map(str::to_owned);
    let shouted = into_upper(words); // `words` is moved here
    assert_eq!(best.as_deref(), Some("rust"));
    assert_eq!(shouted, ["ZIG", "RUST"]);
    println!("ok");
}
```

- Introduce explicit lifetimes only when a relationship must be
  expressed; most functions infer them.
- Before choosing `Rc`, `Arc`, `RefCell`, or `Mutex`, name the ownership
  problem and the runtime cost they solve; `RefCell` moves borrow checks
  to runtime and is `!Sync`.
- Make ownership and invalidation visible in public APIs: `&T` borrows,
  `T` moves, `Cow` when either is fine, `impl Iterator` to lend results
  without allocating.
- The usual invariant is many shared borrows or one mutable borrow;
  interior mutability is a documented exception, not a default.

## API and type design

Prefer enums for finite state and newtypes for identifiers and units.
Invalid combinations should not compile.

```rust
//! Newtypes and enums make invalid states unrepresentable.

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct Cents(u64);

#[derive(Debug, PartialEq, Eq)]
enum Payment {
    Pending,
    Captured { amount: Cents },
    Refunded { amount: Cents, reason: String },
}

fn total_captured(payments: &[Payment]) -> Cents {
    let sum = payments
        .iter()
        .map(|p| match p {
            Payment::Captured { amount } => amount.0,
            Payment::Pending | Payment::Refunded { .. } => 0,
        })
        .sum();
    Cents(sum)
}

fn main() {
    let payments = [
        Payment::Pending,
        Payment::Captured { amount: Cents(250) },
        Payment::Refunded { amount: Cents(100), reason: "duplicate".into() },
        Payment::Captured { amount: Cents(50) },
    ];
    assert_eq!(total_captured(&payments), Cents(300));
    println!("ok");
}
```

- Keep traits close to their consumers and name them by capability.
- Generics for static dispatch; `dyn Trait` when runtime polymorphism is
  intentional and the trait is dyn-compatible (no generic methods, no
  `Self` returns, no `async fn` without boxing).
- Keep the public surface small; `#[non_exhaustive]` on enums and structs
  that may grow; private fields with constructors and accessors.
- Avoid wrappers, managers, helpers, and macros that add no behavior.
- Public items, errors, and wire formats are contracts once consumers
  depend on them; `cargo semver-checks` when the crate is published.

## Legible control flow

Keep the happy path visible and failures early. Rust's tools are `?`,
`let else` (Rust 1.65+), `match`, and a final successful expression.

```rust
//! Legible control flow: `?`, `let else`, and a final successful expression.

use std::collections::HashMap;

#[derive(Debug, PartialEq)]
enum RunError {
    MissingKey(&'static str),
    BadValue(std::num::ParseIntError),
}

impl From<std::num::ParseIntError> for RunError {
    fn from(e: std::num::ParseIntError) -> Self {
        RunError::BadValue(e)
    }
}

fn workers(config: &HashMap<&str, &str>) -> Result<usize, RunError> {
    let Some(raw) = config.get("workers") else {
        return Err(RunError::MissingKey("workers"));
    };
    let n: usize = raw.parse()?;
    Ok(n.clamp(1, 64))
}

fn main() {
    let mut config = HashMap::new();
    assert_eq!(workers(&config), Err(RunError::MissingKey("workers")));
    config.insert("workers", "x");
    assert!(matches!(workers(&config), Err(RunError::BadValue(_))));
    config.insert("workers", "200");
    assert_eq!(workers(&config), Ok(64));
    println!("ok");
}
```

Review `?` chains for the error type they produce and the context they
lose; a short function is not automatically a clear one.

## Naming and conversions

Follow the Rust API Guidelines: `snake_case` functions and modules,
`UpperCamelCase` types and traits, `SCREAMING_SNAKE_CASE` constants;
`as_` for cheap borrowed views, `to_` for owned or expensive conversions,
`into_` for consuming conversions; `iter`, `iter_mut`, `into_iter`; no
`get_` prefix on plain getters. Reference:
https://rust-lang.github.io/api-guidelines/naming.html

## Errors and panics

`Result<T, E>` for recoverable failure, `Option<T>` for absence, an enum
error callers can match on, the source preserved.

```rust
//! Errors: an enum the caller can match on, with the cause preserved.

use std::fmt;
use std::num::ParseIntError;

#[derive(Debug)]
enum PortError {
    Empty,
    NotANumber(ParseIntError),
    OutOfRange(u32),
}

impl fmt::Display for PortError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            PortError::Empty => write!(f, "port is empty"),
            PortError::NotANumber(e) => write!(f, "port is not a number: {e}"),
            PortError::OutOfRange(n) => write!(f, "port {n} is out of range"),
        }
    }
}

impl std::error::Error for PortError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            PortError::NotANumber(e) => Some(e),
            _ => None,
        }
    }
}

fn parse_port(text: &str) -> Result<u16, PortError> {
    if text.is_empty() {
        return Err(PortError::Empty);
    }
    let n: u32 = text.parse().map_err(PortError::NotANumber)?;
    u16::try_from(n).map_err(|_| PortError::OutOfRange(n))
}

fn main() {
    assert_eq!(parse_port("8080").unwrap(), 8080);
    assert!(matches!(parse_port(""), Err(PortError::Empty)));
    assert!(matches!(parse_port("http"), Err(PortError::NotANumber(_))));
    assert!(matches!(parse_port("70000"), Err(PortError::OutOfRange(70000))));
    println!("ok");
}
```

- Libraries expose an enum (often via `thiserror`); applications may use
  `anyhow` for propagation when the project accepts it. Never make callers
  compare error strings.
- `unwrap` and `expect` only on invariants the code established, with the
  message stating the invariant; never on input.
- Panic behavior is an API decision: document `# Panics`; keep panics out
  of FFI and `Drop`.
- Cleanup that can fail (`flush`, `commit`, `close`) is an explicit method
  called on the success path; `Drop` is best effort and silent.

## Async and concurrency

Every spawned task needs an owner, an exit path, a cancellation strategy,
error observation, and a shutdown contract. For threads, scoped threads
(Rust 1.63+) make the owner explicit and let tasks borrow.

```rust
//! Scoped threads: borrow the data, every thread joined before return.

use std::sync::Mutex;
use std::thread;

fn squares(input: &[u64]) -> Vec<u64> {
    let out = Mutex::new(vec![0; input.len()]);
    thread::scope(|s| {
        for (i, n) in input.iter().enumerate() {
            let out = &out;
            s.spawn(move || {
                let value = n * n;
                out.lock().unwrap()[i] = value;
            });
        }
    });
    out.into_inner().unwrap()
}

fn main() {
    assert_eq!(squares(&[0, 1, 2, 3]), [0, 1, 4, 9]);
    println!("ok");
}
```

- Async: keep a `JoinHandle` or use a `JoinSet`; a dropped handle detaches
  the task and loses its panic.
- Never hold a `std::sync::MutexGuard` across `.await`; end the critical
  section first or use an async-aware lock when the design needs it.
- No blocking calls on a runtime worker: `spawn_blocking` or a dedicated
  thread.
- Bound every channel and decide what a full queue means; drop the last
  `Sender` deliberately to end a receiver loop; handle `send` errors.
- Check the cancellation-safety notes of every future used inside
  `select!`.
- Shared ownership, channels, locks, and atomics only when the behavior
  requires them; prefer bounded, structured concurrency.

## Unsafe Rust and FFI

Every `unsafe` block is a security and correctness boundary.

- Minimize and isolate unsafe code behind the smallest safe API that
  upholds the invariant; a `// SAFETY:` comment names the invariant and
  who guarantees it.
- Review validity, initialization (`MaybeUninit`), alignment, aliasing
  (`&mut` uniqueness), lifetimes, thread safety (`Send`/`Sync` impls),
  panic behavior, and layout (`repr(C)` when it is a contract).
- FFI inputs, callbacks, and foreign ownership are untrusted boundaries;
  panics do not cross `extern "C"` (abort since Rust 1.81; use `C-unwind`
  only when unwinding across is the design).
- Miri, sanitizers, and fuzzing where the code touches unsafe or parses
  input.

Reference: https://doc.rust-lang.org/nomicon/

## Performance and dependencies

Measure before optimizing: allocations, cloning, data layout, lock
contention, serialization, and profiles (`perf`, `flamegraph`, `criterion`).
Claims require benchmarks on the shipped profile.

Before recommending a crate, inspect maintenance, adoption, license,
provenance, transitive cost, feature flags, build scripts, proc macros, and
native code. Standard library first; popular crates are references, not
automatic dependencies. Never expose credentials through Cargo commands,
logs, caches, artifacts, or examples.

## Rustdoc and generated code

- Public documentation starts with a standalone summary sentence;
  `# Errors`, `# Panics`, and `# Safety` where applicable; intra-doc links
  ``[`Type`]``; `# Examples` are doctests run by `cargo test`.
- Inspect rendered output with `cargo doc --workspace --no-deps`.
- Generated Rust (bindgen, prost, build scripts) is not edited by hand;
  change the source and regenerate.

## Tests and validation

Write tests around the contract, not only the happy path:

- invalid input, returned errors, and panics documented as such;
- cancellation, timeout, and shutdown of tasks;
- ownership and aliasing behavior at API boundaries;
- serialized wire forms and feature combinations the project documents;
- `unsafe` paths under Miri when present.

### Process-isolated tests for environment

`std::env::set_var` is `unsafe` under edition 2024 and racy under the
multi-threaded test harness. When the environment is the contract, spawn
the test binary again with `std::env::current_exe()`, a guard variable,
`--exact`, an explicit environment, and read the first line of stdout;
otherwise pass configuration explicitly and test the pure function.

Run repository-configured checks first. If no stronger gate exists, use
the baseline from [`SKILL.md`](SKILL.md#-formatting-and-verification) and
label it as such.

## Updating a project to a newer edition or toolchain

An update is a migration with two pins: the source (current `edition`
and `rust-version`) and the target. One commit per step, suite green
after each:

1. Toolchain bump in `rust-toolchain.toml` or CI; `cargo build` and
   `cargo clippy` with the new release; the warnings are the list.
2. `cargo fix --edition` on a clean tree; review the diff (the 2024
   edition changes `impl Trait` captures, `static mut` references, unsafe
   `extern` blocks and attributes, `if let` and tail temporaries, and
   makes `set_var` unsafe); commit the mechanical result alone.
3. Bump `edition` in `Cargo.toml`; build; fix what the automatic pass
   could not.
4. Raise `rust-version` only when a used feature requires it; record why
   in the commit.
5. Dependency updates one family per commit (`cargo update -p`), audit
   after each (`cargo audit` or `cargo deny` when adopted).
6. `[lints]` review: promote experiments that earned it, drop the noise.

A step that changes behavior is a bug, not a step. Revert it and add the
test that would have caught it.

## Version awareness

| Release | What it changed |
|---|---|
| 1.63 | Scoped threads (`std::thread::scope`) |
| 1.65 | `let else`, generic associated types |
| 1.70 | `OnceLock`, `LazyLock` (1.80) for lazy statics |
| 1.71 | `-unwind` ABIs stabilized; plain `"C"` unchanged |
| 1.74 | `[lints]` table in `Cargo.toml` |
| 1.75 | `async fn` and `impl Trait` in traits (not dyn-compatible) |
| 1.79 | Inline `const`, `use<..>` precise capturing (1.82) |
| 1.81 | Panics reaching `extern "C"` abort; sorts may panic on non-total orders; `#[expect]` |
| 1.85 | Edition 2024: RPIT captures all lifetimes, `static_mut_refs` deny, unsafe `extern`, unsafe `no_mangle`, unsafe `set_var`, earlier drop of `if let` and tail temporaries |

Read the release notes and the edition guide of the project's pinned
version before trusting a name:
https://doc.rust-lang.org/edition-guide/ and
https://github.com/rust-lang/rust/blob/master/RELEASES.md

## References

- [The Rust Programming Language](https://doc.rust-lang.org/book/)
- [The Rust Reference](https://doc.rust-lang.org/reference/)
- [The Rustonomicon](https://doc.rust-lang.org/nomicon/)
- [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)
- [The Cargo Book](https://doc.rust-lang.org/cargo/)
- [Edition Guide](https://doc.rust-lang.org/edition-guide/)
- [Rust Code Review Directives](CODE-REVIEW.md)
