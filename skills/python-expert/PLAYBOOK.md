# Python Engineering Playbook

Implementation guidance for writing clear, typed, testable, and secure
Python. This file answers **how to build the change** in each of the three
modes the skill recognizes. Scenario-based review directives live separately
in [`CODE-REVIEW.md`](CODE-REVIEW.md).

These are defaults, not automatic repository policy. Read `pyproject.toml`,
`setup.cfg`, `tox.ini`, CI, and the package layout before adopting an
optional gate or changing an established contract.

## Before writing code

1. Run `py-mode <path>` (or read the archaeology markers by hand) and name
   the mode: legacy, greenfield, or migration. The mode decides how much of
   this playbook applies.
2. Read the interpreter floor (`requires-python`, `python_requires`,
   `.python-version`) and never use syntax above it.
3. Read the target package and its tests before introducing an abstraction.
4. Define the contract: valid input, absence (`None` versus missing), errors,
   timeouts, retries, partial success, ownership of mutable objects, and
   cleanup.
5. Identify trust boundaries: users, network payloads, files, subprocesses,
   deserialization, environment variables, and logs.

## Mode: greenfield

Apply the modern baseline in full.

- Python 3.13+ unless the project floor says otherwise.
- `pyproject.toml` with a `[project]` table, a declared build backend, and a
  committed lockfile when the project is an application.
- `src/` layout for libraries; flat layout is acceptable for small tools when
  the repository already uses it.
- Type hints on every public function and method; `mypy` or `pyright`
  configured as evidence, not as a hard gate unless the project says so.
- `ruff` as formatter and linter with configuration in `pyproject.toml`.
- `pytest` or `unittest` per project choice; do not mix conventions inside
  one suite.
- `pathlib.Path` for paths, `datetime` with explicit `tzinfo`, `logging` or
  the project's logger, `subprocess.run` with argument lists.

## Mode: legacy

Preserve behavior. The job is the fix or the feature, not the modernization.

- Do not reformat files you did not need to touch. Run `py-check --check`
  (or set `JACAZUL_PY_IGNORE_FORMATTING=1`) so the house formatter does not
  rewrite a tree that has its own conventions.
- Match the local style: string formatting, import order, naming, test
  runner, and exception patterns. A modern idiom in one function among a
  hundred legacy ones is noise, not progress.
- Do not add type hints, dataclasses, `pathlib`, or f-strings to code you are
  not changing. Add them inside the function you are already editing only
  when the interpreter floor allows it and the surrounding code will not
  look foreign.
- Do not introduce `ruff`, `pytest`, `pyproject.toml`, or a lockfile as a
  side effect. Propose them as a migration plan instead.
- Keep Python 2 compatibility shims (`six`, `__future__`) in place until a
  migration step removes them deliberately.
- Add a regression test in the project's existing runner before fixing a
  bug; the test proves the old behavior you must keep.

## Mode: migration (legacy to current)

Migration is a sequence of separate commits, each with the suite passing
before and after. Do not combine steps. Suggested order; the project decides
the actual one:

1. **Interpreter floor.** Establish the lowest interpreter the project must
   support and record it (`requires-python` or `python_requires`). Remove
   Python 2 shims only when the floor is 3.x everywhere the code runs.
2. **Packaging metadata.** Introduce `pyproject.toml` alongside `setup.py`
   or `setup.cfg`, move metadata, keep the old file until the build is
   proven, then delete it in its own commit.
3. **Formatter adoption.** One commit that only reformats, with the
   formatter configuration added in the same commit and no logic changes.
   Add it to `.git-blame-ignore-revs`. Line length follows the project's
   existing convention unless the project chooses the house 79.
4. **Linter adoption.** Enable `ruff` with the rule set the project already
   satisfies, then widen rules in later commits, each fixing one rule
   family.
5. **Typing at boundaries.** Annotate public entry points, I/O boundaries,
   and data models first. Introduce `mypy`/`pyright` in non-strict mode;
   raise strictness per package.
6. **Test runner transition.** Run the existing `unittest` suite under
   `pytest` (it collects `unittest` cases) before rewriting any test.
   Rewrite tests only when you touch the code they cover.
7. **Dependency modernization.** Replace `requirements.txt` pinning with a
   lockfile, upgrade one dependency family per commit, and run the suite
   after each.
8. **Idiom sweep.** `pathlib`, f-strings, dataclasses, context managers,
   `subprocess.run`, `logging`. Per package, per commit, with the suite
   green.

A migration step that changes behavior is a bug, not a step. Revert it.

## Packaging and environment

- Declare the interpreter floor and the build backend; never rely on the
  developer's global interpreter.
- Use `venv` or `uv` per project; do not install into system Python.
- Applications commit a lockfile; libraries declare ranges and test the
  extremes.
- Console scripts go through `[project.scripts]` (or the legacy equivalent),
  not through copied files under `scripts/`.
- Namespace packages are deliberate; an accidental missing `__init__.py`
  changes import semantics.

## Typing as a contract

- Annotate public functions, methods, and module-level constants. Private
  helpers may rely on inference when the types are obvious.
- Prefer builtins (`list[str]`, `dict[str, int]`, `X | None`) on 3.10+;
  use `typing` names only for what builtins lack (`Protocol`, `TypedDict`,
  `Literal`, `TypeVar`, `Callable`).
- `Any` is a proof obligation: write why the type is unknown, and narrow it
  at the first opportunity.
- Validate at boundaries. A type hint does not check runtime data; parse
  external input into a typed structure (`dataclass`, `TypedDict` with a
  validator, or the project's model library) before using it.
- `Protocol` for structural interfaces near the consumer; do not create
  abstract base classes before there are two implementations.
- Treat type-checker output as evidence. A clean run proves consistency, not
  correctness.

## Errors and failure contracts

- Raise specific exceptions; catch specific exceptions. `except Exception`
  is acceptable only at a process boundary that logs and re-raises or
  converts to an exit code.
- Never `except: pass`. If ignoring is correct, catch the specific type and
  write the reason.
- Chain causes: `raise NewError(...) from err`. Use `from None` only to hide
  an implementation detail deliberately.
- Cleanup goes in `finally` or a context manager, never after a `return` in
  the happy path.
- CLI entry points return exit codes; they do not `sys.exit` from deep inside
  library code.
- Log once at the boundary that owns the decision; do not log and re-raise
  at every layer.

## Control flow and readability

- Keep the happy path visible: guard clauses and early returns for invalid
  input, no `else` after `return`.
- Avoid mutable default arguments (`def f(items=[])`); use `None` and create
  inside.
- Do not mutate a collection while iterating it; build a new one or iterate
  over a copy.
- Comprehensions for transformation, loops for side effects.
- `is None`, `is True`; never `== None`.
- Keep functions short enough that their tests are obvious.

## Concurrency and lifecycle

- `asyncio`: every task has an owner; keep a reference to the task or use a
  `TaskGroup` (3.11+); handle `CancelledError` by cleaning up and re-raising.
- Never call blocking I/O or CPU-heavy code inside a coroutine; use
  `asyncio.to_thread` or a process pool.
- Threads share memory under the GIL; CPU-bound work needs processes, I/O-
  bound work can use threads or `asyncio`. Say which you chose and why.
- `subprocess.run` with a list of arguments, `check=True` when failure is an
  error, and a `timeout` for anything external. Never `shell=True` with
  external input.
- Register signal handling at the process boundary and make shutdown
  idempotent.

## Data boundaries

- Use `orjson` where the project mandates it; otherwise the standard
  `json`. Never `pickle` untrusted input.
- `yaml.safe_load`, never `yaml.load` without a safe loader.
- Open files with an explicit `encoding`; treat bytes and text as different
  types.
- Build paths with `pathlib`; validate that user-supplied components stay
  under the intended root (`resolve()` and `is_relative_to`).
- `tempfile.NamedTemporaryFile` / `mkstemp` instead of predictable names in
  `/tmp`.

## Security boundary

Treat external input as hostile by default:

- no `eval`, `exec`, or `compile` on external data; no `shell=True` with
  user input; no `os.system`;
- deserialization only through safe loaders; size and depth limits on
  parsers;
- secrets from the environment or a vault, never from the repository or
  logs; redact them in errors and tracebacks;
- `secrets` for tokens and passwords, `random` only for non-security use;
- `pip-audit` (or the project's scanner) when dependency or release risk is
  in scope; review `setup.py` and build hooks of new dependencies as code
  that runs on install.

## Tests and validation

Write tests around the contract, not only the happy path:

- invalid input and raised exceptions;
- cancellation, timeout, and cleanup;
- `None` versus missing, empty collections, encoding edges;
- concurrency completion and failure propagation;
- security boundaries and resource cleanup.

Prefer designing testable code over mocking: explicit dependencies, small
seams, pure functions for logic. Mock at the process or network boundary,
not inside your own package.

### Process-isolated tests for import-time environment

Environment-sensitive behavior fixed at import time (`os.environ` read at
module level, a cached settings object, `functools.cache`) cannot be varied
by `monkeypatch.setenv` in the same process. Run the case in a child:

```python
import os
import subprocess
import sys


def test_timezone_from_env():
    if os.environ.get("JACAZUL_WANT_TZ_HELPER") == "1":
        from app.clock import today_label

        print(today_label(1_700_000_000))
        return

    for zone in ("UTC", "America/New_York", "Asia/Tokyo"):
        env = {**os.environ, "JACAZUL_WANT_TZ_HELPER": "1", "TZ": zone}
        out = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-s", __file__,
             "-k", "test_timezone_from_env"],
            env=env,
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
        ).stdout
        assert expected_label(zone) == out.splitlines()[0]
```

Use `sys.executable`, an explicit environment, a dedicated guard variable, a
narrow `-k` filter, and a timeout. Read the first line of the child's output;
the runner prints its own summary afterwards. `unittest` suites use
`python -m unittest module.Class.test` the same way.

### Time and timezone determinism

Pass timestamps explicitly or inject a `now()` callable. Use aware
`datetime` objects (`tzinfo=timezone.utc` or `zoneinfo.ZoneInfo`) and never
compare naive and aware values. `time.monotonic()` for elapsed time.

Run repository-configured checks first. If no stronger gate exists, use the
house baseline from [`SKILL.md`](SKILL.md#-mandatory-verification-py-check-gateway)
and label it as such: `py-check <path>` in greenfield and migration, and
`py-check --check <path>` in legacy mode.

## Version awareness

Check the interpreter floor before using:

- 3.14: template strings (`t"..."`) and deferred annotation evaluation by
  default; read the release notes before assuming either.
- 3.12: `type` statement and PEP 695 generics syntax; f-string grammar
  relaxations.
- 3.11: `ExceptionGroup`, `except*`, `asyncio.TaskGroup`, `tomllib`.
- 3.10: `match`, `X | Y` unions, parenthesized context managers.
- 3.9: builtin generics (`list[int]`), `zoneinfo`.
- 3.8: walrus operator, positional-only parameters.

## References

- [The Python Tutorial](https://docs.python.org/3/tutorial/)
- [The Python Language Reference](https://docs.python.org/3/reference/)
- [PEP 8](https://peps.python.org/pep-0008/)
- [PEP 484 Type Hints](https://peps.python.org/pep-0484/)
- [Python Packaging User Guide](https://packaging.python.org/)
- [asyncio documentation](https://docs.python.org/3/library/asyncio.html)
- [Python Code Review Directives](CODE-REVIEW.md)
