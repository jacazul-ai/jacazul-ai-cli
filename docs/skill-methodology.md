# Skill Authoring Methodology

How to create and maintain a skill in this repository, independent of the
skill's subject. Language experts, tutors, workflow skills and the review core
all follow it.

Much of the craft here was adapted from
[`samber/cc-skills-golang`](https://github.com/samber/cc-skills-golang) (MIT,
Copyright (c) 2026 Samuel Berthe), whose `CLAUDE.md` is the most complete
public treatment of skill authoring we have found. Attribution and the pinned
commit live in the [Provenance](#provenance) section. Claims sourced from that
project are marked; everything else is our policy.

## Trigger → Action

### When you write a skill description

The description is the only thing read before the skill loads. Nothing else in
the file matters if selection fails.

1. State what the skill does, then when to use it — in that order.
2. Write in the third person. "I can help you…" and "You can use this to…"
   degrade discovery.
3. Name the concrete nouns someone would actually type: file extensions, tool
   names, import paths, directory names, domain terms.
4. Be insistent inside the skill's own concern. Under-triggering is the
   default failure.
5. Scope against siblings. When two skills overlap, say what each is *not* for
   and name the other one.

Keep it under 1,000 characters. Quote the value when it contains a colon
followed by a space, or starts with `[`, `]`, `<` or `>` — an unquoted one
breaks YAML parsing and the skill drops out of the listing with no error.

### When you write a skill body

- Write imperatively, verb first: `Run`, `Reject`, `Validate`.
- Explain why, not only what. Reasoning lets the model handle edge cases the
  author did not foresee.
- Use one term per concept. Mixing synonyms for the same thing costs accuracy.
- Give one default with an escape hatch, never a menu of five options.
- Assume competence. Cut any paragraph explaining a well-known technology.
- Prefer tables and checklists over prose for enumerable content.
- Match specificity to fragility: prose where many approaches work, an exact
  command where the operation is destructive or order-dependent.
- State facts version-relative, not date-relative. "Go 1.24+" stays true;
  "as of August 2026" goes stale silently because nothing re-validates it.
- Put load-bearing rules early. Compaction keeps the head of a file.

### When you decide between a reference file and a new skill

Three layers carry different costs:

| Layer | Loaded | Cost |
| --- | --- | --- |
| Metadata (`name`, `description`) | At startup, for every installed skill | Permanent, paid in every project |
| Body | On activation | Recurring while the skill is active |
| `references/`, `assets/`, `scripts/` | Only when the body points at them | Paid once, only if actually read |

Start with a reference file. Promote it to its own skill only when it must
trigger *without* its parent being active. Creating a skill in advance of that
need is structure by prediction, which this repository rejects.

Two constraints bound the choice:

- Keep references **one level deep**. A nested chain gets partially read and
  silently truncated, so the deepest content never reaches the model and
  nothing signals the loss.
- Installed-skill count has a ceiling. Past roughly 20–50 skills, discovery
  degrades for *all* of them, including skills unrelated to the new one
  (upstream guidance).

Upstream states that a body stays rendered in context across every turn while
a reference is paid once. Treat that as their documented model of harness
behaviour, not as a verified fact; the reliability argument stands on its own,
because reading a reference is an action the agent takes directly, while
activating another skill depends on the harness choosing to load it.

### When you lay out a skill directory

The target shape is a thin entry point plus topic references:

```
skills/<name>/
  SKILL.md          hub: philosophy, policy boundary, routing table, mandate
  references/       one file per owned topic, one level deep
  CODE-REVIEW.md    only for skills that review code, on the shared scale
```

`PLAYBOOK.md` is the legacy shape. Several skills still carry one, and that is
fine until each is next restructured. Do not recreate a playbook in a skill
that has already moved to `references/`, and do not treat its absence there as
something missing.

`go-expert` is the pilot for this layout. The choice is not arbitrary: a pilot
needs an owner active enough in the subject to judge whether the restructure
preserved conceptual quality, rather than merely counting files. A migration
that splits cleanly but degrades the guidance is a regression only a
practitioner can see.

### When you cross-reference another skill

Each concept lives in exactly one owning skill. Every other skill points at
the owner instead of restating the rule.

Write the reference as a citation in backticks, and say what the reader loses
without it:

```markdown
→ See `owner/repo@skill` for the ownership and lifecycle rules.
```

Never write a bare `@mention`. Harnesses that support `@` references read it
as a force-load directive and pull the whole referenced skill into context,
bypassing triggering and burning the budget.

A reference must degrade gracefully. If the target is not installed, the
sentence should still tell the reader what they are missing.

### When you create a new skill

1. Write the body, then run the description through the checklist above.
2. Check which existing skills should now point at the new one. Where an
   existing skill covers adjacent ground, add the cross-reference rather than
   letting the two drift apart.
3. Update any routing table that maps intent to skill.
4. Follow the update checklist below.

### When you update a skill

1. If scope changed — a topic moved in or out, or a skill was added or
   removed — update the routing table and the boundary section that
   disambiguates competing skills.
2. Verify the frontmatter still parses and still matches the directory name.
3. Update the documentation that describes the skill to users.
4. Record the change where the workflow requires it before closing the task.

### When a skill never triggers

Work down this index. Each row is a failure mode with its correction.

| Symptom | Cause | Fix |
| --- | --- | --- |
| Never triggers | Vague description | Concrete nouns plus an explicit "use when" clause |
| Erratic triggering | First-person description | Rewrite in third person |
| Agent acts without reading the body | Workflow steps in the description | Describe what and when only |
| Silently absent from the listing | Unquoted `:` + space, or leading `[ ] < >` | Quote the description |
| Token bloat, ignored tail | Monolithic body | Split into `references/` |
| Information missing from a reference | Nested reference chain | Flatten to one level |
| Wasted budget | Restating model knowledge | Delete it; assume competence |
| Brittle edge-case handling | `MUST`/`NEVER` in caps everywhere | Explain the reasoning instead |
| Model dithers | A menu of options | One default plus an escape hatch |
| Silently wrong later | Date-relative facts | State them version-relative |
| Budget blown by one reference | `@`-mentioning another skill | Cite the identifier in backticks |
| Discovery degrades everywhere | Too many installed skills | Prune, or demote skills to references |
| Cannot prove the skill helps | No evaluation | Adversarial cases plus a baseline run |
| Effect disappears elsewhere | Validated on one model only | Re-measure per target model |

## Evaluation

An evaluation is adversarial or it is worthless. It must test what the skill
adds, not what the model already knows.

- Design a trap: a task whose natural, lazy implementation is subtly wrong.
  The trap must not instruct the wrong approach explicitly — the skill shifts
  defaults, it cannot override a direct instruction.
- Pre-flight every case *without* the skill. If the baseline passes, cut or
  redesign the case. This is the cheapest quality gate available.
- Isolate the skill under test. Loading a skill that overlaps its content
  inflates the baseline and hides the real uplift.
- Test judgment, not API knowledge. Ask which structure fits, not how to call
  a known function.
- Treat any measured uplift as belonging to the model that produced it.

## What we do not adopt

Upstream practices deliberately left out, so nobody reintroduces them by
accident:

| Not adopted | Reason |
| --- | --- |
| Universal `MUST`/`ALWAYS` framing | Conflicts with separating repository mandate from convention |
| Mandated worktree path for all work | This repository has its own Git workflow |
| Their tooling chain for token counts and linting | Not installed here; gates are repository-configured |
| A router skill that activates other skills | Cascading activation is forbidden by the Horizontal Skill Architecture mandate in `AGENTS.md` |
| Parallel sub-agent dispatch as a default | Not our operating posture |

## Planned: promotion to a skill

Not implemented. This document is the source for a future skill, working name
`skill-expert`, subject-agnostic and serving every skill in `skills/` rather
than any one language.

It stays a document until it has to act rather than be read. That is the same
reference-to-skill promotion rule stated under [When you decide between a
reference file and a new skill](#when-you-decide-between-a-reference-file-and-a-new-skill),
applied to this file: a skill is earned when it must trigger on its own, not
granted in advance because the content looks important enough. Promoting it
now would be structure by prediction, and this document would be the first
thing to reject that.

The trigger for promotion is concrete: an agent needs these rules loaded while
authoring a skill, without a human pointing at the file. Until that happens,
the Skill Authoring mandate in `AGENTS.md` carries the obligation and this
document carries the content.

On promotion, the body moves into the skill, the longer tables become its
`references/`, and the `AGENTS.md` mandate points at the skill instead of at
this file. Nothing here is rewritten in the move.

## Provenance

| Field | Value |
| --- | --- |
| Source | `samber/cc-skills-golang` |
| Reviewed commit | `19a0626ae8565d27a7b7bdf59d8d99d94d7e284c` (2026-09-07) |
| Reviewed on | 2026-09-20 |
| License | MIT, Copyright (c) 2026 Samuel Berthe |
| Citation | DOI 10.5281/zenodo.21605229 |

Re-evaluate against the pinned commit when upstream publishes an update, and
do not reintroduce anything listed under [What we do not
adopt](#what-we-do-not-adopt) without a new decision.

---

**Version:** 0.1.0
**Last Updated:** 2026-09-20
