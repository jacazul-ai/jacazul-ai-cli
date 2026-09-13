# Zig Expert Skill

Guide for the zig-expert skill: explicit, allocator-honest, safety-aware
Zig with a pinned toolchain, the conventional `zig fmt`/`zig build test`
baseline, and review on the shared `code-review` scale. Verified on Zig
0.16.0.

## Trigger → Action

### When you touch any Zig tree

The expert pins the release before anything else:

```bash
zig version
grep minimum_zig_version build.zig.zon
```

The project floor wins over the installed toolchain. Zig is pre-1.0 and
the standard library moves between minors, so every claim the expert makes
names the release it was verified on, and the installed `std` is the final
word when documentation and code disagree.

### When you inherit Zig code from another era

Run `zig-era <root>`. It names the newest release the code targets, the
oldest marker still present, and the declared floor, without needing the
toolchain:

```text
🐊 ZIG_ERA: 0.16
   floor: 0.16.0 (build.zig.zon)
   migration: oldest marker 0.13, newest 0.16; walk VERSIONS.md between them
  - 0.13: std.heap.GeneralPurposeAllocator x1 (old.zig)
  - 0.16: main(init: std.process.Init) x1 (new.zig)
```

The expert then reads the old names through
[`skills/zig-expert/VERSIONS.md`](../skills/zig-expert/VERSIONS.md), a
ladder from 0.11 to 0.16 checked against each release's notes, and writes
for the project's floor.

### When a new Zig release comes out

Nobody re-reviews the skill by memory. `python -m unittest
tests.test_zig_examples` fails when the installed version has no section
in the ladder or when a playbook example stops compiling; the
[refresh procedure](../skills/zig-expert/VERSIONS.md#refresh-procedure-one-per-zig-release)
turns the release notes into ladder rows, era markers and fixed examples.

### When a snippet from the internet does not compile

Expected. Between 0.11 and 0.16 the language removed `async`/`await`,
changed `@ptrCast`, split `@Type`, made `std.ArrayList` unmanaged, rewrote
I/O around `std.Io`, moved `std.fs` and `std.Thread.Mutex` into `std.Io`,
renamed the general-purpose allocator to `DebugAllocator`, and deprecated
`@cImport`. Ask the expert for the 0.16 form; the
[playbook](../skills/zig-expert/PLAYBOOK.md) carries a version ladder and
examples that compiled on 0.16.0.

### When you write a function that allocates

It takes an `std.mem.Allocator`, its doc comment says who frees, and the
release is paired on the next line: `defer` when the function owns the
memory, `errdefer` when the caller receives it on success. Functions with
more than one allocation get a `std.testing.checkAllAllocationFailures`
test; a missing `errdefer` shows up as a leak.

### When you run the gate

```bash
zig fmt --check <paths>
zig build
zig build test
zig build test -Doptimize=ReleaseSafe   # when the code ships in a release mode
```

`std.testing.allocator` fails the run on a leak. `zig build test --fuzz`,
cross-target builds and sanitizers are complementary unless the repository
configures them.

### When something works in Debug and breaks in ReleaseFast

Debug and ReleaseSafe panic on the safety-checked behaviors listed in the
language reference (out of bounds, overflow, invalid enum, unwrapping
null, wrong union field, and more); ReleaseFast and ReleaseSmall make them
undefined. The expert treats the safety net as a debugging aid: external
values are validated explicitly, `unreachable` states a proven invariant,
and casts are claims the code can back.

### When you do I/O or concurrency (0.16)

Everything goes through `std.Io`: `main(init: std.process.Init)` receives
`init.io`, tests use `std.testing.io`, library code accepts `io` and
`*Io.Writer` as parameters. Tasks belong to a `Group` or a `Future` that
is awaited or canceled by its owner; `io.async` may run inline,
`io.concurrent` requires concurrency. There are no language-level async
keywords.

### When you call C

Translate-c through the build (`b.addTranslateC`) in new code; `@cImport`
is deprecated in 0.16 and kept only in legacy code until a migration step.
Foreign pointers are null-checked and bounded, foreign integers go through
`std.math.cast`, and errors never cross an `export` boundary.

### When you ask for a Zig code review

Findings use the shared [`code-review` scale](../skills/code-review/SKILL.md)
with the scenarios in
[`skills/zig-expert/CODE-REVIEW.md`](../skills/zig-expert/CODE-REVIEW.md):
cleanup on the error path, ownership across allocators, `unreachable` on
input, `undefined` read before write, foreign memory, tasks nobody awaits,
and names from another Zig version.

### When you want to learn Zig

Ask for a tutorial. The engine activates `tutor`, `zig-tutor` and
`zig-expert` together; see [Tutors](tutor.md). Every example is compiled on
your toolchain before it is shown.

## Best Practices

1. Pin the version before the first edit and name it in every claim.
2. Pair every allocation with `defer` or `errdefer` on the next line.
3. Run the suite under ReleaseSafe when you ship a release mode.
4. Accept `io` and writers as parameters; never print from a library.
5. Grep the installed `std` when the docs and the compiler disagree.

---

**Version:** 1.0.0
**Last Updated:** 2026-09-13
