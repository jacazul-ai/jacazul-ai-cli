import os
import unittest
from pathlib import Path

from jacazul.hatch.engine import hatch_prompt


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class MultiAgentLoopContractTest(unittest.TestCase):
    """Verify the additive multi-agent engine protocol."""

    def test_engine_includes_additive_multi_agent_protocol(self):
        logic = self._read("jacazul/hatch/templates/core/logic.md")
        protocol = self._read(
            "jacazul/hatch/templates/core/multi_agent_loop.md"
        )

        self.assertIn(
            '{% include "multi_agent_loop.md" %}',
            logic,
        )
        self.assertIn("existing solo workflow", protocol)
        self.assertIn("Taskwarrior", protocol)
        self.assertIn("remove or change existing solo behavior", protocol)
        self.assertIn("## Consensus Review Protocol", protocol)
        self.assertIn("single-persona review", protocol)
        self.assertIn("signed `DECISION`", protocol)

    def test_user_docs_describe_additive_continuity(self):
        docs = self._read("docs/tw-flow.md")

        self.assertIn("## Multi-Agent Continuity", docs)
        self.assertIn("solo workflow remains", docs.lower())
        self.assertIn("Taskwarrior remains the source of truth", docs)
        self.assertIn("When to use consensus review", docs)
        self.assertIn("single-persona review", docs)

    def test_hatch_renders_protocol_into_engine_skill(self):
        previous_project_id = os.environ.get("PROJECT_ID")
        os.environ["PROJECT_ID"] = "multi-agent-loop-test"
        try:
            hatch_prompt("gemini", persona_override="jacazul")
            rendered = self._read("skills/jacazul-engine/SKILL.md")
        finally:
            if previous_project_id is None:
                os.environ.pop("PROJECT_ID", None)
            else:
                os.environ["PROJECT_ID"] = previous_project_id

        self.assertIn("## Multi-Agent Continuity Extension", rendered)
        self.assertIn(
            "existing solo workflow remains unchanged", rendered.lower()
        )
        self.assertIn("## Consensus Review Protocol", rendered)

    def test_hatch_renders_protocol_into_agent_prompt(self):
        for client in ("copilot", "opencode"):
            hatch_prompt(client, persona_override="arnalbam")
            rendered = self._read(f"agents/arnalbam-{client}.md")

            self.assertIn("## Multi-Agent Continuity Extension", rendered)
            self.assertIn(
                "existing solo workflow remains unchanged",
                rendered.lower(),
            )
            self.assertIn("## Consensus Review Protocol", rendered)

    def test_direct_harness_prompts_load_protocol(self):
        for launcher in (
            "scripts/jacazul-pi",
            "scripts/jacazul-claude",
            "scripts/jacazul-gemini",
            "scripts/jacazul-gemini-sandboxed",
        ):
            source = self._read(launcher)
            self.assertIn("multi_agent_loop.md", source)

    @staticmethod
    def _read(relative_path: str) -> str:
        return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
