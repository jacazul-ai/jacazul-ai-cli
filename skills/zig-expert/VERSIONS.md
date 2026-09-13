# Zig Version Ladder

Old-to-new names from Zig 0.11 to 0.16, so the expert reads code written
for any of them and writes for the project's floor. Each row was checked
against the release notes of the version that introduced it
(`https://ziglang.org/download/<version>/release-notes.html`); 0.16 rows
were also checked against the installed `std`. A row says what changed,
not that every project must migrate: in a legacy tree the old name is
correct for its floor.

Use it in three directions:

- **Reading old code:** find the old name in the left column to know what
  it meant and what it became.
- **Writing for a floor:** pick the column of the project's
  `.minimum_zig_version` and use the name that existed then.
- **Updating:** walk the rows between source floor and target, one group
  per commit (see the [playbook](PLAYBOOK.md#updating-a-project-to-a-newer-zig)).

## Era markers

What a tree looks like tells its era before `build.zig.zon` does. The
`zig-era` scan reads these markers; a reviewer can read them by eye.

| Marker in source | Era it indicates |
|---|---|
| `@intCast(u8, x)` two-argument casts, `@boolToInt`, `@intToFloat`, `@ptrToInt` | 0.10 or older |
| `for (items) \|x, i\|` without `0..`; `async`/`await`/`suspend` keywords with a frame | 0.10 or older (async also 0.11 to 0.14 as stubs, removed 0.15) |
| `std.build.Builder`, `exe.setBuildMode`, `b.standardReleaseOptions()` | 0.10 or older |
| `std.os.` calls for POSIX (`std.os.abort`, `std.os.exit`), `@fieldParentPtr(T, "f", p)`, `@fabs`, `@errSetCast` | 0.11 |
| `.{ .path = "src/main.zig" }` in `build.zig`, `LazyPath.relative` | 0.11 or 0.12 |
| `std.ChildProcess`, `std.rand.`, `ComptimeStringMap`, `zig-cache/` directory | 0.12 or older |
| `std.heap.GeneralPurposeAllocator(.{}){}`, `callconv(.C)`, `@setCold`, `@export(foo, ...)` without `&`, `.Int`/`.Struct` in `std.builtin.Type` switches, `addExecutable(.{ .root_source_file = ... })` without `root_module` | 0.13 or older |
| `usingnamespace`, `std.ArrayList(T).init(gpa)` with `list.append(x)` (managed), `std.io.getStdOut().writer()`, `BufferedWriter`, `"{}"` on a type with a `format` method, `BoundedArray`, `build.zig.zon` `.name = "string"` without `.fingerprint` | 0.14 or older |
| `std.fs.cwd()`, `std.fs.File`, `std.Thread.Mutex`, `std.io.` namespace, `pub fn main() !void` without `Init`, `@Type(.{ ... })`, `@cImport` in new code | 0.15 or older |
| `main(init: std.process.Init)`, `std.Io.Dir`/`File`, `std.Io.Mutex`, `Io.Group`, `@Int`/`@Struct`, `b.addTranslateC`, `std.testing.io` | 0.16 |

Mixed markers mean a migration in progress; the newest marker sets the
target, the oldest sets what still has to move.

## 0.11

| Old | New | Note |
|---|---|---|
| `@intCast(u8, x)`, `@ptrCast(*T, p)`, `@truncate`, `@bitCast`, `@floatCast` with a type argument | `@intCast(x)` with the result type from context | Result Location Semantics for casts |
| `@boolToInt`, `@intToFloat`, `@floatToInt`, `@intToPtr`, `@ptrToInt`, `@enumToInt`, `@intToEnum` | `@intFromBool`, `@floatFromInt`, `@intFromFloat`, `@ptrFromInt`, `@intFromPtr`, `@intFromEnum`, `@enumFromInt` | Renamed for the `X from Y` reading |
| `for (items) \|x, i\|` | `for (items, 0..) \|x, i\|` | Explicit range operand; `for (&arr) \|*x\|` for pointer captures |
| `std.json.parse`, `parseFree`, `TokenStream`, `StreamingParser` | `std.json.parseFromSlice`, `Parsed(T).deinit()`, `Scanner`, `Reader` | An allocator is always required for parsing |
| `(object.method)(args)` bound functions | `object.method(args)` only | Bound functions removed |
| Language-level `async`/`await` | Not available (stubs stay until 0.15) | Self-hosted compiler without async |

## 0.12

| Old | New | Note |
|---|---|---|
| `std.os.*` for POSIX | `std.posix.*` | Prefer the cross-platform layer over POSIX |
| `@fieldParentPtr(Parent, "field", ptr)` | `const p: *Parent = @fieldParentPtr("field", ptr)` | Result type from context |
| `@fabs` | `@abs` | Works on integers and floats |
| `@errSetCast` | `@errorCast` | Also handles error unions |
| `LazyPath.relative("src/x.zig")`, `.{ .path = "src/x.zig" }` | `b.path("src/x.zig")` | Deprecated in 0.12, gone later |
| `fn () align(4) void` | compile error | Function types cannot carry alignment |
| Bring-your-own-OS layer | removed | No migration path |

## 0.13

| Old | New | Note |
|---|---|---|
| `std.ChildProcess` | `std.process.Child` | Old name removed after deprecation |
| `std.ComptimeStringMap(T, kvs)` | `std.StaticStringMap(T).initComptime(kvs)` | List moved to the init call |
| `Crc32WithPoly(.Castagnoli)` | `Crc(.Crc32Iscsi)` | Hash API |
| `.iov_base`/`.iov_len` | `.base`/`.len` | POSIX iovec fields |
| `std.Progress` by pointer, `node.activate()` | `std.Progress.start()`, nodes by value | Progress API |
| `zig-cache/` | `.zig-cache/` | Cache directory |
| `YES_COLOR` | `CLICOLOR_FORCE` | Compiler color output |

## 0.14

| Old | New | Note |
|---|---|---|
| `std.heap.GeneralPurposeAllocator(.{}){}` | `std.heap.DebugAllocator(.{}){}` | Rewritten for runtime page size |
| Managed `std.ArrayList(T).init(gpa)`, `list.append(x)` | Unmanaged variants with the allocator per call | Deprecated here, default in 0.15 |
| `switch` without labels for state machines | `sw: switch (x) { ... continue :sw next }` | Labeled switch |
| `const v: S = S.default` | `const v: S = .default` | Decl literals |
| `@export(foo, ...)` | `@export(&foo, ...)` | The address is exported |
| `@setCold(true)` | `@branchHint(.cold)` | First statement of the function |
| `.Int`, `.Struct`, `.Pointer`, `.One` in `std.builtin.Type` | `.int`, `.@"struct"`, `.pointer`, `.one` | Lowercased fields |
| `callconv(.C)` | `callconv(.c)` | Decl literal; `.withStackAlign(.c, 4)` available |
| `build.zig.zon` `.name = "pkg"` | `.name = .pkg` plus `.fingerprint = 0x...` | Enum literal name, generated fingerprint, 32-byte limits |
| `addExecutable(.{ .root_source_file = ... })` | `addExecutable(.{ .root_module = b.createModule(.{ ... }) })` | Module creation API |
| `std.mem.tokenize`, `std.mem.split`, `std.zig.CrossTarget` | `tokenizeAny`/`tokenizeScalar`, `splitAny`/`splitScalar`, `std.Target.Query` | Deprecated aliases now errors |
| Aggregate sentinels | forbidden | Sentinels must be scalars |

## 0.15

| Old | New | Note |
|---|---|---|
| `std.ArrayList(T)` managed with an allocator field | `std.ArrayList(T)` is unmanaged; managed is `std.array_list.Managed(T)` | `ArrayListUnmanaged` becomes an alias |
| `std.io.getStdOut().writer().print(...)` | `var w = std.fs.File.stdout().writer(&buf); const out = &w.interface; ... try out.flush();` | "Writergate": buffer lives in the interface |
| `std.io.GenericReader`/`GenericWriter`, `BufferedWriter`, `CountingWriter` | `std.Io.Reader`/`std.Io.Writer`; buffered types deleted | One interface with a buffer |
| `std.fs.File.reader()`/`writer()` | `deprecatedReader()`/`deprecatedWriter()`, then the new writer with a buffer | Transitional names |
| `"{}"` on a type with a `format` method | `"{f}"` | Explicit call of the format method |
| `pub fn format(self, comptime fmt, options, writer)` | `pub fn format(self, writer: *std.Io.Writer) std.Io.Writer.Error!void` | `FormatOptions` only for numbers |
| `std.fmt.Formatter` | `std.fmt.Alt` | |
| `usingnamespace` | removed | Conditional declarations or `@fieldParentPtr` mixins |
| `async`/`await` keywords, `@frameSize` | removed | Concurrency moves to the standard library (0.16 `std.Io`) |
| `std.DoublyLinkedList(T).Node` | `std.DoublyLinkedList.Node` embedded in your struct, `@fieldParentPtr` | De-generified lists |
| `std.BoundedArray`, `std.fifo.LinearFifo`, `std.RingBuffer` | removed | Unmanaged `ArrayList` over a buffer |
| LLVM backend in Debug on x86_64 | self-hosted x86_64 backend by default in Debug | Faster builds; `-fllvm` to opt out |

## 0.16

| Old | New | Note |
|---|---|---|
| `pub fn main() !void` | `pub fn main(init: std.process.Init) !void` | `init.io`, `init.gpa`, `init.arena`, `init.minimal.args`, `init.environ_map` |
| Free functions doing I/O | Every I/O call takes an `io: std.Io` | `Io.Threaded` complete, `Io.Evented` experimental, `Io.Uring` proof of concept |
| `std.fs.cwd()`, `std.fs.Dir`, `std.fs.File`, `std.fs.File.stdout()` | `std.Io.Dir.cwd()`, `std.Io.Dir`, `std.Io.File`, `Io.File.stdout()` with `Io.File.Writer.init(file, io, &buf)` | Filesystem moved under `Io` |
| `std.Thread.Mutex`, `Condition`, `RwLock`, `Semaphore` | `std.Io.Mutex` and friends, taking `io` | `std.Thread.spawn` remains for raw threads |
| `std.process.Child.spawn()` | `std.process.spawn(io, ...)`, `std.process.run(gpa, io, ...)` | |
| `std.heap.ThreadSafeAllocator` | removed; `ArenaAllocator` is thread safe and lock free | Mutexes need `io` |
| `@Type(.{ .int = ... })` | `@Int`, `@Struct`, `@Union`, `@Enum`, `@Pointer`, `@Fn`, `@Tuple` | One builtin per kind |
| `@cImport` | `b.addTranslateC` in `build.zig` and `@import` of the module | Deprecated, still compiles |
| Hand-rolled task pools | `io.async`, `io.concurrent`, `Io.Group`, `Io.Future`, `Io.Batch` with `await`/`cancel` | Task-level abstraction in the library |
| `std.testing` without an `Io` | `std.testing.io` (an `Io.Threaded`), `std.testing.fuzz` with `Smith` | |

## Refresh procedure (one per Zig release)

Zig is pre-1.0, so this ladder is reviewed once per release, by script,
not by memory. The gate that says a refresh is due is
`tests/test_zig_examples.py`: it fails when the installed `zig version`
has no `## <minor>` section here, and it fails when any file in
`examples/` no longer passes `zig test`.

1. Install the release; `zig version`.
2. Run `python -m unittest tests.test_zig_examples`. The failures are the
   work list: broken examples and the missing ladder section.
3. Read `https://ziglang.org/download/<version>/release-notes.html`.
   Extract every old → new pair for the language, `std`, and the build
   system into a new `## <minor>` table above, with a note per row.
4. For each row with a syntactic signature (a renamed symbol, a changed
   call shape), add an era marker: a row in the "Era markers" table, a
   regex in `jacazul/zigexpert/archaeology.py` (`until` the previous
   minor for the old form, `since` the new minor for the new form when it
   is unmistakable), and a case in `tests/test_zig_era.py`.
5. Run `zig init` in a scratch directory and diff the generated
   `build.zig`, `build.zig.zon`, `main.zig` against the shapes described
   in the playbook; update the playbook where the skeleton moved.
6. Fix the examples in `examples/` until `zig test` passes on the new
   release, then paste the exact file bodies back into the playbook (the
   test checks that the playbook blocks mirror the files).
7. Update the version ladder in the playbook, the landmarks in
   `SKILL.md`, and the "verified on" release in the three files.
8. Record the refresh as a task with the release in its description and
   the release-notes URL in a `RESEARCH` note; `Refs: #117` until a
   dedicated ticket exists.

Nothing in this procedure requires remembering what changed: the test
names the release, the notes name the changes, the examples prove the
result.

## Stable across the ladder

`defer`/`errdefer`, error sets and `try`/`catch`, optionals, slices and
sentinel pointers, `comptime` parameters and functions returning types,
`test` blocks and `std.testing.allocator`, `zig fmt`, the four optimize
modes and the safety-checked behavior list, `std.mem.Allocator` as the
allocator interface, `std.debug.print`.
