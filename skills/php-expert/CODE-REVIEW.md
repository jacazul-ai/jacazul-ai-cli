# PHP Code Review Directives

PHP-specific review scenarios: the code shape to avoid, the runtime
sequence it creates, what can fail, and the evidence or correction a
reviewer should require.

The review method, scenario format, tracks, areas, technical levels,
advisories, and evidence labels are owned by the shared
[Code Review skill](../code-review/SKILL.md). This file adds PHP scenarios
only and never redefines those labels. Before judging version-sensitive
code, read the floor (`composer.json` `require.php`, what production runs)
and run `php-mode <root>` to know whether the tree is legacy, greenfield,
or in migration, and `php-census --floor <prod>` to know what already
exceeds the production floor.

Scenarios are grouped by [track](../code-review/SKILL.md#tracks). The track
describes the learning path, not the severity: a Foundations pattern can
still create a critical security or availability incident. A review comment
must be tied to the repository's contract or a credible failure mode.

PHP has no compiler pass and, in legacy trees, no type declarations. Review
concentrates on what nothing else checks: type juggling against input,
SQL and HTML built from strings, `@`-silenced failures, globals as the
API, syntax above the production floor, and migration commits that hide a
behavior change.

## Mode-aware review

- **Legacy:** a modern idiom introduced in one function among legacy ones
  is a `SUGGESTION` / `MAINTENANCE` finding against the change. Any
  construct newer than the production floor is `BLOCKER` / `FIX-NOW` /
  `POLICY`: it will fatal on deploy.
- **Greenfield:** missing `strict_types`, untyped public signatures, `==`
  against input, or string-built SQL are `SUGGESTION` or `WARNING`
  findings under `CONTRACT` or `SECURITY`.
- **Migration:** a commit that mixes construct families or carries a
  behavior change is `WARNING` / `FIX-NOW` / `POLICY`; a commit that raises
  the census instead of lowering it is `SUGGESTION` / `MAINTENANCE` with
  the count in the comment.

## Worked example (full form)

```php
function find_user($db, $id) {
    $sql = "SELECT * FROM users WHERE id = " . $id;
    $res = @mysql_query($sql, $db) or die(mysql_error());
    while ($row = mysql_fetch_assoc($res)) { return $row; }
}
```

**Context:** A legacy helper called from request handlers with `$_GET['id']`.

**Runtime sequence:** The id is concatenated into SQL unescaped. The query
runs under `@`, so a warning is silenced; `or die` turns a failure into a
half-rendered page with the database error printed. On PHP 7 and later,
`mysql_query` no longer exists: the function is a fatal error on first
call, after production flips.

**Failure modes:** SQL injection through `id`; information leak through
`mysql_error()` on screen; a hard fatal on the target PHP; no way to test
the function because the connection is global.

**Review directive:** Bind parameters through the project's database
wrapper, never concatenate input; no `@`, no `die` in library code; keep
the function inside the bridge subset if production is still on 5.6 (PDO
and `mysqli` exist there). Require a characterization test with a known
id before the change and after it.

**Acceptable correction:** Route through the wrapper's prepared-statement
method (`$db->selectOne('SELECT * FROM users WHERE id = ?', [$id])`),
return `null` on no row, throw on connection failure, log instead of
printing. In migration mode this is two commits: the wrapper method, then
the call site.

**Classification:** `BLOCKER` / `FIX-NOW` / `SECURITY` / `TRACE`.

## Foundations: correctness

### 1. Loose comparison against input

**Problem:** `==` (or `switch`, `in_array` without strict) comparing a
request value, a database string, or a token to a number or string.

**What can happen:** `"abc" == 0` was true before 8.0 and false after; `"1e3"
== "1000"` is true; `null == false == 0 == ""`. Authorization and routing
decisions flip between versions.

**Safer shape:** `===` and explicit casts; `in_array($x, $list, true)`;
`match` (or a strict `switch`) where the floor allows.

### 2. `empty()` and `isset()` used as validation

**Problem:** `empty($_POST['qty'])` rejects `"0"`; `isset` treated as
"has a value" when the key holds `null`.

**What can happen:** Valid zero values are rejected; nulls slip through
as present.

**Safer shape:** `array_key_exists` for presence, explicit checks for the
value, `filter_var` with a validating filter for numbers and emails.

### 3. `@` and `or die`

**Problem:** Errors silenced with `@`, or a failure branch that prints and
exits (`or die(mysql_error())`).

**What can happen:** Real failures disappear or leak internals to users;
the process exits from inside a library function; nothing is testable.

**Safer shape:** Exceptions from the boundary that owns the decision; an
error handler that converts warnings when the project does; logging, not
printing.

### 4. Globals as the API

**Problem:** Functions that read `global $db`, `$_SESSION`, or
`$GLOBALS['config']` instead of receiving what they need.

**What can happen:** Order-dependent behavior, hidden coupling, tests that
need the whole application booted.

**Safer shape:** Parameters and constructors; in legacy trees, a thin
adapter that injects the global once at the entry point while the
function itself becomes pure.

### 5. Reference leaks from `foreach`

**Problem:** `foreach ($items as &$item)` followed by another loop over
`$items` or a reuse of `$item`.

**What can happen:** The last element is overwritten with the value of the
next loop; data silently corrupted.

**Safer shape:** `unset($item)` after the loop; avoid reference iteration
unless mutation in place is the contract.

### 6. String interpolation and offsets from another era

**Problem:** `"${var}"`, `"$arr[key]"` without quotes, `$str{0}`.

**What can happen:** Deprecation in 8.2 (`${}`), a parse error in 8.0
(`{}` offsets), constant lookups instead of keys.

**Safer shape:** `"{$var}"`, `"{$arr['key']}"`, `$str[0]`.

### 7. Integer and float assumptions

**Problem:** `intdiv` expectations from `/`, money in floats, `round`
half-up assumptions, `(int)` on overflowing strings.

**What can happen:** Wrong totals; `PHP_INT_MAX` saturation; locale
dependent decimal separators in `(float)` before 8.0.

**Safer shape:** `intdiv`, `bcmath` or integer minor units for money,
explicit rounding mode, validated numeric input.

### 8. Array functions that reorder or reindex

**Problem:** `array_merge` on numeric keys renumbers; `sort` drops keys;
`array_unique` keeps the first key; `+` on arrays does not overwrite.

**What can happen:** Ids lost, associations broken, "merged" values
ignored.

**Safer shape:** Choose the function by the key contract: `+` or
`array_replace` to keep keys, `asort`/`ksort` to keep associations,
`array_values` deliberately.

### 9. Closures capturing by value

**Problem:** `use ($counter)` expected to see later changes; `$this`
captured in a closure stored past the object's life.

**What can happen:** Stale values; leaks through long-lived closures.

**Safer shape:** `use (&$x)` only when shared mutation is intended;
`static function` when `$this` is not needed.

### 10. Closing `?>` and output before headers

**Problem:** A trailing `?>` followed by a newline in a class file; `echo`
or a BOM before `header()` or `session_start()`.

**What can happen:** "headers already sent"; broken redirects and cookies;
whitespace in JSON responses.

**Safer shape:** Omit the closing tag in pure-PHP files; save files without
a BOM; output only after headers.

## Boundaries: resources and lifecycle

### 11. SQL built from strings

**Problem:** Concatenation or interpolation of any value into SQL, with or
without `mysql_real_escape_string`.

**What can happen:** SQL injection; escaping misses numeric contexts and
identifiers; charset-dependent bypasses.

**Safer shape:** Prepared statements through PDO or `mysqli`, via the
project's single wrapper; identifiers from an allowlist.

### 12. Output without context escaping

**Problem:** `echo $name` into HTML, `href="<?= $url ?>"`, data dropped into
inline scripts.

**What can happen:** Cross-site scripting; open redirects through
`javascript:` URLs.

**Safer shape:** `htmlspecialchars($v, ENT_QUOTES | ENT_SUBSTITUTE,
'UTF-8')` for HTML, `rawurlencode` for URL parts, `json_encode` with
`JSON_HEX_TAG` for script contexts; the template engine's escaping when
one exists.

### 13. Sessions handled by hand

**Problem:** `session_start` after output; ids not regenerated on login;
session data trusted as authorization without re-checking.

**What can happen:** Session fixation; headers already sent; privilege kept
after revocation.

**Safer shape:** Start before output; `session_regenerate_id(true)` on
privilege change; cookie flags; re-read authorization from the source of
truth on sensitive actions.

### 14. Files, uploads, and paths

**Problem:** `move_uploaded_file` to a web-served directory with the
client's name; `include $_GET['page'] . '.php'`; `file_get_contents` on a
user path.

**What can happen:** Remote code execution through an uploaded `.php`;
local file inclusion; arbitrary file read.

**Safer shape:** Store outside the web root with a generated name;
allowlist includes; `realpath` and prefix check before any user path.

### 15. `unserialize`, `eval`, `extract`, variable variables

**Problem:** `unserialize($_COOKIE['cart'])`, `eval` on templates, `extract($_REQUEST)`,
`$$name` from input.

**What can happen:** Object injection and code execution; variable
overwrite (`$isAdmin`).

**Safer shape:** JSON for untrusted structures; `unserialize` with
`allowed_classes => false`; no `eval`; explicit variable assignment.

### 16. Timezone and `DateTime` mutability

**Problem:** `date()` without a set timezone; `DateTime` (mutable) passed
around and modified by a callee; `strftime` with locale expectations.

**What can happen:** Off-by-hours across servers; a date changed by a
helper; `strftime` deprecated in 8.1 and locale-dependent output.

**Safer shape:** `date_default_timezone_set` once; `DateTimeImmutable`
with explicit zones; `DateTime::format` or `IntlDateFormatter`.

### 17. Encoding assumptions

**Problem:** `strlen`/`substr` on UTF-8; `utf8_encode` used as "fix
encoding"; database connection without `utf8mb4`.

**What can happen:** Broken characters, truncated multibyte strings,
mojibake stored permanently.

**Safer shape:** `mb_*` functions; `mb_convert_encoding` with explicit
source and target; `utf8mb4` on the connection and the schema.

### 18. Shell commands and external processes

**Problem:** `exec("convert $file ...")`, `shell_exec` with interpolated
input, `system` without checking the exit code.

**What can happen:** Command injection; failures reported as success.

**Safer shape:** `escapeshellarg` on every argument, `proc_open` with an
argument array where the floor allows, exit code checked.

### 19. Autoloading and `require_once` chains

**Problem:** Hundreds of `require_once` with relative paths; a
`__autoload` function; classes found by include order.

**What can happen:** Order-dependent fatals; `__autoload` removed in 8.0;
untestable units.

**Safer shape:** Composer PSR-4 (post-flip in migration); `spl_autoload_register`
as the bridge; absolute paths from `__DIR__`.

### 20. Tests that boot the world

**Problem:** A test that needs the full application, a live database, and
a fixed clock to run; or no tests at all for the code about to change.

**What can happen:** Nobody runs them; migration steps go unverified.

**Safer shape:** Characterization tests around the entry points being
touched; process isolation for `php.ini`-dependent behavior; a smoke runner
when PHPUnit is not yet in the tree.

## Systems: contracts, migration, and versions

### 21. Syntax above the production floor

**Problem:** `??`, `fn`, `match`, typed properties, `?->`, or `enum` in a
tree whose production still runs 5.6 (or any floor below the construct).

**What can happen:** A parse error on deploy; the whole request fatals,
not just the feature.

**Safer shape:** `php-census --floor <prod>` at zero before deploy; the
bridge subset until the flip; the probe with the production binary when
available.

### 22. Migration commit with a behavior change

**Problem:** A commit that converts `each()` to `foreach` and also fixes a
condition, or reformats a file and changes a default.

**What can happen:** The regression hides inside a large mechanical diff;
`.git-blame-ignore-revs` buries it.

**Safer shape:** One construct family per commit; behavior changes in
their own commits with their own tests; census totals in the message.

### 23. PHP 4 constructors and inheritance

**Problem:** A method named after the class acting as constructor; a
subclass calling `parent::ClassName()`; both a PHP 4 and a `__construct`
present with different bodies.

**What can happen:** Removed in 8.0: the object is constructed without
running the old method; subclass calls fatal.

**Safer shape:** `__construct` with the old name kept as a forwarder while
callers still use it, then removed; grep for `parent::OldName(`.

### 24. Dynamic properties as a data model

**Problem:** Classes that assign undeclared properties (`$this->row = ...`)
as a habit, or code that relies on `stdClass`-like behavior of real
classes.

**What can happen:** Deprecated in 8.2; a future fatal; typos create new
properties silently today.

**Safer shape:** Declare properties (typed where the floor allows);
`#[AllowDynamicProperties]` only on genuine bags while the declaration work
is tracked; `stdClass` or arrays for truly dynamic data.

### 25. The database wrapper migrated call site by call site

**Problem:** `mysql_*` replaced by `mysqli_*` or PDO in individual files,
leaving two connection styles alive.

**What can happen:** Two connections, two escaping regimes, transactions
that span neither; a migration that never finishes.

**Safer shape:** One wrapper, one adapter switch, then delete the old
path; prepared statements arrive with the adapter.

### 26. `php.ini` semantics assumed

**Problem:** Code that only works with `short_open_tag=On`,
`register_globals`, `magic_quotes`, `display_errors=On`, or a specific
`error_reporting`.

**What can happen:** Behavior changes between servers; `<?` printed as
text; input silently escaped or not.

**Safer shape:** `<?php` and `<?=` only; superglobals read explicitly; no
dependence on quotes settings; errors logged.

### 27. Composer dependencies pinned to the past

**Problem:** `guzzle 6`, `ramsey/uuid 3` and similar locked years ago;
`platform.php` faking a newer PHP; `vendor/` committed with local edits.

**What can happen:** Known vulnerabilities; packages that fatal on 8.x;
edits lost on `composer install`.

**Safer shape:** One dependency family per commit after the flip;
`composer audit`; patches through `composer-patches` or a fork, never
edits inside `vendor/`.

### 28. Performance claims without measurement

**Problem:** OPcache assumptions, "arrays are slow" rewrites, caching added
everywhere, `SELECT *` "optimized" by hand.

**What can happen:** No gain, more code, stale caches.

**Safer shape:** Profile (Xdebug profiler, Blackfire, or the project's
tool) on representative requests; index the query the profile names; cache
with an invalidation story.

## Cross-cutting directives

### Two pins: floor and target

**Avoid:** Reviewing a migration tree against only the target PHP or only
the production PHP.

**Context:** Production runs the floor; development runs the target; a
change must be correct on both until the flip.

**Review directive:** Every migration review states both versions, runs
`php-census --floor <prod>` (must be zero) and `php-census --lint
<target>` (parse errors must not grow), and treats a construct above the
floor as `BLOCKER`.

**Classification:** `BLOCKER` / `FIX-NOW` / `POLICY` / `TOOL`.

### Legacy trees reformatted as a side effect

**Avoid:** Running a formatter or a Rector set over a legacy tree inside a
fix commit.

**Review directive:** Reject diffs whose mechanical changes exceed the
change's scope; mechanical steps get their own commit and
`.git-blame-ignore-revs` entry.

**Classification:** `WARNING` / `FIX-NOW` / `POLICY` / `REPRODUCED`.

## Automated review baseline

The verification commands are defined once in
[`SKILL.md`](SKILL.md#-conventional-verification-baseline).
Repository-configured gates always take precedence.

Evidence scope:

- `php -l` (floor and target binaries): parse errors only.
- `php-census`: removed and deprecated construct counts; the floor check.
  Static heuristics, not proof.
- PHPCompatibility (phpcs), PHPStan or Psalm with a baseline: analyzers
  that find more than the census and miss runtime juggling.
- The project's test runner: behavior verification.
- `composer audit`: dependency advisories; not proof of application
  security.

## Source index

- [PHP Manual](https://www.php.net/manual/en/) — language reference and
  function documentation.
- [Migrating from PHP 5.6.x to PHP 7.0.x](https://www.php.net/manual/en/migration70.php)
  — removed extensions and functions, engine exceptions.
- [Migrating from PHP 7.4.x to PHP 8.0.x](https://www.php.net/manual/en/migration80.php)
  — string-to-number comparison, removed constructs.
- [Migrating from PHP 8.0.x to PHP 8.1.x](https://www.php.net/manual/en/migration81.php),
  [8.2](https://www.php.net/manual/en/migration82.php),
  [8.3](https://www.php.net/manual/en/migration83.php),
  [8.4](https://www.php.net/manual/en/migration84.php) — deprecations.
- [PHP Comparison operators](https://www.php.net/manual/en/language.operators.comparison.php)
  — loose comparison tables.
- [PHP `unserialize`](https://www.php.net/manual/en/function.unserialize.php)
  — object injection warning.
- [OWASP PHP Configuration Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/PHP_Configuration_Cheat_Sheet.html)
- [PHPCompatibility](https://github.com/PHPCompatibility/PHPCompatibility)
  and [Rector](https://getrector.com/documentation) — migration accelerators.
