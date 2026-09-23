# Doc Comments (Go 1.19+)

Owner of: doc comment formatting and the rendered-output validation gate.

Write doc comments for rendered output, not just source readability. `go doc`
and pkg.go.dev apply formatting rules that can turn a comment into a clean
overview or a useless wall of text depending on spacing and indentation.

- **Package doc:** Place the package comment immediately above
  `package <name>` with no blank line between them, or it will not be
  recognized as the package documentation.
- **Code blocks:** A line indented with a tab or at least four spaces relative
  to the comment text renders as a code block. Use this for examples.
- **Lists:** A line starting with `-`, `*`, `+`, or a number renders as a list
  item. Continuation lines must stay aligned, or the rendered list breaks.
- **Headings:** A line starting with `# ` renders as a heading. Use headings
  sparingly in package docs and only when the overview is long enough to need
  structure.
- **Exported identifier convention:** Doc comments for exported identifiers
  should start with the identifier name (`// Foo does X`). Follow standard Go
  documentation conventions so tooling and reviewers do not treat the comment
  as malformed.

## Say why, not what

A comment that restates the signature costs a line and earns nothing:
`// GetUser gets a user` tells the reader what they already read. Document
what the caller cannot see — the contract, the units, the ownership of what
is returned, what happens on failure, and the limitation that will surprise
them.

The same applies inside a function. A comment explaining *what* a
well-named statement does is a sign the statement should be renamed
instead; a comment explaining *why* a surprising line exists is the one
that survives.

## Markers the tooling actually reads

Some comment text is not prose — `go doc`, `gopls`, `pkg.go.dev` and the
linters act on it.

- **`// Deprecated: ...`** must be its own paragraph, and everything that
  understands Go doc comments will mark the symbol and suggest the
  replacement. Say what to use instead; a deprecation with no successor
  only tells people they are stuck.
- **Doc links** (Go 1.19+) connect symbols: `[Reader]`, `[io.Writer]`,
  `[Buffer.Len]`. Writing the name in backticks instead produces plain
  text, so the reader has to search for it.
- **Directives** such as `//go:generate` and `//go:embed` have no space
  after the slashes and are excluded from the rendered documentation. A
  directive placed inside a doc comment disappears from the docs and keeps
  working, which is exactly the wrong way round to discover a mistake.

## Documenting an interface

Document what an implementation must guarantee, not what the current
implementation happens to do: the contract is the thing other people
implement against. Say whether a method may block, whether it is safe for
concurrent use, and what it does with a nil argument — none of which the
signature can express.

**Validation gate:** Before considering documentation done, run
`go doc ./<package>` or `go doc <package>.<Symbol>` and inspect the rendered
output. A comment that looks fine in source may still render as a run-on
paragraph, broken list, or malformed example block.

A doc comment describes a contract, so it ages with the exported API it
documents — see [packages](packages.md).


## Scope

This reference owns doc comments — the documentation the Go toolchain
renders. README, CONTRIBUTING, changelog and delivery documentation are
repository concerns, not language ones; in this project they are governed
by the Documentation Mandate in `AGENTS.md` and its documentation map.
