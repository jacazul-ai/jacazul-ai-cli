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

## The typed nil return

An interface value holds a type and a value, and it is `nil` only when both
are. A function that declares `error` but returns a typed nil pointer hands
back a non-nil interface, so the caller's `if err != nil` fires on success:

```go
// The caller always sees an error, even when there is none.
func validate(s string) error {
	var err *ValidationError
	if s == "" {
		err = &ValidationError{Field: "name"}
	}

	return err
}
```

Declare the failure path and the success path separately and return the
untyped `nil` for success:

```go
func validate(s string) error {
	if s == "" {
		return &ValidationError{Field: "name"}
	}

	return nil
}
```

`errors.Is(err, nil)` does not rescue this: the interface was already
non-nil before it reached the comparison. The same trap applies to any
interface-typed return, not only `error` — see
[structs-interfaces](structs-interfaces.md) for the nil receiver it pairs
with.

Default `go vet` does not catch this. `staticcheck` and the `nilerr` linter
report some shapes; neither covers every path, so the defence is the habit
of returning the untyped `nil` rather than a tool.

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
