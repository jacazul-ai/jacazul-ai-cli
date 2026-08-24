---
date: YYYY-MM-DD
timezone: UTC
model: <current model id>
provider: <provider>
persona: <active persona>
client: <claude|pi|gemini|copilot|other>
runtime_mode: <COUNSELOR|UNHINGED>
project: <project name>
plan: <plan name>
task: <task description>
ticket: <#id or none>
human_intervention: <none|minimal|guided|high>
source_session: <session id or none>
status: <observed|validated|promoted>
---

# Testimony: <short mission title>

This record preserves a real execution that teaches an agent how to cross a
similar mission from a cold start. Keep the narrative factual and retain the
evidence needed to distinguish repeatable behavior from a one-off success.

## Mission

### Objective

What had to be true at the end?

### Starting state

What did the agent know, what was anchored, and what was deliberately unknown?

### Entry signals

What words, task mode, ticket, error, or repository state should trigger this
playbook?

## Autonomous execution

### Context resolution

What did the agent read before acting? Include focus, task context, inherited
notes, repository state, and relevant skills.

### Action loop

List the actions in order. Each step must be executable by a cold-start agent.

1. <action>
2. <action>
3. <action>

### Decision gates

Record the points where the agent had to choose a path, including the evidence
used and the rejected alternatives.

| Gate | Evidence | Decision | Rejected path |
|---|---|---|---|
| <decision point> | <observed state> | <chosen action> | <alternative and why> |

### Failure and recovery

For every failure, record the command or symptom, the interpretation, the
corrective action, and the verification that closed the loop.

| Symptom | Meaning | Recovery | Verification |
|---|---|---|---|
| <failure> | <tactical interpretation> | <fix> | <proof> |

## Validation and outcome

### Quality gates

- Tests: <commands and results>
- Lint/format: <commands and results>
- Security or safety checks: <commands and results>
- Documentation check: <updated docs or reason not applicable>

### Result

What changed, what was verified, and what remains open?

### Evidence

Link or quote the durable evidence: commit, diff, test output, task outcome,
issue, logs, or screenshots. Do not paste secrets or private credentials.

## Distilled playbook

This is the part an agent can reuse. Remove story and keep operational rules.

### Trigger

When the agent sees <signal>, it should begin with <first action>.

### Cold-start procedure

1. <orient and resolve context>
2. <perform the core action>
3. <run the decision gate>
4. <validate the result>
5. <record outcome and preserve focus>

### Non-negotiable invariants

- <rule that must hold>
- <rule that must hold>
- <safety boundary>

### Anti-patterns

- Do not <failure mode>.
- Do not <failure mode>.

### Promotion candidate

State the smallest rule that should be promoted into an agent template or skill.
Do not promote the entire narrative automatically.

## Limits and transferability

### What generalizes

Which parts apply to other projects, runtimes, personas, or models?

### What does not generalize

Which parts depend on this repository, ticket, tool, or environment?

### Follow-up

What should be tested in the next similar mission before promoting the rule?
