# Values and Ownership

Owner of: copy semantics, shared state through reference types, ownership
transfer, and the nil-versus-empty decision.

- Remember that assignments copy values, while slices, maps, pointers,
  interfaces, channels, and function values can still refer to shared state.
- Document whether a function borrows, consumes, mutates, or returns ownership
  of a slice, buffer, map, or pointer.
- Clone data at an ownership boundary when later mutation or retention would
  be surprising. Avoid copying synchronization values after first use.
- Decide whether nil and empty mean the same thing. Make the distinction
  explicit when it reaches JSON, storage, or another wire boundary.
- Do not retain a large backing allocation merely to return a small subset;
  measure and copy when the lifetime justifies it.

## Parameters: value or pointer

This is the parameter question; the receiver question belongs to
[structs-interfaces](structs-interfaces.md), and the two answers do not
have to match.

Pass by pointer when the function mutates the argument, when nil is a
meaningful value the caller can send, or when the struct is large enough
that copying it costs more than the indirection — roughly 128 bytes, and
worth measuring rather than guessing.

Pass by value otherwise. `string`, `int`, `bool`, `float64`, and
`time.Time` are already small; a `*string` parameter that is never nil and
never assigned through buys nothing and forces every caller to have an
addressable variable. For a small read-only struct the value is often
faster anyway, because it stays on the stack and in cache.

"To save memory" is not a reason. A pointer trades a copy for a possible
cache miss, and for small values that trade loses.

## Returning internals

An exported method that returns a struct's own slice or map hands callers a
live handle to the internals. Return `slices.Clone` or `maps.Clone` when
later mutation by the caller would be surprising — see
[data-structures](data-structures.md) for the aliasing mechanics and
[packages](packages.md) for why the field stays unexported in the first
place.

Ownership is the question behind most concurrency bugs as well: see
[concurrency](concurrency.md) for goroutine, channel, and lock ownership.

Whether a seam is needed at an ownership boundary is decided in
[testing](testing.md); what shape it takes is decided here and in
[packages](packages.md).
