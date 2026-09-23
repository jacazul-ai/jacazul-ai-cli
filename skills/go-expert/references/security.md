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
| SSRF | a `net.Dialer` whose `Control` checks the resolved address |
| Timing leaks | `crypto/subtle.ConstantTimeCompare`, `hmac.Equal` |
| Weak randomness | `crypto/rand` for anything security-bearing |
| Password storage | a slow, salted KDF — never a bare hash |
| Transport downgrade | `tls.Config` with an explicit `MinVersion` |
| Oversized input | `http.MaxBytesReader`, server timeouts, bounded decompression |

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

`os.Root` is a traversal guard, not a sandbox. Its own documentation says
it does not stop bind mounts, `/proc` special files, or Unix device files,
and that `Chmod`, `Chown` and `Chtimes` race against a swap to a symlink on
Unix. Choose a root the attacker cannot mount into.

Archive extraction is the same bug with a different source: every entry
name in a zip or tar is attacker-chosen, and `filepath.Join(dest, name)`
with `../` in the name writes outside `dest`. Open each entry through an
`os.Root` over the destination, and refuse entries that are symlinks or
devices rather than trying to reproduce them.

Two smaller file mistakes keep recurring. A temporary file with a
predictable name is a race another process can win — `os.CreateTemp`
chooses the name and creates the file in one step. And the mode argument is
the policy: `0o600` for anything holding a secret, never `0o666` or
`0o777` in the hope that the umask narrows it.

## Injection

Pass subprocess arguments directly. `exec.Command("sh", "-c", userInput)`
is the vulnerability, not the shell itself; `exec.Command(bin, arg1, arg2)`
never parses a string.

Placeholders bind values, never identifiers. A column in `ORDER BY`, a
table name or a sort direction cannot be a `$1`, so the tempting fix is
`fmt.Sprintf` — which reopens the hole. Map the user's choice through a
fixed allowlist to a constant string, and interpolate only that. A dynamic
`IN (...)` is the other case: generate one placeholder per value and pass
the values as arguments, never join them into the query.

Server-side request forgery is not solved by parsing the URL. Checking the
host name before the request loses to a name that resolves to
`169.254.169.254` or `127.0.0.1`, or to one that resolves differently the
second time. Check the address that is actually dialed, in the `Control`
hook of the `net.Dialer` behind the client's transport, and refuse
loopback, private, link-local and unspecified ranges there — `netip.Addr`
has a predicate for each. Redirects are followed by the same client, so the
check has to live in the dialer, not in the handler.

An open redirect is the same trust mistake pointed at users:
`http.Redirect` to a URL taken from the query string. Accept a relative
path or an allowlisted host, nothing else.

`html/template` escapes according to where a value lands — HTML body,
attribute, URL, JavaScript — which `text/template` does not do at all.
Using `text/template` for HTML, or casting to `template.HTML` to silence
an escaping problem, throws that away. The cast says "I have already
proven this is safe", so it needs to be true.

## Cryptography

Use vetted constructions and do not assemble your own. The recurring Go
mistakes are narrow and specific:

- comparing secrets, tokens or MACs with `==`, which returns early and
  leaks length and prefix through timing. Use `hmac.Equal` for MACs and
  `crypto/subtle.ConstantTimeCompare` for the rest — and know that the
  latter returns immediately when the lengths differ, so it hides content,
  not length. Compare fixed-length digests when the length is the secret.
- reusing a nonce with AES-GCM. A nonce must never repeat under the same
  key, and generating it with `crypto/rand` per message is the simple
  correct answer.
- `math/rand` anywhere a value must be unguessable — tokens, nonces,
  session identifiers, password resets.
- calling `cipher.Block.Encrypt` in a loop, which is ECB: identical
  plaintext blocks produce identical ciphertext. A `Block` is a primitive;
  wrap it in `cipher.NewGCM`.
- storing a password as `sha256.Sum256(password)`. A fast hash is the wrong
  tool — it is built to be cheap to compute, and so is brute-forcing it.
  Use a deliberately slow, salted function: Argon2id or bcrypt from
  `golang.org/x/crypto`, or `crypto/pbkdf2` (Go 1.24+) with a high
  iteration count.

`crypto/md5`, `crypto/sha1`, `crypto/des` and `crypto/rc4` exist for
interoperability with formats that already use them. Their presence in new
code is a finding unless the format forces them.

## Transport

Never set `InsecureSkipVerify: true` outside a test, and never as a way to
make a certificate error go away; it disables the check that the peer is
who it claims to be. `ssh.InsecureIgnoreHostKey` in `golang.org/x/crypto`
is the same mistake for SSH. Set `MinVersion` explicitly rather than
inheriting a default that changes between releases.

## Resource limits

A server with no timeouts can be held open by a client that sends one byte
a minute. `http.ListenAndServe` sets none, so build the `http.Server`:
`ReadHeaderTimeout` is the one that defeats a slow header trickle while
leaving the handler free to decide how long a body may take;
`ReadTimeout`, `WriteTimeout` and `IdleTimeout` bound the rest. The
deadline rules for the work inside are in [context](context.md).

Bound what is read, not only how long:

- `http.MaxBytesReader` on a request body returns an error past the limit.
  `io.LimitReader` returns a plain `io.EOF` instead, so a decoder reading
  from it sees a truncated but apparently complete input.
- A decompressor is an amplifier: a few kilobytes of gzip can expand to
  gigabytes. Limit the decompressed stream, and treat hitting the limit as
  an error rather than an end.
- A size computed from input — `rows * cols`, a length prefix — is checked
  before it reaches `make`. The overflow rules are in
  [numbers](numbers.md).
- `encoding/gob` states that it is not hardened against adversarial input.
  Decode untrusted data with a format that is, and validate the result.

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
