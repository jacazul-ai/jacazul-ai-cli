import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Every surface that lists first-turn skills for a session or agent prompt.
SURFACES = (
    "scripts/jacazul-claude",
    "scripts/jacazul-pi",
    "scripts/jacazul-copilot",
    "scripts/jacazul-gemini-sandboxed",
    "prompts/onboard.md",
    "jacazul/hatch/templates/core/responsibilities.md",
    "jacazul/hatch/templates/agent_master.md",
)
ON_DEMAND = "git-expert before the first repository operation"
# An eager mention names an on-demand expert in the same sentence as an
# immediate or first-action load.
EAGER = re.compile(
    r"(immediately|FIRST action)[^.\n]*\b(git|security)-expert"
    r"|\b(git|security)-expert\b[^.\n]*immediately"
)


class KeystoneLoadTest(unittest.TestCase):
    """git-expert and security-expert load on demand, not in turn one."""

    def test_surfaces_load_experts_on_demand(self):
        for surface in SURFACES:
            text = (PROJECT_ROOT / surface).read_text(encoding="utf-8")
            self.assertIn(ON_DEMAND, text, surface)
            self.assertIsNone(EAGER.search(text), surface)

    def test_pi_first_action_list_is_engine_and_workflow_only(self):
        text = (PROJECT_ROOT / "scripts/jacazul-pi").read_text(
            encoding="utf-8"
        )
        block = text.split("## 🛑 MANDATORY: SKILL ACTIVATION", 1)[1]
        first_list = block.split("\n\n", 1)[0]

        self.assertIn("- jacazul-engine", first_list)
        self.assertIn("- taskwarrior-expert", first_list)
        self.assertNotIn("- git-expert", first_list)
        self.assertNotIn("- security-expert", first_list)

    def test_agents_keystone_names_the_on_demand_experts(self):
        raw = (PROJECT_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        text = " ".join(raw.split())

        self.assertIn("load on demand", text)
        self.assertNotIn("four core required skills", text)


if __name__ == "__main__":
    unittest.main()
