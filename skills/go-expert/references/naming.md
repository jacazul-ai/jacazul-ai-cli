# Naming: Types, Structs, and Interfaces

Owner of: identifier choice for types, interfaces, and their Java-shaped
anti-patterns. Package naming lives in [packages](packages.md).

Go has no classes — use Go terminology: **types**, **structs**, and
**interfaces**.

- Name concrete types by domain role or real responsibility. `Manager`,
  `Service`, `Processor`, and `Helper` are suspect unless they describe a real
  domain concept; avoid inheritance-shaped `BaseThing` / `AbstractThing`.
- Keep interfaces small and behavior-based; prefer standard-library-style
  names when they fit: `Reader`, `Writer`, `Handler`, `Closer`, `Encoder`,
  `Decoder`, `Validator`.
- Define interfaces near the consumer unless the repository has a clear
  package-boundary reason not to.
- Avoid Java-style `IThing`, `ThingInterface`, or broad service interfaces
  created before there are real consumers.
- Name interfaces by behavior rather than by implementation: `Reader` over
  `FileManager`.

Use explicit types for units, identifiers, states, and values whose invalid
combinations would otherwise be easy to construct. A named type that makes an
illegal state unrepresentable earns its existence; one that only renames a
`string` does not.

An interface that does not yet have a consumer is not a naming problem, it is
a premature abstraction — see
[`SKILL.md`](../SKILL.md#abstraction-is-discovered-not-designed).
