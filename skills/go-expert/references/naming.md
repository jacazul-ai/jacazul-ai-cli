# Naming

Owner of: identifier choice across the language — case, stuttering,
receivers, constructors, error names, variant suffixes, and the
Java-shaped anti-patterns. Package naming lives in [packages](packages.md);
the shape of the code around the name belongs to
[code-style](code-style.md).

A Go name is read at the call site, with the package qualifier attached.
That single fact explains most of the conventions below.

## MixedCaps, and why it is not cosmetic

Go identifiers use `MixedCaps` or `mixedCaps`. Underscores appear only in
test subcase names, generated code, and OS or cgo interop.

```go
MaxPacketSize     // exported
userCount         // unexported
parseHTTPResponse

MAX_PACKET_SIZE   // C habit
max_packet_size   // Python habit
kMaxBufferSize    // Hungarian habit
```

This is load-bearing rather than aesthetic: the case of the first letter
*is* the export mechanism, so a naming scheme that fights capitalization
fights the language.

## Do not stutter

The package name is already at the call site. Repeating it makes the
reader parse the same word twice.

```go
http.Client       // not http.HTTPClient
json.Decoder      // not json.JSONDecoder
user.New()        // not user.NewUser()
config.Parse()    // not config.ParseConfig()
```

It applies to every exported name in the package, not only the main type.
In package `dbpool`, callers write `dbpool.Status` and `dbpool.Option`, so
`PoolStatus` and `PoolOption` stutter just as `DBPool` does.

## Constructors

A package exporting one primary type names its constructor `New`, because
`apiclient.New()` already says what it builds. `NewTypeName` is for
packages that construct several types, as `http.NewRequest` and
`http.NewServeMux` do.

## Receivers

One or two letters, derived from the type, and the same letters on every
method of that type: `func (s *Server)`, `func (b *Buffer)`. A receiver is
not a place to be descriptive — it appears in every method and the type is
right there in the signature. Do not name it `this` or `self`.

Whether it is a pointer or a value is a different question, decided in
[structs-interfaces](structs-interfaces.md).

## Acronyms keep one case

An acronym is all upper or all lower, never mixed: `URL`, `ServeHTTP`,
`xmlParser`, `userID`. `Url` and `Http` look like typos to a Go reader
because the standard library never writes them that way.

## Errors

- Sentinel values take an `Err` prefix: `ErrNotFound`, `ErrTimeout`.
- Error *types* take an `Error` suffix: `PathError`, `SyntaxError`.
- Error strings start lowercase and carry no trailing punctuation, because
  they are almost always wrapped into a longer sentence:
  `fmt.Errorf("parsing token: %w", err)`. A capital letter or a full stop
  lands in the middle of that sentence.

Give the string enough context to be read on its own once wrapped. A
package prefix (`"apiclient: not found"`) is one way to do that, not a
rule — the standard library is not consistent about it, and `os.ErrNotExist`
carries none.

What an error *promises its caller* is decided in [errors](errors.md); this
is only what it is called.

## Booleans read as predicates

A boolean should read as a question at the point of use. Methods usually
carry the question word — `IsDir`, `IsValid`, `HasPrefix` — and that is
worth following.

For fields, the honest version is weaker than the rule often quoted: the
standard library is full of bare adjectives (`InsecureSkipVerify`,
`DisableKeepAlives`) and they read fine. Prefer a name that cannot be
mistaken for a non-boolean; a prefix is one way to get there, not a
requirement.

## Variant names the standard library established

| Form | Meaning | Example |
| --- | --- | --- |
| `Must` prefix | Panics instead of returning an error; for package init | `regexp.MustCompile` |
| `f` suffix | Takes a format string | `fmt.Errorf`, `log.Printf` |
| `Context` suffix | The variant that takes a `context.Context` | `db.QueryContext` |
| `With` prefix | Returns a derived value | `context.WithTimeout` |

Reach for these only when the behavior matches. A `MustDoThing` that does
not panic, or a `WithThing` that mutates, is worse than an unfamiliar name.

## Import aliases

Alias only to resolve a collision, and keep it short and obvious:
`mrand "math/rand"` beside `crypto/rand`. An alias that merely shortens a
name removes the reader's ability to find the package.

## Types, structs, and interfaces

Go has no classes — use Go terminology: **types**, **structs**, and
**interfaces**.

- Name concrete types by domain role or real responsibility. `Manager`,
  `Service`, `Processor`, and `Helper` are suspect unless they describe a
  real domain concept; avoid inheritance-shaped `BaseThing` /
  `AbstractThing`.
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
combinations would otherwise be easy to construct. A named type that makes
an illegal state unrepresentable earns its existence; one that only renames
a `string` does not.

An interface that does not yet have a consumer is not a naming problem, it
is a premature abstraction — see
[`SKILL.md`](../SKILL.md#abstraction-is-discovered-not-designed).

**Sources:** [Effective Go](https://go.dev/doc/effective_go#names) and the
naming sections of [Go Code Review Comments][cr].

[cr]: https://go.dev/wiki/CodeReviewComments
