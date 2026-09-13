# Python Code Review Directives

Python-specific review scenarios: the code shape to avoid, the runtime
sequence it creates, what can fail, and the evidence or correction a reviewer
should require.

The review method, scenario format, tracks, areas, technical levels,
advisories, and evidence labels are owned by the shared
[Code Review skill](../code-review/SKILL.md). This file adds Python scenarios
only and never redefines those labels. Before judging version-sensitive code,
read the interpreter floor (`requires-python`, `python_requires`,
`.python-version`) and run `py-mode` to know whether the tree is legacy,
greenfield, or in migration.

Scenarios are grouped by [track](../code-review/SKILL.md#tracks). The track
describes the learning path, not the severity: a Foundations pattern can still
create a critical security or availability incident. A review comment must be
tied to the repository's contract or a credible failure mode.

Python has no compiler standing between the author and production. Review
therefore concentrates on what nothing else checks: swallowed exceptions,
mutable state shared by accident, untyped boundaries, blocking calls in event
loops, unsafe deserialization and subprocess use, and tests that pass without
proving anything.

## Mode-aware review

The mode changes what counts as a finding:

- **Legacy:** a modern idiom introduced in one function among legacy ones is a
  `SUGGESTION` / `MAINTENANCE` finding against the change, not for it. A
  side-effect reformat of untouched files is a `WARNING` / `POLICY` finding.
- **Greenfield:** missing type hints on public functions, missing
  `pyproject.toml` metadata, and `os.path` string surgery are
  `SUGGESTION` findings under `CONTRACT` or `MAINTENANCE`.
- **Migration:** a commit that mixes a migration step with a behavior change
  is a `WARNING` / `FIX-NOW` / `POLICY` finding; steps are separate commits.

## Worked example (full form)

```python
async def refresh(cache: dict[str, Item], client: Client) -> None:
    for key in cache:
        item = await client.fetch(key)
        if item is None:
            del cache[key]
        else:
            cache[key] = item
```

**Context:** `cache` is shared with request handlers on the same event loop.

**Runtime sequence:** The loop iterates the live dictionary. Each `await`
yields to other tasks, which may insert or delete keys. `del cache[key]`
inside the iteration changes the dictionary's size.

**Failure modes:** `RuntimeError: dictionary changed size during iteration`
from the loop's own deletion, or from a concurrent handler mutating the
dictionary between awaits. Handlers observe a half-refreshed cache with no
way to tell.

**Review directive:** Do not mutate a collection while iterating it, and do
not hold an iteration over shared state across `await`. Require either
iteration over a snapshot with mutations applied after, or a lock around the
whole refresh when handlers must not see intermediate state.

**Acceptable correction:** `for key in list(cache)` and collect changes into
`updates` and `removals`, then apply them after the loop; or guard the cache
with an `asyncio.Lock` if atomic visibility is part of the contract. Add a
test with a concurrent mutation.

**Classification:** `WARNING` / `FIX-NOW` / `CONCURRENCY` / `TRACE`.

## Foundations: correctness

These are the first checks for almost every Python implementation and
review.

### 1. Swallowed exceptions

**Problem:** `except:`, `except Exception:`, or `except SomeError: pass`
hides a failure, or a broad handler logs and continues where the caller
expected an error.

**What can happen:** Partial writes are reported as success, a typo in a
variable name becomes a silent no-op, and the real failure surfaces far away
from its cause. A bare `except:` also catches `KeyboardInterrupt` and
`SystemExit`.

**Review questions:**

- Which exception types can this block actually receive, and is each one
  handled or deliberately ignored with a reason?
- Does the handler re-raise, convert, or return a value the caller can
  distinguish from success?

**Safer shape:** Catch specific types. Reserve broad handlers for process
boundaries that log with `exc_info` and re-raise or exit. Write the reason
next to every intentional `pass`.

### 2. Mutable default arguments

**Problem:** `def f(items=[])` or `def f(config={})`.

**What can happen:** The default object is created once at definition time
and shared by every call; state leaks between calls and between tests.

**Safer shape:** Default to `None` and create the object inside the
function. `ruff` rule `B006` reports it when enabled.

### 3. Mutating a collection while iterating

**Problem:** Items are added to or removed from a list, dict, or set inside a
loop over the same object.

**What can happen:** `RuntimeError` for dicts and sets, silently skipped
elements for lists, and different behavior between interpreter versions.

**Safer shape:** Iterate over a copy (`list(d)`, `d.items()` snapshot) or
build a new collection with a comprehension.

### 4. `is` versus `==` and truthiness traps

**Problem:** `x == None`, `if not items` where an empty collection and `None`
mean different things, `x is 0`, or `is` used to compare strings and
integers.

**What can happen:** Identity comparison of interned small integers or
strings works by accident and breaks with other values; `0`, `""`, `[]`, and
`None` collapse into one branch.

**Safer shape:** `is None` / `is not None` for `None`, `==` for values, and
explicit `len(items) == 0` when emptiness and absence differ at the
boundary.

### 5. Closures capturing loop variables late

**Problem:** Lambdas or nested functions defined in a loop reference the
loop variable without binding it.

**What can happen:** Every callback sees the last value; callbacks registered
per item all act on the final item.

**Safer shape:** Bind with a default argument (`lambda x=x: ...`),
`functools.partial`, or a factory function.

### 6. String formatting and encoding mismatches

**Problem:** Bytes and text are concatenated, files are opened without
`encoding`, or `%` formatting receives a tuple by accident.

**What can happen:** `TypeError` on the first non-ASCII input, platform-
dependent behavior from the default encoding, or `TypeError: not all
arguments converted` when a single tuple argument is formatted.

**Safer shape:** Open text files with `encoding="utf-8"` (or the documented
one), keep `bytes` and `str` separate, and prefer f-strings when the
interpreter floor allows them.

### 7. Integer and float assumptions

**Problem:** `int / int` expected to truncate, float equality with `==`,
`round` expected to round half up, or currency in floats.

**What can happen:** Off-by-one in indexes, flaky comparisons, banker's
rounding surprises, and money that does not add up.

**Safer shape:** `//` for integer division, `math.isclose` for floats,
`decimal.Decimal` for money, and explicit rounding modes.

### 8. Shadowing builtins and modules

**Problem:** A local named `list`, `id`, `type`, `input`, or a module file
named `json.py`, `test.py`, or `logging.py` inside the package.

**What can happen:** The builtin is unusable in that scope; the module
shadows the standard library for the whole package and imports resolve to
the wrong file.

**Safer shape:** Rename. `ruff` rule family `A` reports builtin shadowing.

### 9. Import-time side effects

**Problem:** A module reads the environment, opens a connection, starts a
thread, or parses arguments at import time.

**What can happen:** Importing for a test or a docs build performs I/O,
`monkeypatch` cannot change what was read at import, and import order
becomes behavior.

**Safer shape:** Move work into functions called from `main()` or a
constructor; keep module level to definitions and constants.

### 10. Wildcard imports and unclear exports

**Problem:** `from module import *`, or a package `__init__.py` that
re-exports everything and defines no `__all__`.

**What can happen:** Names collide silently, tooling cannot resolve
references, and the public surface is whatever happens to be importable.

**Safer shape:** Explicit imports; `__all__` on packages that define a public
API.

## Boundaries: resources and lifecycle

These checks become important as code handles files, processes, network,
concurrency, or a public interface.

### 11. Resources without a context manager

**Problem:** `open()`, sockets, locks, database cursors, or temporary
directories are acquired without `with` and released after a `return` or
only on the happy path.

**What can happen:** Descriptors leak until garbage collection, files are
left unflushed on exceptions, locks stay held after an error, and Windows
refuses to delete open files.

**Safer shape:** `with` for every resource with a lifetime; `contextlib` to
build managers for your own resources; cleanup in `finally` when a manager
does not fit.

### 12. `subprocess` with a shell and external input

**Problem:** `subprocess.run(cmd, shell=True)` or `os.system` with a string
built from user data; no `timeout`; return code unchecked.

**What can happen:** Command injection, a hung process that blocks the
caller forever, and a failure reported as success because `check=True` was
not set.

**Safer shape:** Argument lists, `shell=False`, `check=True` (or explicit
return-code handling), `timeout`, and `capture_output` only when the output
is bounded.

### 13. Blocking calls inside `asyncio`

**Problem:** `time.sleep`, `requests`, file I/O, or CPU-heavy code inside a
coroutine.

**What can happen:** The event loop stops serving every other task for the
duration of the call; latency spikes while CPU stays low.

**Safer shape:** Async clients and `asyncio.sleep`; `asyncio.to_thread` or a
process pool for blocking or CPU-bound work.

### 14. Fire-and-forget tasks

**Problem:** `asyncio.create_task(coro())` with the returned task dropped, or
`ensure_future` with no owner.

**What can happen:** The event loop keeps only a weak reference, so the task
can be garbage-collected mid-execution; exceptions surface as "Task
exception was never retrieved" long after the fact; shutdown does not wait.

**Safer shape:** Keep a strong reference (a set with a done callback) or use
`asyncio.TaskGroup` (3.11+) so the owner awaits completion and sees errors.

### 15. Swallowed `CancelledError`

**Problem:** `except Exception` around an `await` in Python 3.8+ is fine, but
`except BaseException` or a bare `except` catches `CancelledError` and does
not re-raise; or cleanup after cancellation awaits without shielding.

**What can happen:** Cancellation is lost, the task keeps running after the
caller gave up, and shutdown hangs.

**Safer shape:** Let `CancelledError` propagate; clean up in `finally`; use
`asyncio.shield` only for cleanup that must complete.

### 16. Threads, the GIL, and shared state

**Problem:** Threads mutate shared lists or dicts assuming the GIL makes
compound operations atomic, or CPU-bound work is threaded expecting a
speedup.

**What can happen:** Lost updates on read-modify-write sequences, and no
throughput gain for CPU-bound code under the GIL.

**Safer shape:** `threading.Lock` around compound operations, `queue.Queue`
for handoff, `concurrent.futures.ProcessPoolExecutor` for CPU-bound work.
On a free-threaded build, review the same code as genuinely concurrent.

### 17. Naive and aware datetimes

**Problem:** `datetime.now()` and `datetime.utcnow()` produce naive values
that are compared or stored next to aware ones; timezones are applied by
string manipulation.

**What can happen:** `TypeError: can't compare offset-naive and
offset-aware datetimes`, silently wrong offsets, and tests that pass only
in the developer's timezone.

**Safer shape:** `datetime.now(timezone.utc)`, `zoneinfo.ZoneInfo`, aware
values end to end, `time.monotonic()` for durations, and an injected clock
in tests.

### 18. Logging that leaks or misfires

**Problem:** f-strings inside `logger.debug(f"...")` evaluated on every
call, secrets or personal data in log lines, `print` in library code, or
`logging.basicConfig` called inside a library.

**What can happen:** Costly formatting for disabled levels, credentials in
log aggregators, and a library that hijacks the application's logging
setup.

**Safer shape:** `logger.debug("... %s", value)`, redact at the boundary,
`logging.getLogger(__name__)` in libraries, configuration only in the
application entry point.

### 19. Public API drift

**Problem:** A function grows positional parameters, a return type changes
from `list` to generator, a module is renamed without a shim, or `__all__`
shrinks.

**What can happen:** Downstream callers break on upgrade with no deprecation
path; keyword-only and positional-only contracts are silently violated.

**Safer shape:** Keyword-only parameters for options (`*,`), deprecation
warnings for one release, versioned changelog entries, and tests that
import the public names.

### 20. Environment mutation in tests

**Problem:** Tests assign `os.environ[...]` directly, or rely on
`monkeypatch.setenv` to change values a module read at import time.

**What can happen:** Test order dependence, leaked state into later tests,
and a false pass because the cached value never changed.

**Safer shape:** `monkeypatch.setenv` for values read at call time; a child
process for import-time or cached configuration (see the
[playbook](PLAYBOOK.md#process-isolated-tests-for-import-time-environment)).

### 21. Mocking the wrong target

**Problem:** `patch("requests.get")` when the code under test did
`from requests import get`, or mocking a private helper of the same package
instead of the boundary.

**What can happen:** The mock never applies and the test hits the network;
or the test pins implementation details and breaks on every refactor.

**Safer shape:** Patch where the name is looked up (`module_under_test.get`),
mock at process or network boundaries, and prefer fakes over mocks for
your own interfaces.

## Systems: contracts and performance

These require reasoning about trust boundaries, the interpreter, or
measured runtime behavior.

### 22. Unsafe deserialization

**Problem:** `pickle.loads`, `yaml.load` without a safe loader, `marshal`,
or `shelve` on data from the network, a queue, a cache, or a user file.

**What can happen:** Arbitrary code execution on load. The payload does not
need to be malformed; it needs to be crafted.

**Safer shape:** `json` or `orjson`, `yaml.safe_load`, a schema-validated
format, and signed payloads when the producer is trusted but the channel
is not.

### 23. Dynamic code and templates

**Problem:** `eval`, `exec`, `compile`, `importlib.import_module` with a
user-controlled name, or string templates rendered with autoescape off.

**What can happen:** Code injection, module import of attacker-chosen names,
and HTML injection in rendered output.

**Safer shape:** `ast.literal_eval` for literals, allowlists for module
names, autoescaping templates, and no code construction from input.

### 24. Path traversal and temporary files

**Problem:** `os.path.join(base, user_path)` with an absolute or `..`
component, predictable names under `/tmp`, or a check-then-use sequence on
a file.

**What can happen:** Reads or writes outside the intended root, symlink
races, and TOCTOU on the file the code just checked.

**Safer shape:** `Path(base).joinpath(name).resolve()` and
`is_relative_to(base)`, `tempfile` APIs, and opening the file once rather
than checking then opening.

### 25. Weak randomness and homemade crypto

**Problem:** `random` for tokens, session ids, or password reset links;
`hashlib.md5` for passwords; custom encryption.

**What can happen:** Predictable secrets and offline password recovery.

**Safer shape:** `secrets` for tokens, a vetted password hasher (`argon2`,
`bcrypt`, `scrypt` via the project's library), and standard protocols.

### 26. Dependency and build-time trust

**Problem:** A dependency added without inspecting its `setup.py` or build
backend; unpinned ranges in an application; `pip install` from an
unreviewed URL; no lockfile.

**What can happen:** Code runs on install, upgrades change behavior
silently, and a typosquatted package lands in production.

**Safer shape:** Lockfiles for applications, `pip-audit` or the project's
scanner, review of install-time hooks, and pinned indexes.

### 27. Performance claims without measurement

**Problem:** String concatenation in loops rewritten, `lru_cache` added
everywhere, or `__slots__` introduced on the theory that it is faster.

**What can happen:** Unmeasured changes that complicate code and sometimes
make it slower; caches that leak memory because their keys are unbounded.

**Safer shape:** `cProfile`, `tracemalloc`, or `timeit` on representative
input first; bounded caches; a benchmark in the change when performance is
the point.

### 28. `__eq__` and `__hash__` contracts

**Problem:** A class defines `__eq__` without `__hash__`, or a mutable
object is used as a dict key or set member.

**What can happen:** Instances become unhashable (`__hash__` is set to
`None`), or hash changes after insertion make the object unfindable.

**Safer shape:** `@dataclass(frozen=True)` for value objects, define both
methods together, and keep keys immutable.

### 29. Generators, iterators, and exhaustion

**Problem:** A generator is consumed twice, `len()` is called on an
iterator, or a file-backed generator is returned from a `with` block that
already closed the file.

**What can happen:** The second consumer sees nothing, `TypeError` on
`len`, and `ValueError: I/O operation on closed file` on first iteration.

**Safer shape:** Materialize with `list()` when reuse is needed, keep the
resource open for the generator's lifetime (make the generator own the
`with`), and document whether a function returns a sequence or an
iterator.

### 30. Class and inheritance ceremony

**Problem:** Abstract base classes with one implementation, manager and
helper classes with no state, `__init__` that only stores arguments, or
deep inheritance to share a method.

**What can happen:** Indirection without behavior; tests that mock the
ceremony instead of the logic.

**Safer shape:** Functions and modules first; `Protocol` for structural
contracts; dataclasses for data; inheritance only for genuine `is-a` with
shared behavior.

## Cross-cutting directives

### Migration steps that change behavior

**Avoid:** A commit that adopts a formatter, a linter rule family, or type
hints and also fixes a bug or changes logic.

**Context:** Migration commits are large and mechanical; reviewers cannot see
a behavior change inside them. `.git-blame-ignore-revs` will hide the commit
from blame, taking the behavior change with it.

**Runtime sequence:** The suite passes before the commit; the commit reformats
hundreds of lines and changes one condition; the suite still passes because
the condition was untested; the regression ships.

**Failure modes:** A regression attributed to "the formatting commit" with no
way to bisect inside it.

**Review directive:** Require the suite green before and after, a diff that
`ruff format --diff` (or the linter's own fix) reproduces exactly for
mechanical steps, and behavior changes in their own commits.

**Classification:** `WARNING` / `FIX-NOW` / `POLICY` / `TRACE`. Promote to
`BLOCKER` when the mechanical commit touches security-sensitive code.

### Legacy trees reformatted as a side effect

**Avoid:** Running `py-check <dir>` or `ruff format` on a tree whose mode
is legacy, or without an explicit path.

**Context:** `py-check` writes to disk in its first phase. A legacy tree
has its own conventions, often with no formatter configuration.

**Failure modes:** A one-line fix arrives with a thousand-line diff, blame is
destroyed, and the reviewer cannot find the fix.

**Review directive:** In legacy mode require `py-check --check` or
`JACAZUL_PY_IGNORE_FORMATTING=1`; reject diffs whose formatting changes
exceed the change's own scope.

**Classification:** `WARNING` / `FIX-NOW` / `POLICY` / `REPRODUCED`.

## Automated review baseline

The verification commands are defined once in
[`SKILL.md`](SKILL.md#-mandatory-verification-py-check-gateway).
Repository-configured gates always take precedence.

Evidence scope for the tools named there:

- `ruff check`: lints for several scenarios above (`B006` mutable
  defaults, `A` shadowing, `S` security rules when enabled). A clean run is
  evidence, not proof.
- `ruff format --check` and `pycodestyle`: mechanical style only.
- `mypy` / `pyright`: type consistency on annotated code; unannotated code
  is not checked.
- `pytest` / `unittest`: behavior verification.
- `pip-audit`: dependency advisories; not proof of application security.

## Source index

- [Python Language Reference](https://docs.python.org/3/reference/) —
  semantics of defaults, closures, comparisons, and iteration.
- [asyncio: Creating Tasks](https://docs.python.org/3/library/asyncio-task.html#creating-tasks)
  — the loop keeps only weak references to tasks.
- [`subprocess` security considerations](https://docs.python.org/3/library/subprocess.html#security-considerations)
- [`pickle` warning](https://docs.python.org/3/library/pickle.html) — never
  unpickle untrusted data.
- [`datetime` aware and naive objects](https://docs.python.org/3/library/datetime.html#aware-and-naive-objects)
- [`secrets`](https://docs.python.org/3/library/secrets.html)
- [Logging HOWTO](https://docs.python.org/3/howto/logging.html)
- [Ruff rules](https://docs.ruff.rs/rules/) — `B006`, `A001`, `S`-family.
- [Python Packaging User Guide](https://packaging.python.org/)
