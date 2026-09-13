# Zig Engineering Playbook

Implementation guidance for writing explicit, allocator-honest, safety-aware
Zig. This file answers **how to build the change**. Scenario-based review
directives live separately in [`CODE-REVIEW.md`](CODE-REVIEW.md).

Verified on **Zig 0.16.0**. Zig is pre-1.0 and the standard library moves
between minors; every example below compiled and passed under `zig test`
on 0.16.0. When the project pins another release, read its release notes
before trusting a name in this file. Version-sensitive claims are marked.

These are defaults, not automatic repository policy. Read `build.zig`,
`build.zig.zon`, `.minimum_zig_version`, CI, and the package layout before
adopting an optional gate or changing an established contract.

## Before writing code

1. Run `zig version` and read `.minimum_zig_version` in `build.zig.zon`.
   Never use an API above the project's floor.
2. Read `build.zig`: modules, executables, tests, the `run` and `test`
   steps, linked system libraries, and translate-c steps.
3. Read the target module and its `test` blocks before introducing an
   abstraction.
4. Define the contract: who allocates, who frees, with which allocator;
   which error set; what happens on partial failure; which optimize mode
   the code must be correct in (all of them).
5. Identify trust boundaries: C interop, bytes from the network or files,
   command line arguments, environment, and dependencies in
   `build.zig.zon`.

## Toolchain and build

- `zig init` generates the canonical skeleton for the installed release:
  `build.zig`, `build.zig.zon`, `src/main.zig`, `src/root.zig`. Diff a
  project's build against it when in doubt.
- `build.zig.zon` (0.14+ shape, verified on 0.16): `.name` is an enum
  literal, `.fingerprint` is generated once and never changes (forks
  regenerate it), `.minimum_zig_version` declares the floor,
  `.dependencies` entries carry `url` + `hash` or `path` (and `.lazy`),
  `.paths` lists what is part of the package and its hash.
- `std.Build` (0.16): an executable takes a root module,
  `b.addExecutable(.{ .name = "app", .root_module = b.createModule(.{
  .root_source_file = b.path("src/main.zig"), .target = target,
  .optimize = optimize, .imports = &.{ ... } }) })`; a test executable is
  `b.addTest(.{ .root_module = mod })`; `b.addModule` exposes a module to
  consumers, `b.createModule` keeps it private.
- Optimize modes: `Debug`, `ReleaseSafe`, `ReleaseFast`, `ReleaseSmall`.
  Code must be correct in all four; safety checks exist only in the first
  two (see the safety section).
- Cross-compilation is built in: `-Dtarget=aarch64-linux-musl` and friends
  through `b.standardTargetOptions`.
- `zig fmt` is the only formatter and has no options; `zig build test`
  runs every test step; `zig build test --fuzz` runs `std.testing.fuzz`
  cases (0.16).
- C interop: `@cImport` is deprecated in 0.16 in favor of translate-c run
  by the build system (`b.addTranslateC`), and still compiles. New code
  uses the build step; legacy code keeps `@cImport` until a migration
  step replaces it.

## Allocators and ownership

Every allocation names its allocator; nothing allocates behind the
caller's back. The contract of a function that allocates says who frees.

```zig
const std = @import("std");
const Allocator = std.mem.Allocator;

/// Caller owns the returned slice and frees it with the same allocator.
pub fn joinWords(gpa: Allocator, words: []const []const u8) Allocator.Error![]u8 {
    var out: std.ArrayList(u8) = .empty;
    errdefer out.deinit(gpa);

    for (words, 0..) |word, i| {
        if (i != 0) try out.append(gpa, ' ');
        try out.appendSlice(gpa, word);
    }
    return out.toOwnedSlice(gpa);
}

test "joinWords returns an owned slice" {
    const gpa = std.testing.allocator;
    const joined = try joinWords(gpa, &.{ "zig", "0.16" });
    defer gpa.free(joined);
    try std.testing.expectEqualStrings("zig 0.16", joined);
}

test "joinWords releases partial work on failure" {
    try std.testing.checkAllAllocationFailures(
        std.testing.allocator,
        struct {
            fn run(gpa: Allocator) !void {
                const joined = try joinWords(gpa, &.{ "a", "b", "c" });
                defer gpa.free(joined);
            }
        }.run,
        .{},
    );
}
```

- `std.ArrayList(T)` is unmanaged (0.15+, verified 0.16): it starts as
  `.empty`, and `append`, `appendSlice`, `deinit`, `toOwnedSlice` take the
  allocator. `ArrayListUnmanaged` is an alias of the same type.
- `defer` releases on every exit; `errdefer` releases only when the block
  exits with an error. Pair each allocation with one of them on the line
  after it, and use `errdefer` for resources that are handed to the caller
  on success.
- Choosing an allocator (0.16 names): `std.heap.DebugAllocator` for
  development and tests (leak and double-free detection;
  `GeneralPurposeAllocator` no longer exists), `std.heap.smp_allocator` for
  release multi-threaded programs, `std.heap.page_allocator` for large
  page-granular buffers, `std.heap.c_allocator` when linking libc,
  `std.heap.ArenaAllocator` for many small allocations with one lifetime
  (thread safe and lock free in 0.16), `std.heap.FixedBufferAllocator` for
  stack or static buffers. `ThreadSafeAllocator` was removed in 0.16.
- `main(init: std.process.Init)` (0.16) already provides `init.gpa` (a
  general-purpose allocator with leak checking in Debug), `init.arena`
  (process-lifetime arena), `init.io`, `init.minimal.args`, and
  `init.environ_map`. Use them instead of building your own at startup.
- `std.testing.allocator` reports leaks and makes `zig test` exit 1
  (verified). Every test that allocates runs under it.
- `std.testing.checkAllAllocationFailures` (0.16) injects a failure at
  every allocation site in turn; use it on functions with more than one
  allocation to prove `errdefer` coverage.

## Errors and failure contracts

Errors are values from an error set; the error set is part of the
signature and the compiler merges inferred sets for you when you write
`!T`.

```zig
const std = @import("std");

const ParseError = error{ Empty, NotANumber };

fn parsePort(text: []const u8) ParseError!u16 {
    if (text.len == 0) return error.Empty;
    return std.fmt.parseInt(u16, text, 10) catch error.NotANumber;
}

test "error sets are part of the contract" {
    try std.testing.expectEqual(@as(u16, 8080), try parsePort("8080"));
    try std.testing.expectError(error.Empty, parsePort(""));
    try std.testing.expectError(error.NotANumber, parsePort("http"));
}
```

- Name explicit error sets on public functions; inferred `!T` is fine for
  private helpers.
- `try` propagates, `catch` handles, `catch unreachable` asserts an
  invariant and is undefined behavior in ReleaseFast if it fires.
- `errdefer` runs cleanup only on the error path; `errdefer |err|` captures
  the error for logging.
- Error return traces are automatic in Debug and ReleaseSafe when an error
  reaches `main`; keep them by returning errors rather than converting them
  to booleans or optionals.
- `unreachable` states an invariant, never an expected input. Reaching it
  is safety-checked in Debug and ReleaseSafe and undefined in ReleaseFast.

## Comptime and generics

A generic is a function that runs at compile time and returns a type.

```zig
const std = @import("std");

/// A generic is a function that returns a type.
fn Ring(comptime T: type, comptime capacity: usize) type {
    return struct {
        items: [capacity]T = undefined,
        head: usize = 0,
        len: usize = 0,

        const Self = @This();

        pub fn push(self: *Self, value: T) error{Full}!void {
            if (self.len == capacity) return error.Full;
            self.items[(self.head + self.len) % capacity] = value;
            self.len += 1;
        }

        pub fn pop(self: *Self) ?T {
            if (self.len == 0) return null;
            const value = self.items[self.head];
            self.head = (self.head + 1) % capacity;
            self.len -= 1;
            return value;
        }
    };
}

test "comptime parameters build a concrete type" {
    var ring: Ring(u8, 2) = .{};
    try ring.push(1);
    try ring.push(2);
    try std.testing.expectError(error.Full, ring.push(3));
    try std.testing.expectEqual(@as(?u8, 1), ring.pop());
}
```

- `comptime` parameters, `inline for`/`inline while`, and `@TypeOf` cover
  most generic needs; reach for the type-construction builtins (`@Int`,
  `@Struct`, `@Union`, `@Enum`, `@Pointer`, `@Fn`, `@Tuple`, which
  replaced `@Type` in 0.16) only when a type must be synthesized.
- Ask whether comptime buys behavior (a size known at compile time, a
  table computed once) or only ceremony. A runtime parameter is simpler
  when the value is not needed at compile time.
- Decl literals (0.14+): `.empty`, `.init`, `.zero` refer to declarations
  of the expected type; use them for constructors instead of repeating the
  type name.

## Safety modes and undefined behavior

The language reference (0.16.0) lists behaviors that are safety-checked
(panic) in Debug and ReleaseSafe and undefined in ReleaseFast and
ReleaseSmall: reaching unreachable code, index out of bounds, casting a
negative number to unsigned, cast truncation, integer overflow, exact shift
overflow, division by zero, remainder division by zero, exact division
remainder, unwrapping null, unwrapping an error, invalid error codes,
invalid enum cast, invalid error set cast, incorrect pointer alignment,
wrong union field access, out-of-bounds float-to-integer cast, and pointer
cast with invalid null.

Verified on 0.16.0: `u8` overflow panics with `integer overflow` under
`-OReleaseSafe` and wraps silently under `-OReleaseFast`.

- Tests run in Debug by default; run the suite under `-Doptimize=ReleaseSafe`
  too when the code is shipped that way, and know that ReleaseFast removes
  the net.
- `undefined` means any value; Debug and ReleaseSafe fill it with `0xaa`
  as an implementation detail, not a guarantee. Never read a variable
  initialized to `undefined` before writing it.
- Use the explicit operators when wrapping or saturation is the contract:
  `+%`, `-%`, `*%` wrap; `+|`, `-|`, `*|` saturate; `@addWithOverflow` and
  friends report.
- `@intCast`, `@truncate`, `@intFromFloat`, `@enumFromInt`,
  `@errorCast`, `@alignCast`: each is a claim the value fits. Validate
  before casting external values; the safety check is not present in
  ReleaseFast.
- `@setRuntimeSafety(false)` is a local, documented decision for a measured
  hot path, never a default.

## Pointers, slices, and sentinels

- `*T` single item, `*[N]T` pointer to an array, `[]T` slice (pointer plus
  length), `[*]T` many-item pointer without length, `[*:0]T`
  sentinel-terminated pointer, `[:0]T` sentinel-terminated slice, `[*c]T`
  C pointer (nullable, arithmetic allowed; only at C boundaries).
- Prefer slices everywhere in Zig code; convert `[*:0]const u8` from C to
  `[:0]const u8` with `std.mem.span` at the boundary.
- `@ptrCast` creates a pointer that can cause undetectable illegal behavior
  depending on the loads and stores through it; `@alignCast` inserts a
  safety check. Isolate both behind a small function with a comment that
  states the layout invariant.
- Optionals model absence: `?*T` is a nullable pointer with no overhead;
  `orelse` and `if (x) |v|` unwrap. Do not use sentinel values where an
  optional says it.

## Io, concurrency, and lifecycle (0.16)

Starting with 0.16, all input and output goes through an `std.Io` instance;
`main` receives one in `init.io`, tests use `std.testing.io`.
Implementations: `Io.Threaded` (complete), `Io.Evented` (experimental,
fiber based), `Io.Uring` (proof of concept), `Io.Dispatch`, `Io.Kqueue`.
Language-level `async`/`await` keywords do not exist; concurrency is an
`Io` feature.

Inject writers instead of printing to globals:

```zig
const std = @import("std");
const Io = std.Io;

/// Accept an *Io.Writer so the caller decides where output goes.
fn report(w: *Io.Writer, name: []const u8, count: usize) Io.Writer.Error!void {
    try w.print("{s}: {d}\n", .{ name, count });
}

test "writers are injected, not global" {
    var buffer: [64]u8 = undefined;
    var fixed: Io.Writer = .fixed(&buffer);
    try report(&fixed, "items", 3);
    try std.testing.expectEqualStrings("items: 3\n", fixed.buffered());
}

test "reading a file goes through Io" {
    const io = std.testing.io;
    const gpa = std.testing.allocator;
    var tmp = std.testing.tmpDir(.{});
    defer tmp.cleanup();
    try tmp.dir.writeFile(io, .{ .sub_path = "hello.txt", .data = "hi\n" });
    const bytes = try tmp.dir.readFileAlloc(io, "hello.txt", gpa, .limited(1024));
    defer gpa.free(bytes);
    try std.testing.expectEqualStrings("hi\n", bytes);
}
```

Tasks have an owner: a `Group` when many tasks share a lifetime, a
`Future` for one, a `Batch` for operation-level concurrency.

```zig
const std = @import("std");
const Io = std.Io;

fn square(out: *u64, n: u64) void {
    out.* = n * n;
}

test "a Group owns the lifetime of its tasks" {
    const io = std.testing.io;
    var results: [4]u64 = undefined;
    var group: Io.Group = .init;
    defer group.cancel(io);

    for (&results, 0..) |*slot, i| {
        group.async(io, square, .{ slot, @as(u64, i) });
    }
    try group.await(io);
    try std.testing.expectEqualSlices(u64, &.{ 0, 1, 4, 9 }, &results);
}
```

- `io.async` may run inline or concurrently; `io.concurrent` requires real
  concurrency and can fail. Choose by contract, not by hope.
- Every `Group` or `Future` is awaited or canceled before its owner
  returns; `defer group.cancel(io)` is the safety net.
- Synchronization moved to `Io`: `std.Io.Mutex`, `std.Io.Condition`,
  `std.Io.RwLock`, `std.Io.Semaphore` take the `io` instance
  (`std.Thread.Mutex` is gone in 0.16). `std.Thread.spawn` still exists
  for raw threads; `std.atomic.Value(T)` for lock-free state.
- Files and directories: `std.Io.Dir.cwd()`, `dir.openFile(io, ...)`,
  `dir.writeFile(io, ...)`, `dir.readFileAlloc(io, ...)`; stdio through
  `Io.File.stdout()` with an `Io.File.Writer` and an explicit buffer, and
  `flush()` before exit. `std.fs.Dir`/`std.fs.File` moved here in 0.16.
- Subprocesses: `std.process.run(gpa, io, .{ .argv = ... })` for
  collect-and-wait, `std.process.spawn(io, ...)` for streaming; arguments
  are a list, never a shell string.
- Format methods are invoked with the `{f}` specifier (0.15+, verified
  0.16); `{s}` is for strings, `{d}` for integers, `{any}` for a debug
  dump.

## C interop and security boundary

Treat foreign input as hostile by default:

- validate lengths before slicing memory that came from C; a `[*c]T` has
  no length and may be null;
- convert C strings with `std.mem.span` after checking they are
  terminated; never trust a declared size from a foreign header over the
  bytes you received;
- integer conversions at the boundary use `std.math.cast` or explicit range
  checks, not `@intCast`;
- `extern` and `callconv(.c)` functions must not let a Zig error or panic
  cross into C; return codes cross, errors do not;
- dependencies in `build.zig.zon` are pinned by `hash`; a `url` is a
  mirror, the hash is the identity. Review a dependency's `build.zig`
  before adding it: it runs on every build;
- `build.zig` runs arbitrary code at build time; treat third-party build
  logic as untrusted;
- secrets never enter `@embedFile`, source, or logs.

## Tests and validation

- `test` blocks live next to the code; `zig build test` runs the test
  steps declared in `build.zig`; `zig test file.zig` runs one file.
- `std.testing.allocator` for every allocating test; a leak fails the run.
- `std.testing.expectEqual`, `expectEqualStrings`, `expectEqualSlices`,
  `expectError`; `std.testing.tmpDir` for filesystem cases.
- `std.testing.fuzz` (0.16) with a `Smith` for input generation; `zig
  build test --fuzz` drives it.
- Process-isolated tests for environment-sensitive behavior: run the test
  binary again through `std.process.run(gpa, io, .{ .argv = ... })` with a
  guard environment variable, read the first line of stdout.

Run repository-configured checks first. If no stronger gate exists, use the
house baseline from [`SKILL.md`](SKILL.md#-conventional-verification-baseline)
and label it as such: `zig fmt --check`, `zig build`, `zig build test`,
and the suite again under `-Doptimize=ReleaseSafe` when the code ships in
a release mode.

## Version awareness

Zig changes between minors. Before trusting a name:

- 0.16: `std.Io` required for all I/O; `main(init: std.process.Init)`;
  `Io.Group`/`Future`/`Batch`; `std.fs` moved to `std.Io.Dir`/`File`;
  `std.Thread.Mutex` moved to `std.Io.Mutex`; `@Type` split into
  `@Int`, `@Struct`, and friends; `@cImport` deprecated;
  `ThreadSafeAllocator` removed; `ArenaAllocator` thread safe.
- 0.15: unmanaged `ArrayList` by default; `std.Io.Writer`/`Reader`
  rewrite; `{f}` required for format methods.
- 0.14: `DebugAllocator` replaces `GeneralPurposeAllocator`; labeled
  switch with `continue`; decl literals; `build.zig.zon` `.fingerprint`
  and enum-literal `.name`.
- 0.11 to 0.13: `@ptrCast`/`@alignCast` take the result type from context;
  language-level async removed.

Read the release notes of the project's pinned version:
https://ziglang.org/download/<version>/release-notes.html

## References

- [Zig Language Reference 0.16.0](https://ziglang.org/documentation/0.16.0/)
- [Zig 0.16.0 release notes](https://ziglang.org/download/0.16.0/release-notes.html)
- [Zig standard library documentation](https://ziglang.org/documentation/0.16.0/std/)
- [Zig Build System](https://ziglang.org/learn/build-system/)
- [Zig Code Review Directives](CODE-REVIEW.md)
