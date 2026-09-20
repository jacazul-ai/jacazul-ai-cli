# Structs and Interfaces

Owner of: type shape — zero values, receivers, embedding, copy safety, type
assertions, and compile-time interface checks. Identifier choice belongs to
[naming](naming.md); whether an abstraction is warranted at all is decided in
[`SKILL.md`](../SKILL.md#abstraction-is-discovered-not-designed).

## Make the zero value useful

Design structs so they work without explicit initialization. A useful zero
value removes constructor boilerplate and a whole class of nil bugs.

```go
// Ready to use, no constructor
var buf bytes.Buffer
buf.WriteString("hello")

var mu sync.Mutex
mu.Lock()
```

When a field cannot have a working zero value, guard it rather than forcing a
constructor on every caller:

```go
func (r *Registry) Register(name string, item Item) {
	if r.items == nil {
		r.items = make(map[string]Item)
	}
	r.items[name] = item
}
```

A nil map panics on write but reads fine, so the asymmetry is easy to miss —
see [values](values.md) for the nil-versus-empty decision at a boundary.

## Pointer vs value receivers

| Pointer `(s *Server)` | Value `(s Server)` |
| --- | --- |
| The method modifies the receiver | The receiver is small and immutable |
| The receiver holds a `sync.Mutex` or similar | The receiver is a basic type |
| The receiver is a large struct | The method is a read-only accessor |

Keep the receiver type consistent across all methods of a type. A type with
mixed receivers satisfies interfaces only through one of its two method sets,
which surfaces as a confusing compile error far from the cause.

## Nil receivers and nil function fields

A method on a pointer receiver does not panic because the receiver is nil.
It panics when the body dereferences it, which means the same type can have
one method that survives a nil receiver and another that does not:

```go
func (l *Logger) Enabled() bool { return l != nil } // fine on nil
func (l *Logger) Log(msg string) {                  // panics on nil
	fmt.Printf("[%s] %s\n", l.prefix, msg)
}
```

That asymmetry is a trap, not a feature. Treat a nil receiver as a bug
unless the type documents nil as a valid state — an optional dependency is
the usual legitimate case — and guard it explicitly when it is:

```go
func (l *Logger) Log(msg string) {
	if l == nil {
		return
	}
	...
}
```

A nil function field has the same shape with no escape: calling it always
panics. Either check before calling, or install a no-op default at
construction so no call site has to remember:

```go
w := &Worker{onDone: func(string) {}}
```

Between the two, the default is usually better — it puts the decision in
one place instead of at every call site.

## Copy safety

A struct holding a mutex, a channel, or internal pointers breaks when copied:
the copy duplicates the lock state, so two goroutines guard two different
mutexes and the invariant disappears silently.

Embed a `noCopy` sentinel so `go vet` reports every value copy, and pass such
structs by pointer.

**Diagnose:** `go vet ./...` — `copylocks` reports value copies of
lock-bearing structs.

## Embedding

Embedding promotes the inner type's methods and fields to the outer type. It
is composition, not inheritance — the receiver of a promoted method is the
*inner* type, and the outer type overrides by declaring its own method of the
same name.

| Use | When |
| --- | --- |
| Embed | The outer type should expose the full API of the inner one |
| Named field | The inner type is an internal dependency, not part of the API |

Embedding to inherit behavior is the Java shape this skill rejects. Embed to
promote an API deliberately, not to avoid writing a field name.

## Type assertions and switches

Use the comma-ok form. The single-value form panics on mismatch instead of
branching:

```go
s, ok := val.(string)
```

Assert to a small optional interface to exploit a richer implementation
without widening the declared parameter type:

```go
if f, ok := w.(Flusher); ok {
	f.Flush()
}
```

## Compile-time interface checks

Verify a type satisfies an interface at compile time, next to the type
definition. It costs nothing at runtime, and the build fails the moment the
type stops satisfying it.

```go
var _ io.ReadWriter = (*MyBuffer)(nil)
```

## `any` and generics

Prefer a concrete type. When several real instantiations exist, a generic with
the tightest useful constraint beats `any`, which discards type safety and
pushes the error to runtime.

Reach for `any` only at a genuine boundary where the type is unknowable —
JSON decoding, reflection, a plugin edge.

A generic parameter added for a single caller is the same speculative
structure as an interface with one implementation. It earns its place under
the rules in [`SKILL.md`](../SKILL.md#abstraction-is-discovered-not-designed).

## Make illegal states unrepresentable

Use the type system to prevent invalid states from being expressible:

```go
// Anything goes
type Order struct {
	Status string
}

// The compiler constrains the values
type OrderStatus int
```

This is a type-system idiom, not architecture. A named type that removes a
class of invalid values earns its existence; one that only renames a `string`
does not — see [naming](naming.md).
