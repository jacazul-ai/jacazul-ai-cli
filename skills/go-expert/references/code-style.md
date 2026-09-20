# Control Flow and Readability

Owner of: Line of Sight, nesting, early returns, loop and conversion clarity.

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

## Loops, ordering, and conversions

- Make loop bounds, mutation, ownership, and ordering explicit.
- Do not depend on map iteration order. Sort keys when order is part of output
  or behavior.
- Remember that a `range` value is a copy when mutating slice, array, or map
  elements; use an index or deliberate pointer ownership when needed. See
  [values](values.md) for the ownership rules behind this.
- Treat numeric conversions as validation boundaries: check range, sign, unit,
  and precision before converting external or calculated values.

## Function shape

Function scope is decided by contract, not by length — the rule lives in
[`SKILL.md`](../SKILL.md#function-scope-is-contract-not-size). Extracting a
single-call helper purely to shorten a body breaks Line of Sight and buys
nothing.
