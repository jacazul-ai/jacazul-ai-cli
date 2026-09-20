# Security Boundary

Owner of: hostile input, secrets, subprocess construction, and the escape
hatches that bypass Go's guarantees. Repository-wide security work belongs to
the `security-expert` skill; this reference covers the Go-specific surface.

Treat external input as hostile by default:

- validate size, shape, encoding, and allowed values before expensive work;
- pass subprocess arguments directly instead of constructing shell syntax;
- constrain paths, URLs, regular expressions, decompression, and allocations;
- redact credentials and personal data from logs, errors, tests, and traces;
- use least-privilege credentials and reviewed dependencies;
- run vulnerability analysis when dependency or release risk is in scope.

Use `crypto/rand` for anything security-bearing — see
[resources](resources.md) for the surrounding standard-library boundaries.

## unsafe, reflection, and cgo

Do not introduce `unsafe`, reflection, or cgo to bypass a design problem. If
one is required, isolate it behind a small boundary and document lifetime,
alignment, aliasing, layout, and foreign-memory ownership invariants.
