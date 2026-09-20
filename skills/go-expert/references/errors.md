# Errors and Failure Contracts

Owner of: error construction, wrapping, matching, and what an error promises
its caller.

Errors are part of the API contract: enough context for the caller to act,
without redundant context at every layer.

## Core rules

- Wrap underlying errors with `%w` when callers may need `errors.Is` or
  `errors.As`.
- Match and extract with `errors.Is` / `errors.As`; do not compare error
  strings. Never make callers parse error strings as a protocol.
- Use sentinel errors only as a deliberate part of the package contract.
- Prefer direct `if err != nil { return ... }` handling that preserves Line of
  Sight — see [code-style](code-style.md).

## Designing the contract

- Return errors for ordinary operational failures; reserve panic for broken
  invariants or unrecoverable initialization.
- Add context at the layer that can explain or act on the failure.
- Decide whether an error is retryable, terminal, transient, or safe to
  expose.
- Handle errors from `Close`, `Flush`, `Commit`, `Sync`, and `Rollback` when
  they can change the durability or transaction contract — see
  [resources](resources.md).
- Log an error once at the boundary that owns the decision; avoid logging and
  returning the same event at every layer. Output conventions live in
  [logging](logging.md).

The repeated `if err != nil` is not duplication to be factored away. It is the
explicit control flow Go chose; see
[`SKILL.md`](../SKILL.md#dry-carries-less-weight-in-go).
