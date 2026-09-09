import { StringEnum } from "@earendil-works/pi-ai";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";

const JACAZUL_NEOVIM_GUIDANCE = [
	"This agent is running inside jacazul.nvim. Neovim is the active host UI.",
	"Send normal answers to the Neovim transcript and short alerts through jacazul_alert.",
	"Do not treat the Neovim prompt as a terminal or inject keystrokes into it.",
].join("\n");

const JACAZUL_UI_GUIDANCE = [
	"Jacazul UI dispatch: write normal answers as assistant text so they appear in the transcript.",
	"Use jacazul_alert for short user-visible status changes, blockers, or completed worker milestones.",
	"When the user asks for an alert now, call jacazul_alert immediately before writing prose.",
	"Do not encode UI actions in prose or XML/JSON markers; call the jacazul_alert tool instead.",
	"Never use tmux, Neovim remote expressions, or prompt-buffer mutation to deliver an alert.",
].join("\n");

const parameters = Type.Object({
	message: Type.String({ description: "Short message to show in the host UI" }),
	notifyType: Type.Optional(
		StringEnum(["info", "warning", "error"] as const, {
			description: "Visual severity of the notification",
		}),
	),
});

export default function (pi: ExtensionAPI) {
	pi.on("before_agent_start", async (event) => {
		const hostGuidance =
			process.env.JACAZUL_HOST === "jacazul.nvim"
				? `\n\n${JACAZUL_NEOVIM_GUIDANCE}`
				: "";
		return {
			systemPrompt: `${event.systemPrompt}\n\n${JACAZUL_UI_GUIDANCE}${hostGuidance}`,
		};
	});

	pi.registerTool({
		name: "jacazul_alert",
		label: "Jacazul alert",
		description:
			"Show a short, non-blocking notification in the connected Jacazul host UI.",
		promptSnippet: "Show a short status alert in the connected Jacazul UI",
		promptGuidelines: [
			"Use jacazul_alert only for short user-visible status changes, blockers, or completed worker milestones.",
			"When the user explicitly asks for an alert now, call this tool immediately before writing prose.",
			"Do not use jacazul_alert for normal explanations; write those in the assistant response.",
			"Never use tmux, Neovim remote expressions, or prompt-buffer mutation to deliver an alert.",
		],
		parameters,
		async execute(_toolCallId, input, signal, _onUpdate, ctx) {
			if (signal?.aborted) {
				return {
					content: [{ type: "text", text: "Alert cancelled." }],
					details: {},
				};
			}

			if (!ctx.hasUI) {
				return {
					content: [{ type: "text", text: "No host UI is connected." }],
					details: { displayed: false },
				};
			}

			ctx.ui.notify(input.message, input.notifyType ?? "info");
			return {
				content: [{ type: "text", text: "Alert sent to the connected Jacazul UI." }],
				details: { displayed: true },
			};
		},
	});
}
