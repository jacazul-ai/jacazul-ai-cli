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

## Size the structure to the project

Architecture complexity should match project scope. Splitting a small program
into layers costs clarity and buys nothing.

| Project size | Shape |
| --- | --- |
| Script or small CLI, under ~500 lines | Flat `main.go` plus a few files, no layers |
| Medium service, ~500 to 5K lines | Simple layered split by behavior |
| Large service, 5K+ lines | Ask the team which boundary discipline it wants |

A 100-line CLI does not need a domain layer, ports and adapters, or a
dependency-injection container. Start simple and restructure when complexity
demands it, not when a diagram suggests it.

This skill does not prescribe a named architecture. Clean, hexagonal, and DDD
are team choices with real trade-offs, not Go defaults, and adopting one is a
project decision rather than a style correction.

## Keep the dependency direction honest

Domain logic should not import infrastructure. Database access, HTTP clients,
and message queues live in packages that depend on the domain — never the
reverse. This holds whatever the team calls its layering, and it is the part
of "clean architecture" that survives without the ceremony.

## Validate at the boundary, then trust

Validate input where it enters the system: HTTP handlers, CLI argument
parsing, message consumers, file and subprocess reads. Once data has passed
the boundary, internal code should trust it.

Do not re-validate the same value at every layer. It clutters the happy path
and produces the same error from several places, so the caller cannot tell
which check actually fired. This is the same rule that keeps error context
from being restated at every level — see [errors](errors.md), and
[security](security.md) for what boundary validation must cover.

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
