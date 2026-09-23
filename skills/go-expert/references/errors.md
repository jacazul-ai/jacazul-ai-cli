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

## An unchecked error is a decision nobody wrote down

Discarding a returned error with `_` is occasionally right and almost
never explained. When it is right — a `Close` on a read-only file whose
failure changes nothing — say so in a comment, because the next reader
cannot tell a deliberate discard from a forgotten one.

**Diagnose:** `errcheck`, and `staticcheck` for the subset it covers.
Neither is a project mandate unless the repository configures it.

## `%w` is an API decision, `%v` is not

`fmt.Errorf` with `%w` puts the wrapped error into your contract: callers
can reach it with `errors.Is` and `errors.As`, and from then on it cannot
be swapped without breaking them. `%v` formats the text and ends the
chain there.

Inside a package, wrap with `%w` so callers can match what they need. At a
system boundary — the edge of a library, a handler returning to a client —
decide deliberately whether the internals should remain matchable. A
`database/sql` error that escapes through `%w` makes every caller's
`errors.Is` depend on your storage choice.

```go
// Internal: the caller may legitimately match on it.
return fmt.Errorf("loading user %s: %w", id, err)

// Boundary: the cause is logged, not exported into the contract.
return fmt.Errorf("loading user: %v", err)
```

## Joining independent failures

`errors.Join` (Go 1.20+) combines errors that happened side by side rather
than in a chain — validating several fields, closing several resources.
`errors.Is` and `errors.As` traverse the result, so callers keep matching.

```go
var errs error
for _, f := range fields {
	errs = errors.Join(errs, f.Validate())
}

return errs // nil when every Validate returned nil
```

It returns nil when all its arguments are nil, which is what makes the
accumulate-in-a-loop shape work without a length check.

## Extracting a typed error

`errors.As` needs a pointer to a target variable, which is easy to get
wrong. The generic form reads better and cannot be given the wrong target
shape:

```go
pathErr, ok := errors.AsType[*fs.PathError](err)
```

`errors.AsType` is present in the toolchain this skill was checked against
(Go 1.27). Confirm it against the `go` directive in `go.mod` before using
it — see [runtime](runtime.md) for the version rule.

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
