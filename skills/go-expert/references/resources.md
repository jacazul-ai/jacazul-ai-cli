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

Errors returned by `Close`, `Flush`, `Commit`, `Sync`, and `Rollback` can
change a durability or transaction contract — handle them as described in
[errors](errors.md).
