# Data Structures

Owner of: slice and map internals, preallocation, the standard collection
packages, and string building. Ownership and copy semantics of those values
belong to [values](values.md).

## Preallocate when the size is known

`make([]T, 0, n)` and `make(map[K]V, n)` avoid repeated growth copies and map
rehashing. Estimating is enough — the win comes from skipping most of the
growth steps, not from being exact.

Do not depend on *when* growth happens. The slice growth algorithm has changed
between Go releases and may change again, so code that assumes a particular
capacity after a particular number of appends is relying on an implementation
detail.

Preallocation is worth doing when the size is known or bounded. It is not
worth contorting code to compute a size that the program does not already
have.

## Arrays

Prefer an array over a slice only for a fixed, compile-time-known size: a hash
digest, an IPv4 address, a matrix dimension. An array is a value, so it copies
on assignment and on every function call — see [values](values.md).

## Standard collections

| Package | Use for |
| --- | --- |
| `container/heap` | Priority queues |
| `container/list` | Only when frequent middle insertion is the actual cost |
| `container/ring` | Fixed-size circular buffers |

A slice beats `container/list` for almost every traversal-heavy workload, so
reach for the list only when the middle insertion is measured, not assumed.

## Building strings and buffers

- `strings.Builder` for building a string: it avoids the copy that repeated
  concatenation performs.
- `bytes.Buffer` for bidirectional I/O, since it implements both `io.Reader`
  and `io.Writer`.

## The `slices` and `maps` packages (Go 1.21+)

`slices` and `maps` cover sorting, searching, comparison, cloning, and key or
value extraction that used to require hand-written loops. Prefer them over a
local reimplementation, and read the doc comment before assuming a function
copies rather than aliases — see [values](values.md).

## Generic collections

Use the tightest constraint that expresses the requirement: `comparable` for
map keys, `cmp.Ordered` for ordering, a small custom interface for behavior.
A loose constraint pushes errors to the call site and defeats the reason for
the generic. Whether a generic is warranted at all is decided in
[structs-interfaces](structs-interfaces.md).

## Pointer-shaped escape hatches

- `unsafe.Pointer` conversions must follow the patterns the Go spec
  enumerates. Never park one in a `uintptr` across statements: the garbage
  collector does not track `uintptr`, so the referenced object can move or be
  freed. See [security](security.md) for the boundary rules around `unsafe`.
- `weak.Pointer[T]` (Go 1.24+) lets a cache or canonicalization map hold an
  entry without keeping it alive, so the collector can reclaim it. Confirm the
  `go` directive supports it before use — see [runtime](runtime.md).
