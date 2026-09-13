# JavaScript and TypeScript Expert Skill

Guide for the js-ts-expert skill: JavaScript and TypeScript across browser
and Node in legacy, greenfield and migration trees, framework-neutral, with
JavaScript kept thin at the edge of a Go, Rust or Zig backend unless you
choose otherwise.

## Trigger → Action

### When you touch any JavaScript or TypeScript tree

Run `js-mode <root>` first. It prints the mode and the evidence behind it
without needing Node:

```text
🐊 JS_TS_MODE: migration (source: scan)
  - modern tooling: typescript
  - legacy tooling: jquery
  - module system: CommonJS markers x41
  - module system: ESM markers x12
```

| Mode | Meaning | What the expert does |
|---|---|---|
| `legacy` | jQuery, Bower, Grunt/Gulp, Karma, webpack 4, CommonJS-only, `var` | Preserves behavior. No reformat of untouched files, no new tooling, fixes match the surrounding style. |
| `greenfield` | ESM, TypeScript strict, Vite/esbuild/Vitest, Prettier or Biome, pinned package manager | Applies the full modern baseline. |
| `migration` | Mixed markers | Incremental ordered steps, one commit each, suite green before and after. |

Override the scan with `JACAZUL_JS_TS_MODE=legacy|greenfield|migration` or
with `"jacazul": {"mode": "..."}` in `package.json`.

### When you dislike JavaScript and have to maintain it anyway

The expert works inside whatever the code already is (jQuery, a React app
someone else wrote, a Node service) by that code's rules, keeps changes
small, and does not push modernization into a bug fix. Ask for the
migration path when you want it; it comes as separate commits.

### When you want JavaScript kept thin

Say so, or let the expert ask once. Before adding logic to JavaScript it
states the boundary: DOM and interaction stay in the browser; business
rules, trusted validation and persistence go to the backend behind a small
contract (HTTP, WebSocket); CPU-bound browser work goes to WebAssembly
built from Go, Rust or Zig.

### When you choose full-stack JavaScript

Also fine. Answer the boundary question once ("full-stack JavaScript"),
the expert records it as a decision and stops asking. It then serves Next,
Nuxt, SvelteKit, Remix or a plain Node service completely: validation on
the server, data access in plain modules, the client bundle receives only
what it renders. No framework is proposed unprompted and none is
discouraged once chosen.

### When you run the checks

```bash
js-check <root>                 # run what the tree declares; may write per mode
js-check --check <root>         # validate only; never writes
js-check --dry-run <root>       # print the plan
js-check --run-scripts <root>   # also run the project's lint and test scripts
```

`js-check` picks the package manager from the lockfile, plans
`tsc --noEmit` when `tsconfig.json` exists and `prettier`/`eslint` when
configured, and requires an explicit path. It installs nothing and invents
no gate; a tree that declares nothing gets an information line, not a
failure.

### When indentation is not 4 spaces

The house preference is 4 spaces and stays explicit in the banner.
Resolution order: `--indent`, `JACAZUL_JS_TS_INDENT`, the project's own
configuration (`.editorconfig`, `.prettierrc*`, the `prettier` key in
`package.json`), then 4 spaces. A project on 2 spaces stays on 2 spaces. A
greenfield tree that declares nothing gets a prompt to write it down.

### When you must not reformat a legacy tree

Set `JACAZUL_JS_TS_IGNORE_FORMATTING=1`, or rely on the guard: a legacy
tree with no formatter configuration runs check-only automatically.

### When you ask for a JavaScript or TypeScript review

Findings use the shared [`code-review` scale](../skills/code-review/SKILL.md)
with the scenarios in
[`skills/js-ts-expert/CODE-REVIEW.md`](../skills/js-ts-expert/CODE-REVIEW.md):
promises nobody awaits, listeners nobody removes, DOM written from
untrusted strings, `any` and `as` hiding runtime shapes, framework state
owned by the wrong component, install-time trust, and logic that should
not be in JavaScript at all.

### When a framework is present

React, Solid, Vue, Svelte and friends are covered as boundaries and
pitfalls in the [playbook](../skills/js-ts-expert/PLAYBOOK.md): effects and
stale closures, keys and state ownership, signals and tracking scopes,
disposal. Business logic stays in plain modules the framework does not know
about.

## Best Practices

1. Name the mode before the first edit.
2. Answer the boundary question once and record it.
3. In legacy trees, `js-check --check` and match the local style.
4. Migrate in separate commits; never mix a step with a behavior change.
5. Prefer the platform API; measure before adding a dependency.

---

**Version:** 1.0.0
**Last Updated:** 2026-09-13
