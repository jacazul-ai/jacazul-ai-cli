# Data Structures

Owner of: slice and map internals, preallocation, the standard collection
packages, and string building. Ownership and copy semantics of those values
belong to [values](values.md).

## Nil collections

A nil slice, map, or channel is a usable value, not an error state — with
one asymmetry that produces most of the panics:

| | Read / index | Write | `len` | `range` |
| --- | --- | --- | --- | --- |
| Slice | panic | panic | 0 | 0 iterations |
| Map | zero value | **panic** | 0 | 0 iterations |
| Channel | blocks forever | blocks forever | 0 | blocks forever |

A nil map reads fine and panics on the first write, so the bug surfaces far
from the missing `make`. A nil slice, by contrast, appends correctly, which
is why `var s []T` is the idiomatic start of an accumulation loop and
`[]T{}` buys nothing.

Do not adopt a blanket "always initialize" rule for slices: it is wrong in
Go and it hides the one decision that matters, which is whether nil and
empty mean the same thing at the boundary the value reaches. That decision
lives in [values](values.md), and its JSON consequence — `null` versus `[]`
— in [resources](resources.md).

## Aliasing: append and the backing array

A slice is a pointer, a length, and a capacity. Two slices can point into
the same backing array, and `append` reuses that array whenever the
capacity allows, so a write through one is visible through the other:

```go
a := make([]int, 3, 5)
b := append(a, 4)
b[0] = 99 // a[0] is 99 too
```

Whether that happens depends on spare capacity, so the same code can be
correct in a test and wrong in production. When a slice crosses an
ownership boundary, remove the ambiguity: the full slice expression sets
capacity equal to length, forcing the next `append` to allocate.

```go
b := append(a[:len(a):len(a)], 4) // a is never touched
```

The mirror image is retention: a subslice keeps the *whole* backing array
alive, so holding 64 bytes of a 1 MB buffer keeps the megabyte out of the
collector's reach. Copy when the small piece outlives the big one — see
[values](values.md) for the ownership rule behind both directions.

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

`slices.Clone` and `maps.Clone` are the defensive copy at an ownership
boundary. They are clearer than `make` plus `copy` and they preserve nil,
returning nil rather than an empty collection, which keeps the
nil-versus-empty decision the caller made.

Comparison goes through `slices.Equal` and `maps.Equal`; `==` does not
compile for either, and comparing pointers or lengths by hand is how a
wrong-but-passing test gets written.

## Mutating while iterating

Deleting from a map during `range` is defined and safe. Deleting from a
slice during `range` is not: the elements shift under the loop and the
iteration skips the one that moved into the freed index.

```go
// Skips an element after every removal.
for i, v := range items {
	if drop(v) {
		items = append(items[:i], items[i+1:]...)
	}
}

// Go 1.21+: says what it means, and is correct.
items = slices.DeleteFunc(items, drop)
```

Iterating backwards also works when the condition cannot be expressed as a
predicate, but `slices.DeleteFunc` is the first choice.

Map iteration order is randomized by the runtime and must never be part of
a contract. Sort the keys when the order reaches output or behavior — the
control-flow side of that rule is in [code-style](code-style.md).

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
