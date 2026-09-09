---
name: jacazul-ui
description: Natural-language routing between assistant conversation and Jacazul host UI events.
license: MIT
---

# Jacazul UI Dispatch

## Role

When a supported host exposes the Jacazul UI, separate normal conversation
from short operational notifications.

- Normal explanations, answers, plans, and summaries are assistant text. They
  belong in the host transcript.
- Short status changes, blockers, and completed milestones may be sent through
  the `jacazul_alert` tool. The host renders those as a temporary UI alert.
- The user does not need to know the tool name or a wire-format marker. Interpret
  natural language intent and choose the correct channel.

## Natural-language routing

Translate intent, not exact phrases:

| User intent | Channel |
|---|---|
| Ask a question or request an explanation | Normal assistant response |
| Ask to see or receive an answer in chat | Normal assistant response |
| Ask to be warned, notified, or alerted about a short event | `jacazul_alert` |
| Report a worker milestone or completion | `jacazul_alert` when a short alert is useful |
| Report a blocker requiring attention | `jacazul_alert` |
| Provide a long result, code, log, or explanation | Normal assistant response |

Examples of natural requests that can justify an alert:

- "Me avisa quando terminar."
- "Mostra um alerta quando esse worker concluir."
- "Me alerta se der erro."
- "Coloca isso como notificação."

### Immediate alert intent (mandatory)

When the user explicitly asks for an alert now, call `jacazul_alert` immediately
before writing a normal assistant response. Do not answer with prose first and
do not substitute another channel.

This rule includes direct requests such as:

- "me manda um alert";
- "manda um alerta";
- "faz um teste no alert";
- "me avisa agora";
- "coloca isso no alert".

For an immediate alert request, do not use shell commands, `tmux send-keys`,
Neovim remote expressions, or prompt-buffer mutation. The alert tool is the
only delivery path. If the tool is unavailable, report that limitation instead
of pretending that an alert was displayed.

A deferred request means: remember the requested notification condition and call
`jacazul_alert` only when that condition occurs. Do not emit an alert
immediately unless the user asked for an immediate notification.

## `jacazul_alert` usage

When the tool is available, call it with a short message and severity:

```text
message: a concise user-visible status
notifyType: info | warning | error
```

Use:

- `info` for normal milestones and completion;
- `warning` for attention, delay, or degraded operation;
- `error` for a failure or blocked run.

The host controls placement, rendering, and expiration. Do not include terminal
control sequences, secrets, credentials, or large transcripts in an alert.

## Protocol boundary

Do not encode actions in assistant prose, XML markers, or ad-hoc JSON blocks
such as `<JACAZUL_ACTION>`. Do not ask the user to format a tool command when
their natural-language intent is sufficient.

The technical path is owned by the host integration:

```text
natural language
→ this routing skill
→ jacazul_alert tool
→ Pi ctx.ui.notify()
→ extension_ui_request
→ Jacazul host UI
```

The tool is a narrow UI capability. It is not permission to execute arbitrary
Neovim commands, edit files, run shell commands, or change workflow state.

## Host availability

If the Jacazul UI or `jacazul_alert` tool is unavailable:

- keep the normal response in the transcript;
- do not pretend that an alert was displayed;
- explain the limitation only when it affects the user's request.

## Compatibility

This skill is shared by the Jacazul CLI and supported harnesses. The skill can
be loaded and used without `jacazul.nvim`. When `jacazul.nvim` is the host, its
coordinator owns the event interpretation and float rendering.
