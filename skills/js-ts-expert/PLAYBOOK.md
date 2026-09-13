# JavaScript and TypeScript Engineering Playbook

Implementation guidance for writing thin, typed, testable, and secure
JavaScript and TypeScript in each of the three modes the skill recognizes.
This file answers **how to build the change**. Scenario-based review
directives live separately in [`CODE-REVIEW.md`](CODE-REVIEW.md).

These are defaults, not automatic repository policy. Read `package.json`,
`tsconfig.json`, the lockfile, the linter and formatter configuration, and
CI before adopting an optional gate or changing an established contract.

## Before writing code

1. Run `js-mode <root>` and name the mode: legacy, greenfield, or
   migration. The mode decides how much of this playbook applies.
2. Decide the boundary: does this logic belong in JavaScript, in the
   backend language, or in WebAssembly built from it? Say so.
3. Read the runtime floor (`engines.node`, `.nvmrc`, `tsconfig` `target`,
   browserslist) and never use syntax or APIs above it.
4. Read the module system (`type` in `package.json`, `.mjs`/`.cjs`,
   `exports` map) before adding a file.
5. Read the target package and its tests before introducing an abstraction.
6. Identify trust boundaries: user input, URLs, `postMessage`, storage,
   network payloads, third-party scripts, environment variables, and
   dependency install hooks.

## Mode: greenfield

Apply the modern baseline in full.

- ESM only (`"type": "module"`), an `exports` map for libraries, no
  CommonJS.
- TypeScript with `strict: true`; `unknown` at boundaries, never `any`
  without a written reason.
- One package manager, pinned in `packageManager`, with the lockfile
  committed.
- Formatter (Prettier or Biome) and linter (flat ESLint config or Biome)
  declared in the repository; the house 4-space preference written into
  the configuration.
- Tests with the runner the project chose (Vitest, `node:test`,
  Playwright for the browser).
- Platform APIs first; no framework unless the repository already has one.

## Mode: legacy

Preserve behavior. The job is the fix or the feature, not the modernization.

- Do not reformat files you did not need to touch. Run `js-check --check`
  (or set `JACAZUL_JS_TS_IGNORE_FORMATTING=1`) so nothing rewrites a tree
  that has its own conventions.
- Match the local style: `var` where the file uses `var`, callbacks where
  the file uses callbacks, jQuery where the file uses jQuery, the existing
  module wrapper (IIFE, AMD, CommonJS).
- Do not introduce TypeScript, ESM, a bundler, a formatter, or a test
  runner as a side effect. Propose them as a migration plan instead.
- Keep polyfills and shims in place until a migration step removes them
  deliberately.
- Add a regression test in the project's existing runner (Karma, Mocha,
  QUnit, testee) before fixing a bug; the test proves the old behavior you
  must keep.
- If the legacy code is a framework someone else chose, work inside its
  rules and keep the change small; do not rewrite components to a newer
  pattern.

## Mode: migration (legacy to current)

Migration is a sequence of separate commits, each with the suite passing
before and after. Do not combine steps. Suggested order; the project decides
the actual one:

1. **Runtime floor.** Establish the lowest Node version and browsers the
   project must support and record them (`engines.node`, browserslist).
2. **Package manager and lockfile.** One manager, pinned, lockfile
   committed; remove Bower by moving its packages to npm equivalents.
3. **Formatter adoption.** One commit that only reformats, with the
   configuration added in the same commit, added to
   `.git-blame-ignore-revs`. Indentation follows the project's existing
   convention unless the project chooses the house 4 spaces.
4. **Linter adoption.** Flat ESLint config or Biome with the rules the
   project already satisfies; widen per rule family in later commits.
5. **Module system.** Convert CommonJS to ESM one package at a time;
   `.cjs` for files that must stay; an `exports` map before consumers
   depend on deep paths.
6. **TypeScript at boundaries.** Rename entry points and data models to
   `.ts` with `allowJs` and `checkJs` on; raise `strict` per package.
7. **Bundler and test runner.** Replace Grunt/Gulp/webpack 4/Karma with the
   modern equivalents one at a time, keeping the old pipeline until the new
   one is proven.
8. **Idiom sweep.** `const`/`let`, `async`/`await`, `fetch`,
   `AbortController`, platform APIs instead of jQuery. Per package, per
   commit, with the suite green.
9. **Boundary review.** After each step, ask again whether the logic
   belongs in JavaScript at all; a migration is the moment to move
   business rules to the backend.

A migration step that changes behavior is a bug, not a step. Revert it.

## Runtime and modules

- ESM and CommonJS interoperate badly: `require` of an ESM package fails
  on older Node, default-export shapes differ, `__dirname` does not exist
  in ESM (`import.meta.dirname` on Node 20.11+, `fileURLToPath` before).
- Browser and Node are different runtimes; code that touches `window`,
  `document`, `process`, or `fs` states which one it targets. Use
  conditional `exports` for packages that serve both.
- The event loop runs one task at a time; a long synchronous loop blocks
  rendering and I/O. Move CPU-bound work to a Worker, or out of JavaScript.
- Every listener, timer, observer, socket, and stream has an owner and a
  cleanup path; `AbortController` is the cancellation primitive for all of
  them.
- Streams (Web Streams and Node streams) need backpressure; do not buffer
  a whole body when the consumer can read incrementally.

## TypeScript correctness

- `strict: true` in greenfield; raise strictness per package in migration.
- `unknown` for external data; narrow with type guards; validate at
  runtime at the boundary (a schema library the project accepts, or hand
  written guards).
- Discriminated unions for state; exhaustive `switch` with a `never` check.
- Generics only when there are two real call sites that need them; branded
  types for identifiers and units.
- Every `as` cast and non-null assertion (`!`) is a proof obligation; write
  why the assertion holds or replace it with a check.
- Declarations (`.d.ts`) and the `exports` map are the public contract of
  a library; run `tsc` on the consumer side of the contract too.

## Browser and Web Components

- Own the DOM you create; do not reach into DOM owned by another component
  or framework.
- Custom elements: define lifecycle callbacks completely (`connectedCallback`,
  `disconnectedCallback`, `attributeChangedCallback`), reflect attributes
  and properties deliberately, and clean up in `disconnectedCallback`.
- Shadow DOM isolates styles, not events; compose with slots and dispatch
  composed events on purpose.
- Accessibility is behavior: keyboard operation, focus management, roles,
  names, and states. Test them in a real DOM environment.
- Read layout, then write layout; interleaving causes layout thrashing.

## Framework boundaries and pitfalls

Frameworks are covered only because repositories have them. When one is
present:

- React: effects run after paint and re-run per dependency change; stale
  closures capture old state; keys must be stable identities; state
  ownership goes to the lowest common owner; no side effects during
  render.
- Solid: signals track reads inside tracking scopes only; destructuring
  props breaks reactivity; dispose what you create outside the owner.
- Vue and Svelte: reactivity has its own rules for object mutation and
  derived state; read the framework's documentation for the version in use
  before touching state.
- Any framework: keep business logic in plain modules the framework does
  not know about, so the framework can be replaced or removed.

Do not propose a framework for a project that does not have one. Do not
propose replacing one framework with another. When the operator chooses
full-stack JavaScript (Next, Nuxt, SvelteKit, Remix, a plain Node service),
serve it completely: server routes and loaders keep trusted validation on
the server, data access lives in plain modules, the client bundle receives
only what it renders, and the runtime floor and deployment target are
declared. The boundary question was answered; do not reopen it in every
review.

## Errors, promises, and cancellation

- `async` functions return promises; a promise not awaited, returned, or
  handled is an unhandled rejection waiting for the right timing.
- Throw `Error` subclasses with `cause`; catch specific conditions;
  re-throw what you cannot handle.
- `Promise.all` fails fast; `Promise.allSettled` when partial success is
  the contract.
- Pass an `AbortSignal` to `fetch`, event listeners, and long operations;
  handle `AbortError` as cancellation, not failure.
- Validate external data (JSON, form fields, URL parameters, `postMessage`
  payloads) before use; malformed data is an expected input.

## Security boundary

Treat external input as hostile by default:

- no `innerHTML`, `outerHTML`, `insertAdjacentHTML`, or `document.write`
  with untrusted strings; use `textContent` or a sanitizer the project
  accepts;
- no `eval`, `new Function`, or string arguments to `setTimeout`;
- validate URLs before assigning to `href`, `src`, or `location`; reject
  `javascript:` and unexpected origins;
- check `event.origin` on every `postMessage` listener and target a
  specific origin when posting;
- guard against prototype pollution in deep merges and JSON-driven object
  construction (`__proto__`, `constructor`, `prototype` keys);
- secrets never reach the bundle, `localStorage`, or logs;
- review `postinstall` and other install scripts of new dependencies as
  code that runs on every machine; commit the lockfile; run the project's
  audit tool when release risk is in scope;
- respect and, where the project allows, tighten the Content Security
  Policy.

## Tooling and supply chain

- One package manager, pinned; the lockfile is the source of truth for
  installs (`npm ci`, `pnpm install --frozen-lockfile`).
- `exports`, `main`, `types`, and `files` in `package.json` are the
  published contract; test the packed artifact, not the source tree.
- Peer dependencies are declared, not silently installed.
- Source maps are shipped or not on purpose; they leak source when
  published by accident.
- Bundle size and dependency count are costs; measure before adding a
  dependency, and prefer the platform API when it exists.

## Performance

Measure first: DevTools performance panel, `performance.mark`, Node's
`--cpu-prof`. Then fix what the profile names: long tasks, layout
thrashing, unnecessary re-renders, allocations in hot loops, oversized
bundles. When the profile shows CPU-bound work, the answer may be
WebAssembly from the backend language or moving the work off the client.

## Documentation and generated outputs

- Document public APIs, lifecycle, accessibility behavior, failure modes,
  and examples.
- Generated bundles, declaration files, and code from schemas are not
  edited by hand; change the source and regenerate.
- Keep `README` usage in sync with the `exports` map.

## Tests and validation

Write tests around the contract, not only the happy path:

- invalid input, rejected promises, and thrown errors;
- cancellation and cleanup (listeners removed, timers cleared);
- DOM behavior in a real DOM environment or browser, including keyboard
  and focus;
- module boundaries (what the package exports) and serialized wire forms;
- security boundaries (escaping, origin checks).

Run repository-configured checks first. If no stronger gate exists, run
what the tree declares through `js-check`, and label anything else as a
conventional suggestion.

## References

- [MDN Web Docs](https://developer.mozilla.org/)
- [ECMAScript specification](https://tc39.es/ecma262/)
- [Node.js documentation](https://nodejs.org/docs/latest/api/)
- [TypeScript handbook](https://www.typescriptlang.org/docs/handbook/)
- [Web Components on MDN](https://developer.mozilla.org/docs/Web/API/Web_components)
- [OWASP DOM-based XSS prevention](https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html)
- [JavaScript and TypeScript Code Review Directives](CODE-REVIEW.md)
