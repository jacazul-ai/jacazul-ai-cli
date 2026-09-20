# Package and API Design

Owner of: package boundaries, public API surface, compatibility contracts, and
the standard library as a design reference.

## Before writing code

1. Read the module's `go` directive and identify the supported toolchain.
2. Read the target package and its tests before introducing an abstraction.
3. Define the API contract: valid input, absence, errors, timeouts, retries,
   partial success, ownership, and shutdown behavior.
4. Identify trust boundaries: users, network payloads, files, subprocesses,
   databases, dependencies, generated data, and logs — see
   [security](security.md).
5. Decide who owns every mutable value, resource, goroutine, channel, lock,
   transaction, and cancellation signal — see [values](values.md).

## Package design

- Package names: short, lowercase, named by the behavior or domain they
  provide — not artificial layers.
- Avoid grab-bag packages (`util`, `common`, `helpers`) unless the repository
  already uses that convention and the package has a clear boundary.
- Prefer a small public API; keep unexported details inside the owning
  package.
- Prefer concrete types and package functions until a real consumer needs an
  interface or a test seam.
- Define small interfaces near the consumer; name them by behavior — see
  [naming](naming.md).
- Preserve compatibility deliberately: exported types, errors, wire formats,
  and serialization details are contracts once consumers depend on them.

Do not split code into layers to look architectural. A package earns its
boundary by owning behavior, not by occupying a position in a diagram.

## Standard library as design compass

When unsure, look for the pattern in the standard library first — do not
invent a framework pattern when a standard-library pattern is enough:

- `io` for small behavior interfaces.
- `net/http` for handlers and middleware shape.
- `context` for cancellation and deadlines.
- `errors` for wrapping and matching.
- `testing` for table tests and benchmark/fuzz conventions.
- `database/sql` for interface boundaries and explicit error handling.
