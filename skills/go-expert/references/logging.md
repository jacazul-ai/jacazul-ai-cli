# Logging and Output

Owner of: how a package emits logs and program output.

- Follow repository-local output and logging conventions. Do not introduce
  `log`, `slog`, `fmt`, or a new logger abstraction as a cosmetic preference.
- If the project defines a logging interface or output contract, program
  against that contract and keep concrete implementations swappable.
- Plain stdout/stderr may be the local convention for simple CLI output;
  structured logging may be required for services or observability-heavy
  code. Read the local pattern first, then act.
- Log an error once, at the boundary that owns the decision — see
  [errors](errors.md).
- Redact credentials and personal data before they reach a log, an error
  string, or a trace — see [security](security.md).

There is no house logger. The repository's existing choice wins, and switching
it is a project decision, not a style correction.
