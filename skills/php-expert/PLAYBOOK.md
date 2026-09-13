# PHP Engineering Playbook

Implementation guidance for writing explicit, typed, testable, and secure
PHP, and for moving a PHP 5.x codebase to a supported PHP without breaking
production on the way. This file answers **how to build the change**.
Scenario-based review directives live separately in
[`CODE-REVIEW.md`](CODE-REVIEW.md).

This playbook is about the language. Frameworks and CMS (WordPress,
Laravel, Symfony, home-grown front controllers) are out of scope: the
expert works inside whatever is present, by that project's own
documentation, and uses their presence only as evidence of era.

These are defaults, not automatic repository policy. Read `composer.json`,
`php.ini` expectations, CI, and the project's own tooling before adopting
an optional gate or changing an established contract.

## Before writing code

1. Run `php-mode <root>` and name the mode: legacy, greenfield, or
   migration. The mode decides how much of this playbook applies.
2. Read the floor: `composer.json` `require.php`, `config.platform.php`,
   `.php-version`, and what production actually runs. Never use syntax
   above the lowest of them.
3. Read the runtime: SAPI (CLI, FPM, mod_php), `short_open_tag`,
   `error_reporting`, `display_errors`, `date.timezone`, `memory_limit`,
   `open_basedir`, `disable_functions`. Semantics live in `php.ini`.
4. Read the target file and its callers before introducing an
   abstraction; in legacy trees the callers are global.
5. Identify trust boundaries: `$_GET`/`$_POST`/`$_COOKIE`, uploaded files,
   database rows, `unserialize`, `include` paths, shell commands, and
   templates that echo.

## Mode: greenfield

Apply the modern baseline in full.

- PHP 8.2 or newer declared in `composer.json` and honored in CI.
- Composer with PSR-4 autoloading, `composer.lock` committed for
  applications, `vendor/` outside the repository.
- `declare(strict_types=1)` in every file; typed properties, parameters,
  and return types; `readonly` for value objects; enums for finite state;
  `match` for exhaustive branching.
- PDO with prepared statements (or the project's data layer), never string
  concatenation into SQL.
- PHPUnit; a static analyzer (PHPStan or Psalm) at the level the project
  chose; a formatter (PHP-CS-Fixer or phpcs) declared in the repository.
- No `global`, no `extract`, no `eval`, no `@` error suppression.

## Mode: legacy

Preserve behavior. The job is the fix or the feature, not the
modernization.

- Do not reformat files you did not need to touch. There is usually no
  formatter configured; do not add one as a side effect.
- Match the local style: `array()` where the file uses `array()`,
  `var $prop` next to `var $prop`, the file's own escaping helpers, its
  own database wrapper.
- Do not introduce namespaces, Composer, type declarations, or
  `strict_types` into a file that has none. Propose them as a migration
  plan instead.
- Keep every change inside the syntax the **production** PHP accepts
  (see the bridge subset below); development PHP being newer does not
  change the floor.
- Add a characterization test (a request or a function call with the
  observed output) in the project's runner, or a smoke script, before
  fixing a bug; the test proves the behavior you must keep.
- `php -l` with the production binary on every touched file is the
  cheapest gate and it is never skipped.

## Mode: migration (PHP 5.6 to 8.x)

The two-pin situation: production runs the old floor, development runs
the target, and the codebase must keep working on the floor until
production flips. Everything below is one construct family per commit,
suite green after each, no behavior change inside a migration commit.

### 1. Census before code

```bash
php-census <root>                # removed and deprecated constructs by breaking version
php-census --lint php8.4 <root>  # plus php -l with the target binary
php-census --floor 5.6 <root>    # constructs newer than the production floor
```

The census is the progress bar. Rerun it after every step and record the
totals in the commit message or the task. A typical 5.x intranet of 380k
lines shows on the first run: ~200 `mysql_*` calls, ~100 `ereg`/`split`,
~90 `each()`, ~120 classes with PHP 4 constructors, ~125 `strftime`, ~330
dynamic property writes, ~30 `${var}` interpolations, and only a couple of
files that fail to parse on 8.4. Parse errors are rare; runtime removals
are the work.

### 2. The bridge subset

While production stays on 5.6, a change may use only what both versions
accept. Newer than 5.6, therefore forbidden until the flip:

| Construct | Needs |
|---|---|
| `??`, scalar and return types, `declare(strict_types=1)` | 7.0 |
| `[$a, $b] =` destructuring, `?Type`, `void`, `iterable` | 7.1 |
| `fn() =>`, typed properties, `??=`, spread in arrays | 7.4 |
| `match`, `?->`, `#[Attribute]`, named arguments, constructor promotion, `str_contains` | 8.0 |
| `enum`, `readonly`, `never`, first-class callables `f(...)` | 8.1 |
| `readonly class`, DNF types | 8.2 |

Allowed and useful on 5.6: closures (`function () use ()`), short arrays
`[]`, `__construct`, `public` properties, `foreach`, `PDO`, `mysqli`,
`password_hash`, generators, `finally`, variadics `...$args`, `::class`.

`php-census --floor 5.6` lists what the tree already uses above the floor.
When the production binary is available, a self-contained probe (a list of
syntax cases run through `php -l` with the 5.6 binary, each with the
expected pass or fail) is the second line of defense before deploying a
diff.

### 3. Order of work

Ordered by the version that breaks the construct, so each step unlocks
the next target:

1. **Parse errors on the target.** `php-census --lint <target-php>`; fix
   or quarantine the files (embedded third-party tools such as a bundled
   database admin often account for all of them).
2. **Removed in 7.0.** `mysql_*` (see the database step), `ereg*` and
   `split` to `preg_*`, `&new` to `new`, `set_magic_quotes_runtime`,
   `preg_replace` `/e` to `preg_replace_callback`, ASP tags.
3. **Removed in 8.0.** `each()` to `foreach`, `create_function` to
   closures, PHP 4 constructors to `__construct` (keep the old method as
   a thin forwarder only while callers call it by name), `__autoload` to
   `spl_autoload_register`, `$str{0}` to `$str[0]`, `implode` argument
   order, `get_magic_quotes_gpc` (returns false since 5.4; delete the
   branch), string-to-number comparison changes (`0 == "abc"` is now
   false: audit `==` against user input).
4. **Deprecated in 8.1 and 8.2.** `strftime` to `IntlDateFormatter` or
   `DateTime::format`; `FILTER_SANITIZE_STRING` to `htmlspecialchars` at
   output; `${var}` to `{$var}`; `utf8_encode`/`utf8_decode` to
   `mb_convert_encoding`; dynamic properties: declare them, or add
   `#[AllowDynamicProperties]` on classes that genuinely act as bags while
   the declaration work is tracked; passing `null` to non-nullable internal
   parameters (wrap with `(string)` or guard).
5. **Deprecated in 8.3 and 8.4.** `get_class()` without argument,
   implicitly nullable parameters (`Type $x = null` to `?Type $x = null`),
   `E_STRICT`, `mysqli_ping`, `session_set_save_handler` old shape.
6. **`php.ini`-dependent code.** `short_open_tag` (`<?` to `<?php`, keep
   `<?=`), `register_globals`-era reads of `$HTTP_*_VARS` (dead since 5.4:
   delete or map to superglobals), `magic_quotes` branches (delete).
7. **Composer.** Add `composer.json` if absent, declare the floor, replace
   bundled libraries with locked packages one at a time, keep the old copy
   until the new one is proven.
8. **Production flip.** Deploy the target PHP with the census at zero for
   removed constructs and the suite green; keep the old binary available
   for one release cycle.
9. **Idiom sweep, after the flip.** Namespaces and PSR-4, `strict_types`,
   typed signatures, `match`, enums, `readonly`. Per package, per commit.
   This is the step people start with; it is the last one.

### 4. Database layer

`mysql_*` is replaced through the project's single wrapper, not at two
hundred call sites. Give the wrapper (`db` class, ADOdb adapter, or a
thin new class) a `mysqli` or PDO implementation behind the same method
names, switch the wrapper, run the suite, then remove the `mysql_*` path.
Prepared statements arrive in the same move for every query that takes
input; escaping-only helpers (`mysql_real_escape_string`) get a compatible
shim during the transition and are deleted in the idiom sweep.

### 5. Tests as the net

- Characterization tests around every entry point that will be touched:
  request in, response out, database rows before and after.
- `php -l` with the target on touched files; `php-census` totals in the
  commit; `php-census --floor` at zero for the production floor.
- The project's runner (PHPUnit or a smoke script) green after each
  commit.
- Rector (with the `phpcompat` and `php8x` sets) and PHPCompatibility for
  phpcs are accelerators when the project adopts them; they do not replace
  the census, and their output is reviewed, not merged blind.
- Keep a log of what the census counted at each commit; it is the report
  when someone asks how far along the migration is.

### 6. What a migration commit never contains

A behavior change. A reformat of untouched files. Two construct families.
A framework upgrade. If a step changes behavior, it is a bug: revert, add
the test that would have caught it, redo the step.

## Language core

- Types: declare them at public boundaries; `strict_types=1` per file
  where the floor allows; `int|string` unions and `?Type` where absence is
  real; `mixed` is a proof obligation.
- Type juggling: `==` compares after conversion and changed meaning in
  8.0 for numeric strings; `===` unless juggling is the point. Never `==`
  against user input.
- Null: `??` and `?->` for absence; `isset` for existence; `empty` is a
  truthiness trap (`"0"` is empty).
- Arrays: ordered maps; `array_key_exists` versus `isset` (null values);
  copy-on-write, so passing by value is cheap until written.
- References: `&` in `foreach` leaves a dangling reference after the loop;
  `unset` it. Avoid reference parameters unless the API is about them.
- Closures: `use ()` captures by value; `use (&$x)` by reference;
  `static fn` to avoid binding `$this`.
- Exceptions: throw specific ones, catch specific ones; `Throwable` only
  at the top; never `@`; convert warnings to exceptions in the error
  handler when the project does.
- Generators for streams; `yield` instead of building arrays.
- Enums, `readonly`, `match`, attributes, first-class callables when the
  floor allows.

## Runtime

- CLI, FPM, and mod_php differ in `php.ini`, environment, and lifetime;
  test in the SAPI that ships.
- Output buffering and headers: nothing echoes before `header()`; watch
  BOMs and closing `?>` whitespace (omit the closing tag in pure-PHP
  files).
- Sessions: `session_start` before output; regenerate the id on login;
  `httponly`, `secure`, `samesite` cookie flags.
- Timezone: set it once; store UTC; `DateTimeImmutable` with explicit
  zones.
- Encoding: `mb_*` for text, `utf8mb4` in the database, `htmlspecialchars`
  with `ENT_QUOTES | ENT_SUBSTITUTE` and the charset.

## Packaging

- Composer is the package manager; `composer.json` declares the floor;
  `composer.lock` is committed for applications; `vendor/` is installed,
  not committed, unless the project deliberately vendors.
- PSR-4 autoloading; no `require_once` chains for classes once Composer
  exists.
- `composer audit` (or the project's scanner) when release risk is in
  scope; review a dependency's install scripts and `bin` before adding it.

## Data boundaries

- PDO with prepared statements and `ERRMODE_EXCEPTION`; `mysqli` prepared
  statements where PDO is not the project's choice; never interpolated
  SQL.
- `json_encode` with `JSON_THROW_ON_ERROR`; `json_decode` with the same
  and an explicit assoc flag.
- `unserialize` never on untrusted data; `allowed_classes => false` when
  it must run.
- File uploads: validate type by content, store outside the web root,
  never trust the client name.
- Paths: `realpath` and a prefix check before `include`, `file_get_contents`,
  or `readfile` with user input.

## Security boundary

Treat external input as hostile by default:

- SQL through prepared statements only;
- output escaped for its context (`htmlspecialchars` for HTML,
  `rawurlencode` for URLs, JSON for scripts), never `echo $_GET[...]`;
- CSRF tokens on state-changing requests;
- `password_hash` / `password_verify`, never `md5` or `sha1` for
  passwords;
- no `eval`, no `extract` on input, no variable variables from input, no
  `include` of user-controlled paths, no `shell_exec` with unescaped
  arguments (`escapeshellarg`);
- `session_regenerate_id` on privilege change; cookie flags set;
- `display_errors` off in production; errors logged, not shown.

## Tests and validation

- PHPUnit (or the project's runner); characterization tests for legacy
  code; process isolation (`php` subprocess with an explicit `-d` or
  environment) for behavior that depends on `php.ini`.
- `php -l` is the cheapest gate; run it with the production binary and the
  target binary in migration mode.
- Static analysis at the project's declared level with a baseline for
  legacy trees; the baseline shrinks, never grows.

Run repository-configured checks first. If no stronger gate exists, use
the baseline from [`SKILL.md`](SKILL.md#-conventional-verification-baseline)
and label it as such.

## Version awareness

- 5.3: namespaces, closures, late static binding.
- 5.4: short arrays, traits, `$HTTP_*_VARS` and `register_globals` removed.
- 5.5: generators, `finally`, `password_hash`.
- 5.6: variadics, `**`, constant expressions.
- 7.0: scalar types, return types, `??`, `<=>`, `mysql_*` and `ereg`
  removed, engine exceptions.
- 7.1: nullable types, `void`, short list destructuring.
- 7.4: typed properties, arrow functions, `??=`, preloading.
- 8.0: `match`, `?->`, named arguments, attributes, promotion, union types,
  `each()` and `create_function` removed, PHP 4 constructors removed,
  string-to-number comparison change.
- 8.1: enums, `readonly`, fibers, `never`, `strftime` deprecated.
- 8.2: `readonly` classes, DNF types, dynamic properties and `${}`
  deprecated, `utf8_encode` deprecated.
- 8.3: typed class constants, `json_validate`, `#[Override]`.
- 8.4: property hooks, asymmetric visibility, implicitly nullable
  parameters deprecated, `E_STRICT` deprecated.

Read the migration guide of the target version:
https://www.php.net/manual/en/appendices.php

## References

- [PHP Manual](https://www.php.net/manual/en/)
- [Migration guides (appendices)](https://www.php.net/manual/en/appendices.php)
- [PHP Standards Recommendations (PSR)](https://www.php-fig.org/psr/)
- [Composer documentation](https://getcomposer.org/doc/)
- [PHPCompatibility ruleset](https://github.com/PHPCompatibility/PHPCompatibility)
- [Rector](https://getrector.com/documentation)
- [PHP Code Review Directives](CODE-REVIEW.md)
