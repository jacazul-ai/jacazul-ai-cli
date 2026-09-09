/**
 * jacazul-line for OpenCode.
 *
 * Four-row Jacazul workflow dashboard rendered through OpenCode's
 * app_bottom slot (global app frame, below the active route on every
 * route). NOTE: home_footer was tried first and is a dead end: it only
 * renders on the home route and is a single_winner slot already claimed
 * by OpenCode's own internal plugin (order:100, earlier registration),
 * so an external renderer there is never invoked. app_bottom renders in
 * append mode, so registrants coexist. Feature and visual parity port of
 * extensions/pi/jacazul-line.ts:
 * - Fixed palette: lime accent, light-gray values, gray separators.
 * - Git state detection by filesystem walk: repo vs worktree vs bare.
 * - Focus plan and task description resolved through taskp with TTL cache.
 * - Runtime metrics aggregated from session assistant messages.
 * - Width-aware truncation with a gray ellipsis on every row.
 *
 * Known parity gaps vs Pi (documented in task 0f1b50dd outcome):
 * - Pi renders other extensions' status lines; the OpenCode plugin API
 *   exposes no equivalent accessor.
 * - Pi uses Nerd Font section icons; text labels are used here so the
 *   footer survives terminals without patched fonts.
 */

import type { TuiPluginApi, TuiPluginModule } from "@opencode-ai/plugin/tui";
import { createMemo, createSignal, onCleanup } from "solid-js";
import { execFile } from "node:child_process";
import { existsSync, readFileSync, statSync } from "node:fs";
import { basename, dirname, join, resolve } from "node:path";

const PALETTE = {
  lime: "#98C379",
  lightGray: "#B2B2B2",
  gray: "#8C8C8C",
  warning: "#E5C015",
};

type GitKind = "repo" | "worktree" | "none";

type GitInfo = {
  kind: GitKind;
  repoRoot: string | null;
  commonGitDir: string | null;
  worktreeName: string | null;
  insideBareContainer: boolean;
};

type FocusInfo = {
  plan?: string;
  taskUuid?: string;
  independent: boolean;
};

type FocusFile = {
  focused_plan?: string;
  focused_task_uuid?: string;
};

type Segment = {
  text: string;
  color: string;
};

type TaskDescriptionCacheEntry = {
  description?: string;
  checkedAt: number;
  pending?: boolean;
};

const TASK_DESCRIPTION_CACHE = new Map<string, TaskDescriptionCacheEntry>();
const TASK_DESCRIPTION_CACHE_TTL_MS = 30000;
const FOOTER_POLL_MS = 5000;
const FOOTER_HORIZONTAL_PADDING = 2;

function accent(text: string): Segment {
  return { text, color: PALETTE.lime };
}

function value(text: string): Segment {
  return { text, color: PALETTE.lightGray };
}

function quiet(text: string): Segment {
  return { text, color: PALETTE.gray };
}

function warning(text: string): Segment {
  return { text, color: PALETTE.warning };
}

function separator(): Segment {
  return { text: " | ", color: PALETTE.gray };
}

function joinSegments(parts: Array<Segment | null | undefined>): Segment[] {
  const segments: Segment[] = [];
  for (const part of parts) {
    if (!part) continue;
    if (segments.length > 0) segments.push(separator());
    segments.push(part);
  }
  return segments;
}

function isWideCodePoint(cp: number): boolean {
  return (
    (cp >= 0x1100 && cp <= 0x115f) ||
    (cp >= 0x2e80 && cp <= 0xa4cf && cp !== 0x303f) ||
    (cp >= 0xac00 && cp <= 0xd7a3) ||
    (cp >= 0xf900 && cp <= 0xfaff) ||
    (cp >= 0xfe30 && cp <= 0xfe6f) ||
    (cp >= 0xff00 && cp <= 0xff60) ||
    (cp >= 0xffe0 && cp <= 0xffe6) ||
    (cp >= 0x1f300 && cp <= 0x1f9ff) ||
    cp >= 0x20000
  );
}

function charWidth(ch: string): number {
  const cp = ch.codePointAt(0) ?? 0;
  if (cp === 0x200d || cp === 0xfe0e || cp === 0xfe0f) return 0;
  return isWideCodePoint(cp) ? 2 : 1;
}

function cellWidth(text: string): number {
  let width = 0;
  for (const ch of text) width += charWidth(ch);
  return width;
}

function cutToWidth(text: string, maxWidth: number): string {
  let width = 0;
  let cut = "";
  for (const ch of text) {
    const w = charWidth(ch);
    if (width + w > maxWidth) break;
    cut += ch;
    width += w;
  }
  return cut;
}

function fit(segments: Segment[], width: number): Segment[] {
  let total = 0;
  for (const segment of segments) total += cellWidth(segment.text);
  if (total <= width) return segments;

  const budget = Math.max(0, width - 1);
  const trimmed: Segment[] = [];
  let used = 0;
  for (const segment of segments) {
    const w = cellWidth(segment.text);
    if (used + w <= budget) {
      trimmed.push(segment);
      used += w;
      continue;
    }
    const remaining = budget - used;
    if (remaining > 0) {
      trimmed.push({ text: cutToWidth(segment.text, remaining), color: segment.color });
    }
    break;
  }
  trimmed.push({ text: "…", color: PALETTE.gray });
  return trimmed;
}

function formatTokens(count: number): string {
  if (count < 1000) return count.toString();
  if (count < 10000) return `${(count / 1000).toFixed(1)}k`;
  if (count < 1000000) return `${Math.round(count / 1000)}k`;
  if (count < 10000000) return `${(count / 1000000).toFixed(1)}M`;
  return `${Math.round(count / 1000000)}M`;
}

function shortenHome(path: string): string {
  const home = process.env.HOME || process.env.USERPROFILE;
  if (home && path.startsWith(home)) return `~${path.slice(home.length)}`;
  return path;
}

function shortUuid(uuid: string): string {
  return uuid.slice(0, 8);
}

function readJsonFile<T>(path: string): T | null {
  try {
    return JSON.parse(readFileSync(path, "utf8")) as T;
  } catch {
    return null;
  }
}

function sanitizeText(text: string): string {
  return text.replace(/[\r\n\t]/g, " ").replace(/ +/g, " ").trim();
}

function getFocusInfo(): FocusInfo {
  const projectId = process.env.PROJECT_ID;
  const sessionId = process.env.JACAZUL_SESSION_ID;
  const home = process.env.HOME;

  if (!projectId || !home) return { independent: Boolean(sessionId) };

  const taskDir = join(home, ".jacazul-ai", ".task", projectId);
  const independentPath = sessionId ? join(taskDir, `focus-${sessionId}.json`) : null;
  const globalPath = join(taskDir, "focus.json");
  const focusPath = independentPath && existsSync(independentPath) ? independentPath : globalPath;
  const focus = readJsonFile<FocusFile>(focusPath);

  return {
    plan: focus?.focused_plan || undefined,
    taskUuid: focus?.focused_task_uuid || undefined,
    independent: Boolean(independentPath && existsSync(independentPath)),
  };
}

function requestTaskDescription(
  projectId: string,
  uuid: string,
  onResolved: () => void,
): string | undefined {
  if (!/^[0-9a-f-]{36}$/i.test(uuid)) return undefined;

  const cacheKey = `${projectId}:${uuid}`;
  const cached = TASK_DESCRIPTION_CACHE.get(cacheKey);
  const now = Date.now();
  if (cached && now - cached.checkedAt < TASK_DESCRIPTION_CACHE_TTL_MS) {
    return cached.description;
  }
  if (cached?.pending) return cached.description;

  TASK_DESCRIPTION_CACHE.set(cacheKey, {
    description: cached?.description,
    checkedAt: cached?.checkedAt ?? 0,
    pending: true,
  });

  execFile("taskp", [uuid, "export"], {
    env: { ...process.env, PROJECT_ID: projectId },
    timeout: 1000,
  }, (error, stdout) => {
    let description: string | undefined;
    if (!error) {
      try {
        const tasks = JSON.parse(stdout) as Array<{ description?: string }>;
        description = tasks[0]?.description || undefined;
      } catch {
        description = undefined;
      }
    }

    TASK_DESCRIPTION_CACHE.set(cacheKey, {
      description: description ? sanitizeText(description) : undefined,
      checkedAt: Date.now(),
      pending: false,
    });
    onResolved();
  });

  return cached?.description;
}

function findGitInfo(cwd: string): GitInfo {
  let dir = cwd;
  while (true) {
    const gitPath = join(dir, ".git");
    if (existsSync(gitPath)) {
      try {
        const stat = statSync(gitPath);
        if (stat.isFile()) {
          const content = readFileSync(gitPath, "utf8").trim();
          if (content.startsWith("gitdir: ")) {
            const gitDir = resolve(dir, content.slice(8).trim());
            const commonDirPath = join(gitDir, "commondir");
            const commonGitDir = existsSync(commonDirPath)
              ? resolve(gitDir, readFileSync(commonDirPath, "utf8").trim())
              : gitDir;
            const repoRoot = dirname(commonGitDir);
            return {
              kind: "worktree",
              repoRoot,
              commonGitDir,
              worktreeName: basename(dir),
              insideBareContainer: dir === repoRoot,
            };
          }
        }

        if (stat.isDirectory()) {
          return {
            kind: "repo",
            repoRoot: dir,
            commonGitDir: gitPath,
            worktreeName: null,
            insideBareContainer: false,
          };
        }
      } catch {
        return {
          kind: "none",
          repoRoot: null,
          commonGitDir: null,
          worktreeName: null,
          insideBareContainer: false,
        };
      }
    }

    const parent = dirname(dir);
    if (parent === dir) {
      return {
        kind: "none",
        repoRoot: null,
        commonGitDir: null,
        worktreeName: null,
        insideBareContainer: false,
      };
    }
    dir = parent;
  }
}

function splitConfiguredModel(model: string | undefined): { providerID?: string; modelID?: string } {
  if (!model) return {};
  const slash = model.indexOf("/");
  if (slash === -1) return { modelID: model };
  return { providerID: model.slice(0, slash), modelID: model.slice(slash + 1) };
}

function View(props: { api: TuiPluginApi }) {
  const api = props.api;
  const projectId = process.env.PROJECT_ID || basename(api.state.path.directory || process.cwd());
  const mode = process.env.JACAZUL_MODE || "COUNSELOR";

  const [tick, setTick] = createSignal(0);
  const refresh = () => {
    setTick((current) => current + 1);
    api.renderer.requestRender();
  };

  const [termWidth, setTermWidth] = createSignal(
    api.renderer.width || process.stdout.columns || 80,
  );
  const rendererEvents = api.renderer as unknown as {
    on?: (event: string, handler: () => void) => void;
    off?: (event: string, handler: () => void) => void;
  };
  const handleResize = () => {
    setTermWidth(api.renderer.width || process.stdout.columns || 80);
    api.renderer.requestRender();
  };
  rendererEvents.on?.("resize", handleResize);
  const pollTimer = setInterval(refresh, FOOTER_POLL_MS);
  onCleanup(() => {
    rendererEvents.off?.("resize", handleResize);
    clearInterval(pollTimer);
  });

  const focus = createMemo<FocusInfo>(() => {
    tick();
    return getFocusInfo();
  });

  const focusedTask = createMemo<Segment | null>(() => {
    tick();
    const uuid = focus().taskUuid;
    if (!uuid) return null;
    const short = shortUuid(uuid);
    const description = requestTaskDescription(projectId, uuid, refresh);
    return value(description ? `${short} ${description}` : `${short} loading task…`);
  });

  const branch = createMemo(() => {
    tick();
    return api.state.vcs?.branch;
  });

  const git = createMemo(() => {
    tick();
    return findGitInfo(api.state.path.directory || api.state.path.worktree || process.cwd());
  });

  const runtime = createMemo(() => {
    tick();
    const route = api.route.current;
    const sessionID =
      route.name === "session" ? (route.params?.sessionID as string | undefined) : undefined;

    let input = 0;
    let output = 0;
    let cacheRead = 0;
    let cacheWrite = 0;
    let cost = 0;
    let providerID: string | undefined;
    let modelID: string | undefined;
    let variant: string | undefined;
    let contextUsed = 0;

    if (sessionID) {
      for (const message of api.state.session.messages(sessionID)) {
        if (message.role !== "assistant") continue;
        input += message.tokens.input ?? 0;
        output += message.tokens.output ?? 0;
        cacheRead += message.tokens.cache.read ?? 0;
        cacheWrite += message.tokens.cache.write ?? 0;
        cost += message.cost ?? 0;
        providerID = message.providerID;
        modelID = message.modelID;
        variant = message.variant;
        contextUsed = (message.tokens.input ?? 0)
          + (message.tokens.cache.read ?? 0)
          + (message.tokens.cache.write ?? 0);
      }
    }

    if (!modelID) {
      const configured = splitConfiguredModel(
        (api.state.config as unknown as { model?: string }).model,
      );
      providerID = configured.providerID;
      modelID = configured.modelID;
    }

    const contextWindow = providerID && modelID
      ? api.state.provider.find((item) => item.id === providerID)?.models?.[modelID]?.limit?.context ?? 0
      : 0;
    const contextLabel = contextWindow && sessionID
      ? `ctx ${((contextUsed / contextWindow) * 100).toFixed(1)}%/${formatTokens(contextWindow)}`
      : contextWindow
        ? `ctx ?/${formatTokens(contextWindow)}`
        : "ctx ?/?";

    const modelParts = [modelID ?? "no-model", variant, contextLabel].filter(Boolean);

    const usageParts: string[] = [];
    if (input) usageParts.push(`↑${formatTokens(input)}`);
    if (output) usageParts.push(`↓${formatTokens(output)}`);
    if (cacheRead) usageParts.push(`R${formatTokens(cacheRead)}`);
    if (cacheWrite) usageParts.push(`W${formatTokens(cacheWrite)}`);
    if (cost) usageParts.push(`$${cost.toFixed(3)}`);

    return joinSegments([
      accent("🤖"),
      value(modelParts.join(" · ")),
      usageParts.length ? value(usageParts.join(" ")) : null,
    ]);
  });

  const rows = createMemo<Segment[][]>(() => {
    const width = Math.max(
      1,
      (api.renderer.width || termWidth()) - FOOTER_HORIZONTAL_PADDING * 2,
    );

    const workflowRow = joinSegments([
      accent(`🐊 ${mode}`),
      value(projectId),
    ]);

    const focusLabel = focus().independent ? "🎯 focus (independent)" : "🎯 focus";
    const focusRow = focus().plan || focus().taskUuid
      ? joinSegments([
        accent(focusLabel),
        focus().plan ? value(focus().plan) : null,
        focusedTask(),
      ])
      : joinSegments([quiet(focusLabel), value("none")]);

    const info = git();
    const currentBranch = branch();
    let gitRow: Segment[];
    if (info.kind === "worktree") {
      const repoIdentity = shortenHome(info.repoRoot ?? info.commonGitDir ?? api.state.path.worktree);
      const worktree = info.worktreeName ?? basename(api.state.path.worktree || process.cwd());
      const worktreeLabel = currentBranch ? `${worktree}(${currentBranch})` : worktree;
      gitRow = info.insideBareContainer
        ? joinSegments([
          warning("⚠️ bare container"),
          warning(repoIdentity),
          warning(worktreeLabel),
        ])
        : joinSegments([
          accent("worktree"),
          value(repoIdentity),
          value(worktreeLabel),
        ]);
    } else if (info.kind === "repo") {
      gitRow = joinSegments([
        accent("repo"),
        value(shortenHome(info.repoRoot ?? api.state.path.worktree)),
        currentBranch ? value(`branch ${currentBranch}`) : null,
      ]);
    } else {
      gitRow = joinSegments([
        accent("📁 path"),
        value(shortenHome(api.state.path.directory || process.cwd())),
      ]);
    }

    return [workflowRow, focusRow, gitRow, runtime()].map((row) => fit(row, width));
  });

  return (
    <box
      flexDirection="column"
      width="100%"
      paddingLeft={FOOTER_HORIZONTAL_PADDING}
      paddingRight={FOOTER_HORIZONTAL_PADDING}
    >
      {rows().map((row) => (
        <box flexDirection="row" width="100%">
          {row.map((segment) => (
            <text fg={segment.color}>{segment.text}</text>
          ))}
        </box>
      ))}
    </box>
  );
}

const tui: TuiPluginModule = {
  id: "jacazul-line",
  tui: async (api) => {
    api.slots.register<{ app_bottom: {} }>({
      order: 100,
      slots: {
        app_bottom() {
          return <View api={api} />;
        },
      },
    });
  },
};

export default tui;
