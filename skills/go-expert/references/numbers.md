# Numbers: Range, Precision, and Division

Owner of: integer range and truncation, floating-point comparison, division
guards, and unit-carrying numeric types. Where a conversion sits in the
control flow belongs to [code-style](code-style.md); which values must be
validated on the way in belongs to [packages](packages.md).

Go has no implicit numeric conversion, so every conversion is deliberate.
That is the language being honest — and it is also why an out-of-range
conversion is a silent wraparound rather than an error.

## Conversion truncates in silence

A constant that does not fit is a compile error. A *variable* that does not
fit wraps:

```go
var total int64 = 3_000_000_000
count := int32(total) // -1294967296, no panic, no error
```

Check the range before narrowing a value the compiler cannot see:

```go
if total > math.MaxInt32 || total < math.MinInt32 {
	return 0, fmt.Errorf("count %d overflows int32", total)
}
```

Signed to unsigned is the same trap with a friendlier face: a negative value
becomes a very large one, which then passes every `> 0` guard downstream.

When the number arrives as text, let `strconv` enforce the width instead of
parsing wide and narrowing afterwards:

```go
// Range error at the boundary, not a wrapped value three layers in.
n, err := strconv.ParseInt(raw, 10, 32)
```

Treat a conversion as a validation boundary: range, sign, unit, and
precision. Once past it, internal code trusts the value — the same
validate-once rule as [packages](packages.md).

## Floating point is not exact

`0.1 + 0.2 == 0.3` is false, and no amount of rounding in the printer
changes that. Compare with a tolerance:

```go
const epsilon = 1e-9

if math.Abs(got-want) < epsilon {
	// close enough
}
```

An absolute epsilon is only honest when the magnitudes are known and near
each other. Across a wide range, scale the tolerance to the operands
(`math.Abs(a-b) <= epsilon*math.Max(math.Abs(a), math.Abs(b))`), or compare
in the unit the domain actually cares about.

Money is not a float. Use integer minor units — cents, satoshis, basis
points — or a decimal type. A currency amount that drifts by 1e-15 per
operation is a reconciliation bug waiting for the end of the month.

`NaN` is not equal to itself, so `x == x` is false for `NaN` and a `NaN`
key can be inserted into a map and never found again. Test with
`math.IsNaN`, and use `cmp.Compare` (Go 1.21+) when ordering floats that
may contain one.

## Division

| Expression | Result |
| --- | --- |
| `n / 0` on integers | panic: integer divide by zero |
| `f / 0` on floats | `+Inf`, `-Inf`, or `NaN` for `0/0` |
| `math.MinInt64 / -1` | `math.MinInt64` — two's-complement overflow, no panic |

Guard the divisor whenever it comes from data rather than from a literal:

```go
func mean(total, count int) (int, error) {
	if count == 0 {
		return 0, errors.New("mean of an empty set")
	}

	return total / count, nil
}
```

Integer division truncates toward zero and the remainder takes the sign of
the dividend: `-7 / 2` is `-3` and `-7 % 2` is `-1`. When the domain wants
floor division — bucketing, pagination, time slots — say so explicitly
rather than assuming `/` rounds the way the arithmetic class did.

## Units belong in the type

A number whose unit lives only in a variable name is one refactor away from
being wrong. `time.Duration` is the standard-library example, and it also
carries the most common unit bug in Go:

```go
var n int // seconds, read from configuration

timeout := time.Duration(n) * time.Second
```

Writing `n * time.Second` does not compile — mismatched types `int` and
`time.Duration` — and that error is the type system doing its job. The trap
is silencing it with `time.Duration(n)` alone: that compiles, and it means
n *nanoseconds*, which is exactly the bug the error was preventing.

Declaring `type Celsius float64` or `type Bytes int64` costs nothing at
runtime and makes the mismatched addition a compile error — see
[naming](naming.md) for when a named type earns its existence, and
[structs-interfaces](structs-interfaces.md) for making illegal states
unrepresentable with the same tool.
