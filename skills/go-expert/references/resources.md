# Resource and Standard-Library Boundaries

Owner of: acquiring and releasing owned resources, and the standard-library
boundaries where a default silently changes a contract.

- Close HTTP response bodies, database rows, statements, files, and other
  owned resources at the narrowest reliable lifetime boundary.
- Check HTTP errors before dereferencing the response, validate status codes,
  and configure operation-appropriate timeouts — see [context](context.md).
- Parameterize SQL values. Never build SQL by concatenating external input;
  the threat model is in [security](security.md).
- Make JSON presence semantics explicit: `omitempty`, nil pointers, nil
  slices, zero values, and false booleans can change the wire contract. The
  nil-versus-empty decision itself belongs to [values](values.md).
- Use `crypto/rand` for secrets, tokens, nonces, and security decisions;
  `math/rand` is not a cryptographic source.
- Drain a response body before closing it, with
  `io.Copy(io.Discard, resp.Body)`: a body closed part-read cannot return
  its connection to the pool — see [performance](performance.md).
- Avoid finalizers as deterministic cleanup. Make `Close`, cancellation, and
  shutdown explicit.

## `defer` runs at function exit, not at the end of the block

A `defer` inside a loop does not release anything per iteration. The calls
stack up and all of them run when the *function* returns, so a loop over
ten thousand paths holds ten thousand open files — until the file
descriptor limit ends the program somewhere unrelated.

```go
// Every file stays open until the function returns.
for _, path := range paths {
	f, err := os.Open(path)
	if err != nil {
		return err
	}
	defer f.Close()

	process(f)
}
```

The fix is to give the resource a function whose exit is the lifetime you
actually want:

```go
for _, path := range paths {
	if err := processOne(path); err != nil {
		return err
	}
}

func processOne(path string) error {
	f, err := os.Open(path)
	if err != nil {
		return err
	}
	defer f.Close()

	return process(f)
}
```

This is one of the few cases where extracting a function is not ceremony:
the helper exists because the `defer` needs a scope, which is real behavior
rather than a naming exercise.

## `database/sql` has three silent edges

Parameterizing the query is the part everyone remembers. These are the
parts that pass review and lose data.

- **`rows.Err()` after the loop.** `for rows.Next()` ends both on the last
  row and on a mid-stream failure, and the two are indistinguishable
  without checking. A partial result set that looks complete is the worst
  shape a query can return.
- **`defer tx.Rollback()` right after `Begin`.** After a successful
  `Commit` the rollback is a no-op, so the deferred call costs nothing and
  covers every early return in between — including the panic you did not
  plan for.
- **NULL is not the zero value.** Scanning a nullable column into a
  `string` fails at runtime. Use `sql.NullString` and friends, or a pointer,
  and decide at the boundary what absence means — the nil-versus-empty
  question in [values](values.md).

`QueryRow` reports an empty result as `sql.ErrNoRows`, which is a sentinel
to match with `errors.Is`, not an error to wrap and forget — see
[errors](errors.md). Prefer the `Context` variants so a query inherits the
caller's deadline.

## `os.Exit` does not run deferred functions

`os.Exit` terminates immediately: no `defer`, no flush, no `Close`, no
`Rollback`. So does `log.Fatal`, which calls it — which makes a convenient
one-line failure path silently skip every cleanup registered above it.

Confine both to `main`, after the deferred work has run or where there is
none, and return errors everywhere else. A library that calls `os.Exit`
removes its caller's ability to shut down cleanly.

## Decoding is not the inverse of encoding

`encoding/json` has two asymmetries that produce wrong values rather than
errors:

- a number decoded into `any` becomes a `float64`, so a large integer
  identifier loses precision and reformats in scientific notation. Decode
  into a typed field, or call `Decoder.UseNumber` to keep it as a string
  with the digits intact.
- unexported fields are skipped in both directions, silently. A field that
  round-trips as its zero value is usually this and not the wire format.

Errors returned by `Close`, `Flush`, `Commit`, `Sync`, and `Rollback` can
change a durability or transaction contract — handle them as described in
[errors](errors.md).
