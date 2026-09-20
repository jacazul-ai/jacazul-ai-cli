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

Ownership is the question behind most concurrency bugs as well: see
[concurrency](concurrency.md) for goroutine, channel, and lock ownership.

Whether a seam is needed at an ownership boundary is decided in
[testing](testing.md); what shape it takes is decided here and in
[packages](packages.md).
