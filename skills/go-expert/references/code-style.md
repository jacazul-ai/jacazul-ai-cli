# Control Flow and Readability

Owner of: Line of Sight, nesting, early returns, conditions, declarations,
loop clarity, and where a long line breaks. Identifier choice belongs to
[naming](naming.md); `gofmt` owns everything mechanical, so this reference
only covers what a formatter cannot decide.

## Line of Sight

Mat Ryer's principle: "a straight line along which an observer has
unobstructed vision."

- Keep the happy path aligned to the left; make functions quick to scan.
- Handle failures and edge cases early with guard clauses and early returns;
  keep them in indented blocks and avoid deep nesting.
- Prefer the happy successful return as the last statement when possible.
- Flip conditionals to handle failure first instead of wrapping main logic in
  `if/else`.

```go
func Run() error {
	if err := validate(); err != nil {
		return err
	}

	if !ready() {
		return ErrNotReady
	}

	return execute()
}
```

For functions returning only `error`, return `err` on failure and `nil` on
success unless the function name intentionally models an inverted or negative
condition.

**Reference:** Mat Ryer, Line of Sight concept in
https://www.youtube.com/watch?v=yeetIgNeIkc

- `04:18-06:02`: introduces Line of Sight and keeping the main flow visible.
- `06:05`: prefer the happy return as the final statement when possible.
- `06:20`: flip logic to handle failures first and avoid unnecessary `else`.

## Drop the `else` the `return` already made unnecessary

When the `if` body ends in `return`, `break`, or `continue`, the `else` adds
indentation and nothing else. For an assignment with mutually exclusive
cases, assign the default first and override it:

```go
level := slog.LevelInfo

switch {
case debug:
	level = slog.LevelDebug
case verbose:
	level = slog.LevelWarn
}
```

An `else if` chain hides that there is a default at all; the reader has to
reach the last branch to find it.

## `break`, `continue`, and `fallthrough`

Three keywords read like one thing and do another.

`break` inside a `select` or a `switch` that sits inside a `for` breaks the
`select` or the `switch`, not the loop. The loop keeps going, which is
usually the opposite of what the code says it wants. Use a label when the
loop is the target:

```go
loop:
	for {
		select {
		case <-done:
			break loop // without the label, only the select ends
		case v := <-ch:
			handle(v)
		}
	}
```

`fallthrough` transfers to the next case *unconditionally*: it does not
evaluate that case's expression. It is not C's implicit fallthrough made
explicit, it is a jump, and a case list (`case a, b:`) is what most code
actually wants.

## Conditions

A condition with three or more operands is business logic wearing
punctuation. Name the parts:

```go
isAdmin := user.Role == RoleAdmin
isOwner := resource.OwnerID == user.ID
isPublicToVerified := resource.IsPublic && user.IsVerified

if isAdmin || isOwner || isPublicToVerified {
	allow()
}
```

One exception, and it is about behavior rather than taste: an expensive or
side-effecting check stays inline so short-circuit evaluation can skip it.
Hoisting `expensiveCheck(user)` into a named boolean runs it every time.

Scope a variable to the `if` when the check is all it is for:

```go
if err := validate(input); err != nil {
	return err
}
```

Comparing the same value against several alternatives is a `switch`, not a
chain. A `switch` on a named type also lets the reader see the whole set of
cases at once, and `default` states what happens to the rest.

## Declarations

`var` and `:=` are not interchangeable style — they signal different
intent. `var` says the value starts at its zero value and is set later or
used as-is; `:=` says there is a real value right here.

```go
var count int        // starts at zero, incremented below
var buf bytes.Buffer // zero value is already usable
name := "default"    // a value, not a placeholder
```

An empty slice follows the same rule and is the case people get wrong most
often: prefer `var t []string` over `t := []string{}`. Both have length and
capacity zero and both append correctly; the first is the preferred style,
and the second only earns its place where a non-nil zero-length value is
part of a contract — see [data-structures](data-structures.md).

`:=` also declares, which is how shadowing happens. Inside a new block,
`:=` creates a *different* variable with the same name, and the assignment
the author meant to make to the outer one silently does not happen:

```go
var err error

if cond {
	result, err := compute() // new err, shadows the outer one
	use(result)
}
// the outer err is still nil here
```

**Diagnose:** `go vet -vettool=$(which shadow)` with the `shadow` analyzer
from `x/tools`; it is not part of the default `go vet` set.

Composite literals take field names. A positional literal compiles fine
today and silently means something else the moment the type gains or
reorders a field:

```go
srv := &http.Server{
	Addr:        ":8080",
	ReadTimeout: 5 * time.Second,
}
```

**Diagnose:** `go vet ./...` — `composites` flags positional literals for
types from other packages.

## Breaking long lines

There is no column limit in Go, and `gofmt` will not break a line for you.
Past roughly 120 characters, break at a semantic boundary — one argument,
one parameter, or one condition per line — never at whatever column the
editor happened to reach.

When a signature needs that treatment, ask first whether the real problem
is the number of parameters. Wrapping six arguments prettily still leaves
six arguments.

## Loops, ordering, and conversions

- Make loop bounds, mutation, ownership, and ordering explicit.
- Do not depend on map iteration order. Sort keys when order is part of output
  or behavior.
- Remember that a `range` value is a copy when mutating slice, array, or map
  elements; use an index or deliberate pointer ownership when needed. See
  [values](values.md) for the ownership rules behind this.
- Prefer `range` over an index-based loop unless the index itself is used;
  `for range n` (Go 1.22+) covers plain counting.
- Treat numeric conversions as validation boundaries. What has to be checked
  — range, sign, unit, precision — belongs to [numbers](numbers.md).

## Function shape

Function scope is decided by contract, not by length — the rule lives in
[`SKILL.md`](../SKILL.md#function-scope-is-contract-not-size). Extracting a
single-call helper purely to shorten a body breaks Line of Sight and buys
nothing.

Parameter order is conventional and worth keeping: `context.Context` first,
then inputs, then any destination the function writes into.

A long parameter list is a signal, not a violation. Four is about where
call sites stop being readable and positional mistakes start compiling; an
options struct is the usual answer, but only once the list is stable —
introducing one for a function that still has three parameters is the
speculative structure [`SKILL.md`](../SKILL.md#abstraction-is-discovered-not-designed)
rejects.

Naked returns are readable in a function short enough to see whole. Past
that, the reader has to scroll back to find what `return` actually returns,
so name the values explicitly.
