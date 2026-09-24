---
type: llm
---

- The answer sides with the author: a nil slice is the idiomatic
  accumulator, `append` works on it, and `len` and `range` treat it as
  empty.
- It rejects "slices must always be initialized" as a general rule.
- It names the real exception: serialization, where a nil slice encodes as
  JSON `null` and an empty one as `[]`, and places that concern at the
  serialization boundary rather than at the declaration.
