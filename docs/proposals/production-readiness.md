# Proposal: Production Readiness Review

**Status:** Proposal, not implemented.
**Audience:** Contributors and agents.
**Related:** `security-expert`, `code-review`, language experts, and repository-specific release gates.
**Inspiration:** [AI Code Finishing Checklist](https://www.finishkit.app/blog/ai-code-finishing-checklist). This link is an input to the proposal, not an endorsed policy or evidence source.

## When working code is being considered for release

Run a production-readiness review that asks a different question from normal
implementation review:

> The feature works in its expected path, but is there enough evidence to
> operate it safely under real users, failures, attackers, and infrastructure?

Do not turn a generic checklist into universal policy. Detect the workload,
exposure, stack, repository mandates, and deployment environment first, then
select only the applicable checks.

## Problem

AI-assisted implementation can produce a convincing happy path while leaving
release-critical boundaries unverified: credentials, authorization, malformed
input, failure handling, migrations, shutdown, observability, deployment, and
recovery. A build or demonstration proves that one path works; it does not
prove that the system is ready to operate.

A fixed count of failed checks is not a useful release model. One exploitable
authorization bypass can block a release, while several missing polish items
may be safely deferred. Consequence, exposure, and evidence must decide the
verdict.

## Proposed ownership model

A future `production-readiness` skill should orchestrate existing experts. It
must not duplicate their technical guidance or become another monolithic
review catalog.

| Readiness area | Primary owner | Typical evidence |
|---|---|---|
| Secrets, credentials, and supply chain | `security-expert` | Secret scan, history review, scoped credential configuration |
| Authentication and authorization | `security-expert` plus the application expert | Unauthorized and cross-tenant request tests, server-side policy trace |
| Language correctness and failure contracts | Matching language expert | Configured formatter, tests, static analysis, error-path tests |
| Concurrency, lifecycle, and shutdown | Matching language expert | Cancellation tests, race evidence, bounded-resource and shutdown tests |
| Build, packaging, and deployment | Repository release/CI policy | Reproducible production build, artifact provenance, staging result |
| Schema and data compatibility | Application and storage owner | Migration rehearsal, rollback or forward-fix plan, compatibility tests |
| Operations and observability | Future operations/observability owner | Readiness and liveness probes, actionable logs, metrics, alerts, runbook |
| User-facing resilience and accessibility | UI/application expert | Loading, empty, offline, error, keyboard, and viewport tests |
| Review disposition | `code-review` | Classified findings with evidence and explicit advisory outcomes |

The orchestrator selects owners and combines their evidence into one release
verdict. Repository policy remains authoritative; conventional checks are
labeled as guidance unless configured or explicitly requested.

## When selecting a readiness profile

Classify the deliverable before choosing gates:

| Profile | Typical concerns |
|---|---|
| Library | API compatibility, supported versions, tests, documentation, package provenance |
| CLI | Exit codes, stdout/stderr contracts, cancellation, filesystem safety, packaging |
| Service/API | Authentication, authorization, validation, timeouts, limits, migrations, probes, observability |
| Worker/daemon | Idempotency, retries, backpressure, poison messages, shutdown, recovery |
| Web application | Server-side authorization, session lifecycle, input/output safety, async UX, accessibility |
| Agent/plugin/skill | Tool permissions, untrusted instructions, secrets reachability, generated artifacts, containment |

A project can combine profiles. For example, a Go service with a browser UI
uses both the service/API and web-application profiles.

## When running the review

1. Read repository policy, release configuration, and the target environment.
2. Identify assets, attacker-controlled inputs, privileged operations,
   persistence surfaces, external dependencies, and failure boundaries.
3. Select the applicable readiness areas and activate their owning experts.
4. Run configured gates first; add conventional checks only when they answer a
   concrete risk question.
5. Record evidence for success and failure paths. Missing evidence remains
   `UNVERIFIED`; an assertion from the implementation agent is not proof.
6. Report findings through the shared `code-review` scale with technical level,
   advisory, area, and evidence.
7. Require each actionable finding to be fixed, converted to linked technical
   debt where deferral is safe, or explicitly accepted with rationale.
8. Produce a release verdict: `READY`, `READY-WITH-ACCEPTED-RISK`, or
   `NOT-READY`.

## When assigning release priority

Do not copy generic `P0`/`P1`/`P2` labels directly into project policy. Map a
check to consequence:

- A credible critical security, authorization, data-integrity, or essential
  availability failure is `BLOCKER` / `FIX-NOW` and makes the verdict
  `NOT-READY` by itself.
- A non-critical but actionable operational weakness is normally `WARNING` /
  `FIX-OR-TECH-DEBT`.
- Scale, polish, or maintainability improvements are `SUGGESTION` or `NIT`
  unless the product contract makes them essential.

The verdict is risk-based, never a count such as “five failed checks are fine.”

## When adapting an external checklist

Treat external checklists as discovery material, not authority:

- Replace framework-specific commands with repository-configured equivalents.
- Replace broad rules such as “sanitize all data” with explicit validation,
  normalization, parameterization, and output-encoding boundaries.
- Distinguish liveness from readiness; a liveness probe should not create a
  cascading restart because a dependency is temporarily unavailable.
- Treat grep patterns as triage, not proof that secrets or vulnerabilities are
  absent.
- Verify statistical or security claims against authoritative sources before
  using them to set policy.
- Do not install scanners, test libraries, or deployment tooling without the
  normal project and environment authorization gates.

## Proposed deliverables

1. Define the cross-language readiness profiles and owner routing.
2. Add adversarial evaluations that distinguish happy-path completion from
   release readiness.
3. Implement a read-only readiness report before any automatic remediation.
4. Integrate configured project gates without inventing new mandatory tools.
5. Add machine-readable report output only after the human-readable contract
   stabilizes.
6. Pilot the workflow on a sandbox service before applying it to production
   repositories.

## Out of scope

- Claiming formal compliance or penetration-test coverage.
- Replacing language, security, operations, or UI experts.
- Mandating a web framework, cloud provider, CI platform, or observability
  stack.
- Automatically changing credentials, production infrastructure, schemas, or
  release state.
- Declaring readiness from checklist completion without reproducible evidence.

## Open questions

- Should readiness be a standalone skill, a `code-review` mode, or both?
- Which profiles belong in the first implementation?
- How should repository-specific gates declare their evidence and expiration?
- Should a readiness report become a Taskwarrior artifact, a generated file,
  or both?
- What minimum repeatability is required before an AI-judged readiness check
  can influence a release verdict?
