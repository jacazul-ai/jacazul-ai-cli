# Security Boundary

Owner of: the Go-specific attack surface — hostile input, injection,
untrusted paths, cryptographic API misuse, transport configuration, and the
escape hatches that bypass Go's guarantees.

## What belongs here and what does not

This reference covers mistakes you make *in Go code*, with a standard
library answer. Threat modelling, secret storage and rotation, dependency
vetting, CI permissions and supply-chain review belong to the
`security-expert` skill; naming it here is a routing note, not an
activation — this skill never loads another.

Treat external input as hostile by default: validate size, shape, encoding
and allowed values at the boundary it enters, then trust it inside — the
validate-once rule is in [packages](packages.md).

## The surface, and the standard library answer

| Risk | Answer |
| --- | --- |
| SQL injection | Placeholders through `database/sql`; never concatenate |
| Command injection | `exec.Command` with separate arguments; never build a shell string |
| XSS | `html/template`, which escapes by context |
| Path traversal | `os.Root` (Go 1.24+) to scope access to one tree |
| Timing leaks | `crypto/subtle.ConstantTimeCompare` |
| Weak randomness | `crypto/rand` for anything security-bearing |
| Transport downgrade | `tls.Config` with an explicit `MinVersion` |

## Untrusted paths

`filepath.Clean` followed by `strings.HasPrefix` is the classic broken
check: cleaning resolves `..` but the prefix test is a string comparison,
so `/safe-evil` passes a prefix test for `/safe`, and a symlink inside the
tree escapes it entirely.

`os.Root` (Go 1.24+) is the real fix — it opens a directory and refuses
every operation that would leave it, symlinks included:

```go
root, err := os.OpenRoot(baseDir)
if err != nil {
	return err
}
defer root.Close()

f, err := root.Open(untrustedName) // cannot escape baseDir
```

Before Go 1.24, combine `filepath.IsLocal` with a separator-aware check
rather than a prefix test, and remember it is lexical: it cannot see a
symlink. Confirm the `go` directive before relying on `os.Root` — see
[runtime](runtime.md).

## Injection

Pass subprocess arguments directly. `exec.Command("sh", "-c", userInput)`
is the vulnerability, not the shell itself; `exec.Command(bin, arg1, arg2)`
never parses a string.

`html/template` escapes according to where a value lands — HTML body,
attribute, URL, JavaScript — which `text/template` does not do at all.
Using `text/template` for HTML, or casting to `template.HTML` to silence
an escaping problem, throws that away. The cast says "I have already
proven this is safe", so it needs to be true.

## Cryptography

Use vetted constructions and do not assemble your own. The recurring Go
mistakes are narrow and specific:

- comparing secrets, tokens or MACs with `==`, which returns early and
  leaks length and prefix through timing. Use
  `crypto/subtle.ConstantTimeCompare`.
- reusing a nonce with AES-GCM. A nonce must never repeat under the same
  key, and generating it with `crypto/rand` per message is the simple
  correct answer.
- `math/rand` anywhere a value must be unguessable — tokens, nonces,
  session identifiers, password resets.

## Transport

Never set `InsecureSkipVerify: true` outside a test, and never as a way to
make a certificate error go away; it disables the check that the peer is
who it claims to be. Set `MinVersion` explicitly rather than inheriting a
default that changes between releases, and give every server its timeouts —
an unbounded read is a resource exhaustion vector as much as a bug, and the
deadline rules are in [context](context.md).

Redact credentials and personal data before they reach a log, an error
string or a trace — see [logging](logging.md) and [errors](errors.md), since
an error that carries a token propagates it everywhere the error goes.

## unsafe, reflection, and cgo

Do not introduce `unsafe`, reflection, or cgo to bypass a design problem. If
one is required, isolate it behind a small boundary and document lifetime,
alignment, aliasing, layout, and foreign-memory ownership invariants.

`unsafe` removes memory safety, which is the guarantee the rest of this
reference assumes — see [data-structures](data-structures.md) for the
pointer rules it must follow.

**Diagnose:** `govulncheck` reports known vulnerabilities reachable from
your code, which is narrower and more useful than a dependency list. It is
a project mandate only when the repository configures it.
