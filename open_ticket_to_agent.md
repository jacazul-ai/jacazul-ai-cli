AGENT RULE: Block `taskp delete` - Redirect to `tw-flow discard`

TRIGGER:
Any agent attempts to run `taskp delete<uuid>` or `taskp delete<id>`.

ACTION:
BLOCK the command. Do NOT execute it.

ERROR as PROMPT (output this message):
  Blocked: `taskp delete` is forbidden.
  Raw deletion bypasses tw-flow safety checks and context propagation.
  Use: tw-flow discard <uuid>
  If the task has no outcome and cannot be discarded, investigate why before
  deleting.

RATIONALE:
`taskp delete` is a raw Taskwarrior command that hard-deletes a task record,
bypassing all tw-flow abstractions (context propagation, plan integrity, focus
anchors). `tw-flow discard` is the safe equivalent - it performs the same
deletion through the workflow layer with proper checks.

SCOPE:
Applies to ALL agents in ALL modes (COUNSELOR and UNHINGED).
No exceptions. Even orphan/noise tasks must go through `tw-flow discard`.
