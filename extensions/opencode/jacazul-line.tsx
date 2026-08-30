/**
 * jacazul-line for OpenCode.
 *
 * Native TUI footer plugin inspired by extensions/pi/jacazul-line.ts.
 * It keeps the workflow identity visible while leaving the message viewport
 * and OpenCode's native keybindings untouched.
 */

import type { TuiPluginModule, TuiPluginApi } from "@opencode-ai/plugin/tui";
import { createMemo } from "solid-js";
import { execFile } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { basename } from "node:path";

function shortenHome(path: string): string {
  const home = process.env.HOME;
  return home && path.startsWith(home) ? `~${path.slice(home.length)}` : path;
}

function getFocus(): { plan?: string; task?: string; independent: boolean } {
  const projectId = process.env.PROJECT_ID;
  const home = process.env.HOME;
  const sessionId = process.env.JACAZUL_SESSION_ID;

  if (!projectId || !home) return { independent: Boolean(sessionId) };

  const taskDir = `${home}/.jacazul-ai/.task/${projectId}`;
  const independentPath = sessionId ? `${taskDir}/focus-${sessionId}.json` : undefined;
  const globalPath = `${taskDir}/focus.json`;
  const focusPath = independentPath && existsSync(independentPath) ? independentPath : globalPath;

  try {
    const focus = JSON.parse(readFileSync(focusPath, "utf8")) as {
      focused_plan?: string;
      focused_task_uuid?: string;
    };
    return {
      plan: focus.focused_plan,
      task: focus.focused_task_uuid,
      independent: Boolean(independentPath && focusPath === independentPath),
    };
  } catch {
    return { independent: Boolean(independentPath && focusPath === independentPath) };
  }
}

const taskDescriptions = new Map<string, string | undefined>();
const pendingTaskDescriptions = new Set<string>();

function getTaskDescription(
  projectId: string,
  uuid: string | undefined,
  onResolved: () => void,
): string | undefined {
  if (!uuid) return undefined;
  if (taskDescriptions.has(uuid)) return taskDescriptions.get(uuid);
  if (!pendingTaskDescriptions.has(uuid)) {
    pendingTaskDescriptions.add(uuid);
    execFile("taskp", [uuid, "export"], {
      env: { ...process.env, PROJECT_ID: projectId },
      timeout: 1000,
    }, (error, stdout) => {
      let description: string | undefined;
      if (!error) {
        try {
          description = (JSON.parse(stdout) as Array<{ description?: string }>)[0]?.description;
        } catch {
          description = undefined;
        }
      }
      taskDescriptions.set(uuid, description);
      pendingTaskDescriptions.delete(uuid);
      onResolved();
    });
  }
  return undefined;
}

function formatTokens(count: number): string {
  if (count < 1000) return count.toString();
  if (count < 1000000) return `${Math.round(count / 1000)}k`;
  return `${(count / 1000000).toFixed(1).replace(".0", "")}M`;
}

function View(props: { api: TuiPluginApi }) {
  const theme = () => props.api.theme.current;
  const focus = createMemo(getFocus);
  const project = process.env.PROJECT_ID ?? "unknown-project";
  const mode = process.env.JACAZUL_MODE ?? "COUNSELOR";
  const session = createMemo(() => {
    const route = props.api.route.current;
    return route.name === "session" ? props.api.state.session.get(route.params.sessionID) : undefined;
  });
  const taskDescription = createMemo(() =>
    getTaskDescription(project, focus().task, () => props.api.renderer.requestRender()),
  );
  const branch = createMemo(() => props.api.state.vcs?.branch);
  const worktree = createMemo(() => basename(props.api.state.path.worktree));
  const runtime = createMemo(() => {
    const current = session();
    const tokens = current?.tokens;
    const provider = current?.model
      ? props.api.state.provider.find((item) => item.id === current.model?.providerID)
      : undefined;
    const model = current?.model?.id ?? "no-model";
    const variant = current?.model?.variant;
    const modelConfig = current?.model
      ? provider?.models?.[current.model.id]
      : undefined;
    const contextWindow = modelConfig?.limit?.context ?? 0;
    const contextUsed = (tokens?.input ?? 0) + (tokens?.cache.read ?? 0);
    const context = contextWindow
      ? `ctx ${(contextUsed / contextWindow * 100).toFixed(1)}%/${formatTokens(contextWindow)}`
      : "ctx ?/?";
    const usage = tokens
      ? `↑${formatTokens(tokens.input)} ↓${formatTokens(tokens.output)} R${formatTokens(tokens.cache.read)} $${(current?.cost ?? 0).toFixed(3)}`
      : "usage ?";
    return [model, variant, context].filter(Boolean).join(" · ") + ` | ${usage}`;
  });

  return (
    <box
      width="100%"
      paddingTop={1}
      paddingBottom={1}
      paddingLeft={2}
      paddingRight={2}
      flexDirection="column"
      gap={0}
    >
      <box flexDirection="row" gap={2}>
        <text fg={theme().accent}>🐊 {mode}</text>
        <text fg={theme().textMuted}>| {project}</text>
      </box>
      <box flexDirection="row" gap={2}>
        <text fg={theme().accent}>🎯 focus{focus().independent ? " (independent)" : ""}</text>
        <text fg={theme().textMuted}>
          | {focus().plan ?? "none"}
          {focus().task ? ` | ${focus().task.slice(0, 8)}` : ""}
          {taskDescription() ? ` ${taskDescription()}` : ""}
        </text>
      </box>
      <box flexDirection="row" gap={2}>
        <text fg={theme().accent}> worktree</text>
        <text fg={theme().textMuted}>| {shortenHome(props.api.state.path.worktree)} | {worktree()}({branch() ?? "-"})</text>
      </box>
      <box flexDirection="row" gap={2}>
        <text fg={theme().accent}>🤖</text>
        <text fg={theme().textMuted}>| {runtime()}</text>
      </box>
    </box>
  );
}

const tui: TuiPluginModule = {
  id: "jacazul-line",
  tui: async (api) => {
    api.slots.register({
      order: 100,
      slots: {
        home_footer() {
          return <View api={api} />;
        },
      },
    });
  },
};

export default tui;
