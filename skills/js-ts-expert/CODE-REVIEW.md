# JavaScript and TypeScript Code Review Directives

JavaScript and TypeScript review scenarios: the code shape to avoid, the
runtime sequence it creates, what can fail, and the evidence or correction a
reviewer should require.

The review method, scenario format, tracks, areas, technical levels,
advisories, and evidence labels are owned by the shared
[Code Review skill](../code-review/SKILL.md). This file adds JavaScript and
TypeScript scenarios only and never redefines those labels. Before judging
version-sensitive code, read the runtime floor (`engines.node`, `.nvmrc`,
`tsconfig` `target`, browserslist) and run `js-mode` to know whether the
tree is legacy, greenfield, or in migration.

Scenarios are grouped by [track](../code-review/SKILL.md#tracks). The track
describes the learning path, not the severity: a Foundations pattern can
still create a critical security or availability incident. A review comment
must be tied to the repository's contract or a credible failure mode.

The compiler (when there is one) checks types, not behavior. Review
concentrates on what nothing else checks: promises nobody awaits, listeners
nobody removes, DOM written from untrusted strings, `any` and `as` hiding
runtime shapes, framework state owned by the wrong component, dependencies
that run code on install, and logic that should not be in JavaScript at all.

## Mode-aware review

- **Legacy:** a modern idiom introduced in one function among legacy ones is
  a `SUGGESTION` / `MAINTENANCE` finding against the change. A side-effect
  reformat of untouched files is `WARNING` / `POLICY`.
- **Greenfield:** CommonJS in a new file, `any` at a boundary, a missing
  `exports` map, or an added framework without repository precedent are
  `SUGGESTION` or `WARNING` findings under `CONTRACT` or `POLICY`.
- **Migration:** a commit that mixes a migration step with a behavior change
  is `WARNING` / `FIX-NOW` / `POLICY`; steps are separate commits.

## Boundary review

Before the first scenario, ask whether the logic belongs in JavaScript:

- Business rules, trusted validation, persistence, or reusable logic placed
  in the browser or a Node adapter is a `SUGGESTION` / `CONTRACT` finding
  (or `WARNING` when the validation is security-relevant) with the
  correction "move to the backend and expose a contract".
- CPU-bound work on the main thread is `WARNING` / `PERFORMANCE`; the
  correction is a Worker or WebAssembly from the backend language.

## Worked example (full form)

```ts
class Panel extends HTMLElement {
    connectedCallback() {
        window.addEventListener("resize", () => this.layout());
        this.timer = setInterval(() => this.poll(), 1000);
    }
}
```

**Context:** A custom element that is created and removed as the user
navigates.

**Runtime sequence:** Each time the element is connected, a new anonymous
listener and a new interval are registered. When the element is removed,
nothing runs; the listener keeps a reference to the element and the interval
keeps polling.

**Failure modes:** Memory grows with every navigation, `poll` keeps hitting
the network for elements that no longer exist, and `layout` runs on detached
nodes. The leak is invisible in unit tests that never disconnect the
element.

**Review directive:** Every listener, timer, observer, and subscription
registered in `connectedCallback` must be released in
`disconnectedCallback`. Require a single `AbortController` per connection
whose signal is passed to listeners and checked by timers, aborted on
disconnect.

**Acceptable correction:** Create `this.controller = new AbortController()`
in `connectedCallback`, pass `{ signal }` to `addEventListener`, clear the
interval and call `this.controller.abort()` in `disconnectedCallback`. Add a
test that connects, disconnects, and asserts no further polling.

**Classification:** `WARNING` / `FIX-NOW` / `LIFECYCLE` / `TRACE`.

## Foundations: correctness

### 1. Promises nobody awaits

**Problem:** An `async` call is made without `await`, `return`, `.then`, or
`.catch`; or a callback passed to `forEach` or `map` is `async` and its
promise is discarded.

**What can happen:** Errors become unhandled rejections, ordering
assumptions break, and "the function returned" does not mean "the work is
done".

**Safer shape:** `await` or return every promise; use `for...of` with
`await`, or `Promise.all` over a mapped array of promises; enable the
linter rule for floating promises when the project allows.

### 2. Equality and coercion traps

**Problem:** `==` against `null`, numbers, or strings; truthiness checks
where `0`, `""`, and `NaN` are valid; `typeof x === "object"` treating
`null` as an object.

**What can happen:** Valid values fall into the wrong branch; `NaN` never
equals itself; arrays and objects compare by identity.

**Safer shape:** `===` and explicit checks (`x == null` only as a deliberate
null-or-undefined test with a comment), `Number.isNaN`, `Array.isArray`.

### 3. `var`, hoisting, and closure capture

**Problem:** `var` declared in a loop and captured by callbacks; functions
relying on hoisting order.

**What can happen:** Every callback sees the last loop value; a call before
the declaration runs with `undefined`.

**Safer shape:** `const`/`let` (block scoped, per-iteration binding) where
the runtime floor allows; in legacy trees, an IIFE or bound argument.

### 4. Mutating shared objects and arrays

**Problem:** A function sorts, splices, or assigns into an object or array
it received; `Array.prototype.sort` called on a caller's array; default
parameter objects shared across calls.

**What can happen:** Callers observe changes they did not make; React and
Solid state updates are missed because the reference did not change.

**Safer shape:** Copy before mutating (`[...arr].sort`, `structuredClone`
or spread for objects), document ownership, freeze constants.

### 5. Floating point and integer limits

**Problem:** Money in floats, `parseInt` without radix, integers above
`Number.MAX_SAFE_INTEGER`, `toFixed` for rounding.

**What can happen:** `0.1 + 0.2 !== 0.3`, silent precision loss on large
ids from a backend, banker's surprises.

**Safer shape:** Integers in minor units or `BigInt`, string ids across the
wire, `Number.parseInt(x, 10)`, explicit rounding helpers.

### 6. `this` binding surprises

**Problem:** A method passed as a callback loses its receiver; arrow
functions used as methods or constructors; `this` in event handlers of
classic functions.

**What can happen:** `TypeError: cannot read properties of undefined`,
handlers acting on the wrong object.

**Safer shape:** Arrow functions for callbacks that need the enclosing
`this`, explicit `bind`, or plain functions with explicit parameters.

### 7. Date and timezone handling

**Problem:** `new Date(string)` with non-ISO input, local-time arithmetic
for calendar math, `getMonth` off-by-one, dates compared with `==`.

**What can happen:** Parsing differs by engine, DST shifts a "day", and
equality never holds.

**Safer shape:** ISO 8601 strings with explicit offsets, UTC methods for
instants, `Intl.DateTimeFormat` for display, `Temporal` where the runtime
floor allows, `getTime()` for comparison.

### 8. Exceptions as strings and swallowed catches

**Problem:** `throw "failed"`, `catch (e) {}` with nothing inside, or a
catch that logs and continues where the caller expected failure.

**What can happen:** No stack trace, no `cause`, failures reported as
success.

**Safer shape:** Throw `Error` subclasses with `cause`, catch specific
conditions, re-throw what you cannot handle, and write the reason next to
an intentional swallow.

### 9. Array holes, `length`, and iteration order

**Problem:** `delete arr[i]`, `for...in` over arrays, relying on object key
order for integer-like keys.

**What can happen:** Holes break `map` and `forEach` expectations,
`for...in` visits inherited properties, integer-like keys are reordered.

**Safer shape:** `splice` or `filter`, `for...of`, `Map` when order and key
types matter.

### 10. Module side effects at import time

**Problem:** A module registers listeners, reads `location`, starts timers,
or mutates globals when imported.

**What can happen:** Import order becomes behavior; tests and SSR import
the module and trigger browser-only code; tree shaking cannot drop it.

**Safer shape:** Export functions and call them from an entry point; mark
side-effect-free packages with `"sideEffects": false` when true.

## Boundaries: resources and lifecycle

### 11. Listeners, timers, and observers without cleanup

**Problem:** `addEventListener`, `setInterval`, `MutationObserver`,
`ResizeObserver`, `IntersectionObserver`, or a subscription registered
without a matching removal at the end of the owner's life.

**What can happen:** Memory leaks, work on detached nodes, duplicate
handlers after re-mount. See the worked example.

**Safer shape:** One `AbortController` per lifetime, passed as `signal`;
`disconnect()` and `clearInterval` in the teardown path; framework cleanup
returns where applicable.

### 12. Missing `AbortSignal` on `fetch` and long operations

**Problem:** A `fetch` or long loop started for a view keeps running after
the view is gone; a retry loop cannot be stopped.

**What can happen:** Responses arrive for dead components, state is written
after unmount, bandwidth and battery are wasted.

**Safer shape:** Pass `signal` to `fetch`, check `signal.aborted` in loops,
treat `AbortError` as cancellation.

### 13. Blocking the main thread

**Problem:** Synchronous JSON parsing of large payloads, tight loops,
regular expressions with catastrophic backtracking, synchronous storage or
XHR on the main thread.

**What can happen:** Frozen UI, dropped frames, watchdog kills on mobile.

**Safer shape:** Chunk work, use a Worker, stream the payload, or move the
computation to WebAssembly or the backend.

### 14. CommonJS and ESM interop

**Problem:** `require` of an ESM-only package, default-import shape
assumptions across the boundary, `__dirname` in ESM, dual packages with
divergent state.

**What can happen:** `ERR_REQUIRE_ESM` on older Node, `undefined` default
exports, two copies of a singleton.

**Safer shape:** Decide the module system per package, use an `exports`
map with conditions, `import.meta.dirname` or `fileURLToPath`, and test the
packed artifact from both module systems when dual is required.

### 15. `any`, `as`, and `!` hiding runtime shapes

**Problem:** External data typed as an interface without a runtime check;
`as` casts to silence the compiler; non-null assertions on values that can
be absent.

**What can happen:** The compiler is satisfied and the runtime crashes on
the first malformed payload; the type lies to every reader.

**Safer shape:** `unknown` at the boundary, type guards or a schema
validator, `as` only with a comment that states why it holds.

### 16. Non-exhaustive unions and enums

**Problem:** A `switch` over a discriminated union without a `never`
default; string literals compared instead of the union.

**What can happen:** A new variant compiles and is silently ignored at
runtime.

**Safer shape:** `default: { const _exhaustive: never = value; }` (or the
project's `assertNever`), exhaustive `switch`, `satisfies` for lookups.

### 17. Public package contract drift

**Problem:** Deep imports work by accident; `exports`, `types`, or `files`
omit what consumers use; declaration output not tested.

**What can happen:** A patch release breaks consumers; types drift from
runtime.

**Safer shape:** An `exports` map that is the whole contract, `files`
whitelist, a test that installs the packed tarball and imports the public
entry points.

### 18. Framework state ownership and effects

**Problem (React):** State duplicated across components, effects that
derive state from props, stale closures in event handlers, unstable keys,
side effects during render.
**Problem (Solid):** Props destructured, signals read outside a tracking
scope, resources not disposed.
**Problem (any framework):** Business logic inside components.

**What can happen:** Out-of-sync UI, infinite effect loops, lost input
focus on re-render, logic that cannot be tested without the framework.

**Safer shape:** Lift state to the lowest common owner, derive during
render instead of in effects, keep logic in plain modules, follow the
framework's documented rules for the version in use.

### 19. Web Component lifecycle gaps

**Problem:** Work in the constructor that touches attributes or children;
no `disconnectedCallback`; attributes and properties out of sync;
`observedAttributes` missing.

**What can happen:** Elements created by the parser behave differently
from elements created by script; leaks on removal; attribute changes
ignored.

**Safer shape:** Constructor sets up state only; DOM and listeners in
`connectedCallback`; cleanup in `disconnectedCallback`; reflect
deliberately.

### 20. Tests that never see a real DOM

**Problem:** Browser code tested with hand-written mocks of the DOM or with
a simulated environment that lacks layout, focus, and real events.

**What can happen:** Keyboard and focus behavior untested; layout-dependent
bugs invisible; accessibility regressions ship.

**Safer shape:** Run DOM tests in a real browser (Playwright or the
project's equivalent) for behavior that depends on layout, focus, or
events; keep simulated environments for pure rendering.

### 21. Environment and globals in tests

**Problem:** Tests set `process.env`, `globalThis`, or `window.location`
directly and share them across files; modules that read the environment at
import time.

**What can happen:** Order-dependent tests, leaked state, a false pass
because the module cached the old value.

**Safer shape:** Per-test setup and teardown with the runner's helpers,
dependency injection for configuration, a child process for import-time
environment when it is the contract.

## Systems: contracts, security, and performance

### 22. DOM injection from untrusted strings

**Problem:** `innerHTML`, `outerHTML`, `insertAdjacentHTML`,
`document.write`, or a template literal building markup from user data.

**What can happen:** DOM-based cross-site scripting; the payload runs with
the page's origin and tokens.

**Safer shape:** `textContent`, `createElement` and property assignment,
a sanitizer the project accepts, Trusted Types or CSP where the project
supports them.

### 23. Unsafe URLs and navigation

**Problem:** User input assigned to `href`, `src`, `location`, or
`window.open` without validation; open redirects via a `next` parameter.

**What can happen:** `javascript:` URLs execute; users are redirected to
attacker sites after login.

**Safer shape:** Parse with `new URL(input, base)`, allowlist protocols and
origins, reject relative redirects outside the site.

### 24. `postMessage` without origin checks

**Problem:** A `message` listener trusts `event.data` without checking
`event.origin`; `postMessage(data, "*")` with sensitive data.

**What can happen:** Any page that can obtain a reference to the window
injects messages or reads secrets.

**Safer shape:** Check `event.origin` against an allowlist, target a
specific origin, validate the payload shape.

### 25. Prototype pollution

**Problem:** Deep merge, `Object.assign` from parsed JSON, or
`obj[key] = value` with attacker-controlled keys such as `__proto__`,
`constructor`, or `prototype`.

**What can happen:** Every object in the realm gains attacker-chosen
properties; authorization checks flip; denial of service.

**Safer shape:** Reject the dangerous keys, use `Object.create(null)` or
`Map` for dictionaries, `structuredClone` instead of home-made deep copies.

### 26. Dynamic code and `eval`

**Problem:** `eval`, `new Function`, string arguments to timers, dynamic
`import()` with user-controlled specifiers.

**What can happen:** Arbitrary code execution; CSP violations that hide
other problems.

**Safer shape:** Data-driven dispatch tables, allowlisted module
specifiers, no code built from strings.

### 27. Secrets and tokens in the client

**Problem:** API keys in the bundle, tokens in `localStorage`, credentials
in query strings, source maps published with secrets in comments.

**What can happen:** Anyone can read them; XSS turns into full account
takeover.

**Safer shape:** Short-lived tokens in `HttpOnly` cookies or memory,
secrets only on the server, source maps controlled at publish time.

### 28. Dependency and install-time trust

**Problem:** A dependency added for a one-line helper; `postinstall`
scripts unreviewed; no lockfile or an unfrozen install in CI; version
ranges that float across majors.

**What can happen:** Code runs on every developer and CI machine at
install; a compromised or typosquatted package ships; builds differ
between machines.

**Safer shape:** Prefer the platform API, review install scripts, commit
the lockfile, frozen installs in CI, the project's audit tool when release
risk is in scope. A clean audit is evidence, not proof.

### 29. Layout thrashing and re-render storms

**Problem:** Reads and writes of layout properties interleaved in a loop;
a framework component re-rendering on every parent update because of
unstable props; observers writing what they observe.

**What can happen:** Forced synchronous layouts, dropped frames, CPU
pegged with nothing visibly changing.

**Safer shape:** Batch reads then writes, `requestAnimationFrame` for
visual updates, stable references for props, profile before optimizing.

### 30. Bundle and payload cost

**Problem:** A whole library imported for one function, polyfills for
targets the project does not support, images and fonts shipped through
JavaScript, no code splitting for rarely used routes.

**What can happen:** Slow first load, especially on mobile; the cost is
paid by every user on every visit.

**Safer shape:** Measure bundle composition, import narrowly, set
browserslist to the real floor, lazy-load rarely used code, ask whether
the code belongs in the client at all.

### 31. Logic that belongs outside JavaScript

**Problem:** Business rules, trusted validation, or CPU-bound computation
implemented in the browser or a Node adapter when a Go, Rust, or Zig
backend exists.

**What can happen:** Rules duplicated across clients, validation bypassed
by calling the API directly, main-thread stalls, and a second implementation
of the domain that drifts from the real one.

**Safer shape:** Move the rule to the backend and call it through a small
contract; compile CPU-bound work to WebAssembly from the backend language;
keep the JavaScript layer thin.

## Cross-cutting directives

### Migration steps that change behavior

**Avoid:** A commit that adopts a formatter, converts CommonJS to ESM, or
adds TypeScript and also fixes a bug or changes logic.

**Context:** Migration commits are large and mechanical; reviewers cannot
see a behavior change inside them. `.git-blame-ignore-revs` will hide the
commit from blame, taking the behavior change with it.

**Runtime sequence:** The suite passes before; the commit reformats
hundreds of files and changes one condition; the suite still passes
because the condition was untested; the regression ships.

**Failure modes:** A regression attributed to "the ESM commit" with no way
to bisect inside it.

**Review directive:** Require the suite green before and after, a diff the
formatter or codemod reproduces exactly for mechanical steps, and behavior
changes in their own commits.

**Classification:** `WARNING` / `FIX-NOW` / `POLICY` / `TRACE`. Promote to
`BLOCKER` when the mechanical commit touches security-sensitive code.

### Legacy trees reformatted as a side effect

**Avoid:** Running `js-check` in writing mode, `prettier --write`, or
`eslint --fix` on a tree whose mode is legacy.

**Failure modes:** A one-line fix arrives with a thousand-line diff, blame
is destroyed, and the reviewer cannot find the fix.

**Review directive:** In legacy mode require `js-check --check` or
`JACAZUL_JS_TS_IGNORE_FORMATTING=1`; reject diffs whose formatting changes
exceed the change's own scope.

**Classification:** `WARNING` / `FIX-NOW` / `POLICY` / `REPRODUCED`.

## Automated review baseline

The verification commands are defined once in
[`SKILL.md`](SKILL.md#-verification-js-check). Repository-configured gates
always take precedence, and `js-check` runs only what the tree declares.

Evidence scope for the tools it may plan:

- `tsc --noEmit`: type consistency on annotated code; `any` and `as` are
  not checked.
- `eslint` / Biome: lints for several scenarios above (floating promises,
  equality, unused variables) when the rules are enabled.
- `prettier --check` / Biome: mechanical style only.
- The project's test runner: behavior verification.
- The project's audit tool: dependency advisories; not proof of application
  security.

## Source index

- [MDN: Web APIs](https://developer.mozilla.org/docs/Web/API) — DOM,
  `AbortController`, `postMessage`, Web Components lifecycle.
- [MDN: JavaScript reference](https://developer.mozilla.org/docs/Web/JavaScript/Reference)
  — equality, `this`, modules, promises.
- [Node.js: ECMAScript modules](https://nodejs.org/api/esm.html) — ESM and
  CommonJS interoperability.
- [Node.js: `package.json` exports](https://nodejs.org/api/packages.html#exports)
- [TypeScript handbook: Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)
- [OWASP DOM-based XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html)
- [OWASP Prototype Pollution Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Prototype_Pollution_Prevention_Cheat_Sheet.html)
- [React docs: Synchronizing with Effects](https://react.dev/learn/synchronizing-with-effects)
- [Solid docs: Reactivity basics](https://docs.solidjs.com/concepts/intro-to-reactivity)
- [typescript-eslint: no-floating-promises](https://typescript-eslint.io/rules/no-floating-promises/)
