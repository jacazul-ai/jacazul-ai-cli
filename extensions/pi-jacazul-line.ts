/**
 * pi-jacazul-line
 *
 * Jacazul workflow dashboard footer for Pi.
 *
 * Design direction:
 * - Multi-line dashboard, not a strict lualine clone.
 * - No powerline separators by default; they are noisy across multiple rows.
 * - Prioritize Jacazul workflow state: PROJECT_ID, mode, focus, and session scope.
 * - Preserve Pi runtime stats and make Git/worktree state first-class.
 */

import type { AssistantMessage } from "@earendil-works/pi-ai";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { truncateToWidth } from "@earendil-works/pi-tui";
import { execFile } from "node:child_process";
import { existsSync, readFileSync, statSync } from "node:fs";
import { basename, dirname, join, resolve } from "node:path";

const PALETTE = {
	lime: "#98C379",
	mediumGray: "#2C323C",
	lightGray: "#B2B2B2",
	gray: "#8C8C8C",
	white: "#FFFFFF",
	black: "#000000",
};

type GitKind = "repo" | "worktree" | "none";

type GitInfo = {
	kind: GitKind;
	repoRoot: string | null;
	commonGitDir: string | null;
	worktreeName: string | null;
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

type TaskDescriptionCacheEntry = {
	description?: string;
	checkedAt: number;
	pending?: boolean;
};

const TASK_DESCRIPTION_CACHE = new Map<string, TaskDescriptionCacheEntry>();
const TASK_DESCRIPTION_CACHE_TTL_MS = 30000;

function hexToRgb(hex: string): [number, number, number] {
	const clean = hex.replace(/^#/, "");
	return [
		Number.parseInt(clean.slice(0, 2), 16),
		Number.parseInt(clean.slice(2, 4), 16),
		Number.parseInt(clean.slice(4, 6), 16),
	];
}

function style(text: string, fgHex: string, bgHex?: string): string {
	const [fr, fg, fb] = hexToRgb(fgHex);
	let prefix = `\x1b[38;2;${fr};${fg};${fb}m`;
	if (bgHex) {
		const [br, bg, bb] = hexToRgb(bgHex);
		prefix += `\x1b[48;2;${br};${bg};${bb}m`;
	}
	return `${prefix}${text}\x1b[0m`;
}

function label(text: string): string {
	return style(text, PALETTE.gray);
}

function value(text: string): string {
	return style(text, PALETTE.lightGray);
}

function accent(text: string): string {
	return style(text, PALETTE.lime);
}

function sep(): string {
	return style(" | ", PALETTE.gray);
}

function dot(): string {
	return style(" · ", PALETTE.gray);
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
			description,
			checkedAt: Date.now(),
			pending: false,
		});
		onResolved();
	});

	return cached?.description;
}

function formatFocusedTask(projectId: string, uuid: string, onResolved: () => void): string {
	const short = shortUuid(uuid);
	const description = requestTaskDescription(projectId, uuid, onResolved);
	return description ? `${short} ${description}` : `${short} loading task…`;
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
						return {
							kind: "worktree",
							repoRoot: dir,
							commonGitDir,
							worktreeName: basename(dir),
						};
					}
				}

				if (stat.isDirectory()) {
					return {
						kind: "repo",
						repoRoot: dir,
						commonGitDir: gitPath,
						worktreeName: null,
					};
				}
			} catch {
				return { kind: "none", repoRoot: null, commonGitDir: null, worktreeName: null };
			}
		}

		const parent = dirname(dir);
		if (parent === dir) {
			return { kind: "none", repoRoot: null, commonGitDir: null, worktreeName: null };
		}
		dir = parent;
	}
}

function sanitizeStatusText(text: string): string {
	return text.replace(/[\r\n\t]/g, " ").replace(/ +/g, " ").trim();
}

function fit(line: string, width: number): string {
	return truncateToWidth(line, width, style("…", PALETTE.gray));
}

export default function (pi: ExtensionAPI) {
	pi.on("session_start", (_event, ctx) => {
		ctx.ui.setFooter((tui, theme, footerData) => {
			const unsubscribe = footerData.onBranchChange(() => tui.requestRender());

			return {
				dispose: unsubscribe,
				invalidate() {},
				render(width: number): string[] {
					let input = 0;
					let output = 0;
					let cacheRead = 0;
					let cacheWrite = 0;
					let cost = 0;

					for (const entry of ctx.sessionManager.getEntries()) {
						if (entry.type === "message" && entry.message.role === "assistant") {
							const message = entry.message as AssistantMessage;
							input += message.usage.input;
							output += message.usage.output;
							cacheRead += message.usage.cacheRead;
							cacheWrite += message.usage.cacheWrite;
							cost += message.usage.cost.total;
						}
					}

					const cwd = ctx.sessionManager.getCwd();
					const git = findGitInfo(cwd);
					const branch = footerData.getGitBranch();
					const focus = getFocusInfo();
					const projectId = process.env.PROJECT_ID || basename(cwd);
					const mode = process.env.JACAZUL_MODE || "COUNSELOR";

					const contextUsage = ctx.getContextUsage();
					const model = ctx.model;
					const contextWindow = contextUsage?.contextWindow ?? model?.contextWindow ?? 0;
					const contextPercent = contextUsage?.percent;
					const contextLabel = contextPercent === null || contextPercent === undefined
						? `ctx ?/${formatTokens(contextWindow)}`
						: `ctx ${contextPercent.toFixed(1)}%/${formatTokens(contextWindow)}`;
					const thinking = model?.reasoning ? pi.getThinkingLevel() : null;
					const modelParts = [model?.id ?? "no-model", thinking, contextLabel].filter(Boolean);

					const usageParts = [];
					if (input) usageParts.push(`↑${formatTokens(input)}`);
					if (output) usageParts.push(`↓${formatTokens(output)}`);
					if (cacheRead) usageParts.push(`R${formatTokens(cacheRead)}`);
					if (cacheWrite) usageParts.push(`W${formatTokens(cacheWrite)}`);
					if (cost) usageParts.push(`$${cost.toFixed(3)}`);

					const workflowLine = [
						accent("🐊"),
						accent(mode),
						value(projectId),
					].join(sep());

					const focusLabel = focus.independent ? "🎯 focus (independent)" : "🎯 focus";
					const focusLine = focus.plan || focus.taskUuid
						? [
							accent(focusLabel),
							focus.plan ? value(focus.plan) : null,
							focus.taskUuid ? value(formatFocusedTask(projectId, focus.taskUuid, () => tui.requestRender())) : null,
						].filter(Boolean).join(sep())
						: [label(focusLabel), value("none")].join(sep());

					let gitLine: string;
					if (git.kind === "worktree") {
						const repoIdentity = git.commonGitDir ? shortenHome(git.commonGitDir) : "unknown-common-git";
						const worktree = git.worktreeName ?? basename(cwd);
						const worktreeLabel = branch ? `${worktree}(${branch})` : worktree;
						gitLine = [
							accent("🌿 worktree"),
							value(repoIdentity),
							value(worktreeLabel),
						].join(sep());
					} else if (git.kind === "repo") {
						gitLine = [
							accent("🌿 repo"),
							value(shortenHome(git.repoRoot ?? cwd)),
							branch ? value(`branch ${branch}`) : null,
						].filter(Boolean).join(sep());
					} else {
						gitLine = [accent("📁 path"), value(shortenHome(cwd))].join(sep());
					}

					const runtimeLine = [
						accent("🤖"),
						value(modelParts.join(" · ")),
						usageParts.length ? value(usageParts.join(" ")) : null,
					].filter(Boolean).join(sep());

					const lines = [workflowLine, focusLine, gitLine, runtimeLine].map((line) => fit(line, width));
					const extensionStatuses = footerData.getExtensionStatuses();
					if (extensionStatuses.size > 0) {
						const statusText = Array.from(extensionStatuses.entries())
							.sort(([a], [b]) => a.localeCompare(b))
							.map(([, text]) => sanitizeStatusText(text))
							.join(" ");
						lines.push(truncateToWidth(theme.fg("dim", statusText), width, theme.fg("dim", "…")));
					}

					return lines;
				},
			};
		});
	});
}
