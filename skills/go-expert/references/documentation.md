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

**Validation gate:** Before considering documentation done, run
`go doc ./<package>` or `go doc <package>.<Symbol>` and inspect the rendered
output. A comment that looks fine in source may still render as a run-on
paragraph, broken list, or malformed example block.

A doc comment describes a contract, so it ages with the exported API it
documents — see [packages](packages.md).
