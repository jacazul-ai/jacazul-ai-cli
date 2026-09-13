# PHP Expert Skill

Guide for the php-expert skill: PHP as a language, from 5.x legacy through
modern 8.x, framework-neutral, with a reproducible method for migrating a
PHP 5.6 codebase to a supported PHP while production still runs the old
version.

## Trigger → Action

### When you touch any PHP tree

Run `php-mode <root>` first. It prints the mode, the declared floor and the
evidence, without needing PHP installed:

```text
🐊 PHP_MODE: migration (source: scan)
  - packaging: composer.json present
  - removed in 7.0: mysql_* extension x199 (28 files)
  - removed in 8.0: PHP 4 constructor (method named after its class) x121 (68 files)
  - deprecated in 8.2: dynamic property writes ($this->x = ...) to review x333 (72 files)
  - modern since 8.0: match expression x25
```

| Mode | Meaning | What the expert does |
|---|---|---|
| `legacy` | 5.x era: `mysql_*`, `ereg`, `each()`, PHP 4 constructors, globals, `<?` tags, no Composer | Preserves behavior, no reformat, no new tooling, changes inside the production floor's syntax. |
| `greenfield` | PHP 8.2+, Composer, `strict_types`, typed signatures, enums, PHPUnit, an analyzer and a formatter declared | Applies the full modern baseline. |
| `migration` | Removed constructs next to modern syntax, or production behind development | The two-pin protocol, one construct family per commit. |

Override the scan with `JACAZUL_PHP_MODE=legacy|greenfield|migration` or
with `"extra": {"jacazul": {"mode": "..."}}` in `composer.json`.

### When production runs an older PHP than your machine

That is the two-pin situation and the expert names both: the **floor**
(what production runs) and the **target** (where the code is going). Until
production flips, changes use only the syntax both versions accept. The
guard:

```bash
php-census --floor 5.6 <root>     # constructs newer than production; must be zero before deploy
```

```text
🐊 php-census: constructs newer than floor 5.6
breaks  kind         count  files  label
7.0     modern          38     19  ?? null coalescing
7.4     modern          50     13  fn() arrow functions
8.0     modern          25     15  match expression
total: 113 across 3 construct families

💡 PROMPT: these constructs will not run on the production floor 5.6.
```

### When you migrate from PHP 5.6 to 8.x

The method is in
[`skills/php-expert/PLAYBOOK.md`](../skills/php-expert/PLAYBOOK.md) and
starts with a census, not with code:

```bash
php-census <root>                 # removed and deprecated constructs by breaking version
php-census --lint php8.4 <root>   # plus php -l with the target binary
```

```text
breaks  kind         count  files  label
7.0     removed        199     28  mysql_* extension
7.0     removed        104     38  ereg* / split() / spliti()
8.0     removed        121     68  PHP 4 constructor (method named after its class)
8.0     removed         88     29  each()
8.1     deprecated     125    116  strftime() / gmstrftime()
8.2     deprecated     333     72  dynamic property writes ($this->x = ...) to review
total: 1429 across 21 construct families
```

The counts are the progress bar. The order of work follows the version
that breaks each construct: parse errors on the target, removals of 7.0,
removals of 8.0, deprecations of 8.1 to 8.4, `php.ini`-dependent code,
Composer, the production flip, and only then the idiom sweep (namespaces,
`strict_types`, typed signatures). `mysql_*` is replaced through the
project's single database wrapper, not call site by call site. One
construct family per commit, the suite green after each, no behavior
change inside a migration commit.

### When the code has PHP 4 constructors or dynamic properties

The census finds them structurally (a method named after its class; a
`$this->x =` write with no declared property). PHP 4 constructors are
removed in 8.0: add `__construct`, keep the old name as a forwarder while
callers use it, grep for `parent::OldName(`. Dynamic properties are
deprecated in 8.2: declare them, or `#[AllowDynamicProperties]` on genuine
bags while the declaration work is tracked.

### When you ask for a PHP code review

Findings use the shared [`code-review` scale](../skills/code-review/SKILL.md)
with the scenarios in
[`skills/php-expert/CODE-REVIEW.md`](../skills/php-expert/CODE-REVIEW.md).
A construct above the production floor is a `BLOCKER`; every migration
review states both pins and the census totals.

### When the project uses a framework or a CMS

The expert is the language engine. It works inside WordPress, Laravel,
Symfony or a home-grown front controller by that project's own
documentation, uses their presence only as evidence of era, and never
proposes one. Framework guidance is a separate skill if the community
wants it.

### When you want to learn PHP

Ask for a tutorial. The engine activates `tutor`, `php-tutor` and
`php-expert` together; see [Tutors](tutor.md). Every example is checked
with `php -l` on your production floor before it is shown.

## Best Practices

1. Name the mode and the two pins before the first edit.
2. `php -l` with the production binary on every touched file; never skip
   it.
3. `php-census --floor` at zero before any deploy while production is
   behind.
4. Migrate by census, one construct family per commit, idiom sweep last.
5. Bind SQL, escape output for its context, never `@`, never `or die`.

---

**Version:** 1.0.0
**Last Updated:** 2026-09-13
