# Tests and Validation

Owner of: test shape, seam decisions, mock construction, and process-isolated
tests.

## What to test

Write tests around the contract, not only the happy path:

- invalid input and returned errors;
- cancellation, timeout, retry, and shutdown;
- ownership, aliasing, nil/empty, and serialization behavior;
- concurrent completion, failure propagation, and bounded resources;
- security boundaries and resource cleanup.

For bug fixes or behavior changes, create a failing reproduction test or smoke
check before implementing when practical.

## Test shape

- Prefer table-driven tests when multiple cases exercise the same behavior;
  keep tests readable before making them clever.
- Use `t.Helper()` for helpers that should report caller lines. Use standard
  `testing` tools first; add assertion libraries only when they improve
  clarity and are already accepted by the project.

## Seams and mocks

- Prefer designing testable code over adding mocks: small interfaces,
  explicit dependencies, and simple seams.
- Do not force an interface solely because code shells out to an external
  process. Direct shell-out can be tested through controlled external-process
  resources: temporary filesystem fixtures, environment variables, PATH shims
  or fake executables, local URLs or `httptest.Server`, captured
  stdout/stderr, and controlled exit codes.
- Choose the least artificial reliable boundary for the behavior under test.
  Extract a seam or interface when shell-out logic becomes complex, expensive,
  unsafe, hard to reproduce, or has multiple real consumers — not for
  architectural purity alone.
- When a mock is necessary, prefer a function-field mock struct: function
  fields matching the interface methods, methods implemented by calling those
  fields, behavior and argument capture customized per test. Do not implement
  behavior the test does not care about — a nil panic from an unexpected call
  is useful signal.

A test seam is one of the three conditions that make an abstraction
legitimate; the other two are in
[`SKILL.md`](../SKILL.md#abstraction-is-discovered-not-designed). "I might
need to mock this later" is not one of them.

### Process-isolated tests for initialization-time environment

An environment-guarded helper process is a valid Go standard-library idiom,
not an improvised workaround. Use it when a test must vary an environment
variable before package initialization or one-time setup runs. Changing the
parent process after the package has loaded cannot replay `init` or reset a
`sync.Once` decision.

The standard library uses guards such as `GO_WANT_HELPER_PROCESS` across
multiple packages. For a project-specific case, use a precise guard such as
`GO_WANT_EPOCH_HELPER`, re-execute the current test binary, and select only
the helper test with `-test.run=^TestName$`:

```go
func TestEpochDateInZone(t *testing.T) {
	if os.Getenv("GO_WANT_EPOCH_HELPER") == "1" {
		fmt.Fprintln(os.Stdout, dateFromEpoch(testEpoch))
		return
	}

	for _, zone := range []string{"UTC", "America/New_York", "Asia/Tokyo"} {
		t.Run(zone, func(t *testing.T) {
			exe, err := os.Executable()
			if err != nil {
				t.Fatal(err)
			}

			cmd := exec.Command(exe, "-test.run=^TestEpochDateInZone$")
			cmd.Env = append(
				os.Environ(),
				"GO_WANT_EPOCH_HELPER=1",
				"TZ="+zone,
			)
			out, err := cmd.Output()
			if err != nil {
				t.Fatalf("zone %s: %v", zone, err)
			}
			// The child is a full test binary: after the helper branch
			// returns, the testing package still prints "PASS". Read only
			// the first line; never compare the whole output.
			got, _, _ := strings.Cut(string(out), "\n")
			assertDateForZone(t, zone, got)
		})
	}
}
```

The child output is `<value>\nPASS\n`, not the bare value, because the helper
branch returns into the normal test flow. Parse the line you printed, or match
with a regular expression as the standard library does. Do not call
`os.Exit(0)` inside the test function to suppress `PASS`: since Go 1.15 the
testing package reports that as `panic: unexpected call to os.Exit(0) during
test`. If the helper must exit early, handle the guard in `TestMain` before
`m.Run()`.

This is especially useful for date and timezone tests: each child starts with
a fresh environment, so `TZ=UTC`, `TZ=America/New_York`, and `TZ=Asia/Tokyo`
can exercise the same epoch against different local-date interpretations. The
helper-process pattern is standard-library-backed; applying it specifically to
our timezone/date behavior is a project test design, not a claim that the
stdlib `time` tests use this exact scenario.

Use `os.Executable()` rather than `os.Args[0]`. The public API resolves the
running binary robustly when a test changes its working directory;
`os.Args[0]` may be relative. Invoke the child directly with `exec.Command`,
never through a shell, and make the guard branch terminate before the
parent-only assertions.

**Sources:**

- [Go helper-process test guard][stdlib-helper-process]
- [Go environment test coverage][stdlib-environment-tests]

[stdlib-helper-process]: https://cs.opensource.google/go/go/+/go1.27.0:src/testing/helper_test.go
[stdlib-environment-tests]: https://cs.opensource.google/go/go/+/go1.27.0:src/os/os_test.go

## Gates

Run repository-configured checks first. If no stronger gate exists, apply the
conventional baseline defined once in
[`SKILL.md`](../SKILL.md#-conventional-verification-baseline) and label it as
such. `go test -race`, `staticcheck`, and `govulncheck` are complementary
tools, described in
[`CODE-REVIEW.md`](../CODE-REVIEW.md#automated-review-baseline); they
complement tests and review rather than proving correctness alone.
