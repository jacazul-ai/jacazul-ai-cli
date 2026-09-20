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

Errors returned by `Close`, `Flush`, `Commit`, `Sync`, and `Rollback` can
change a durability or transaction contract — handle them as described in
[errors](errors.md).
