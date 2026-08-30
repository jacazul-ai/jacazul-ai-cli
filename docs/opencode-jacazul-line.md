# OpenCode jacazul-line

When OpenCode is started through `scripts/jacazul-opencode`, the project TUI
configuration loads `extensions/opencode/jacazul-line.tsx`.

The dashboard appears below OpenCode's native status line as four rows:

1. workflow mode and project;
2. focus scope, plan, short task UUID, and task description;
3. worktree path and branch;
4. model, variant, context usage, token usage, cache reads, and cost.

The extension does not render a `session_prompt_right` replacement, so the
native OpenCode model and session indicators remain intact.

After changing the extension or `tui.json`, quit and restart OpenCode. The TUI
configuration is loaded only during startup.
