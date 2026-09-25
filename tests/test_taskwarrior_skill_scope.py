import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL = PROJECT_ROOT / "skills" / "taskwarrior-expert" / "SKILL.md"
# Every command and rule the skill taught before it was slimmed.
OWNED = (
    "tw-flow done <uuid>",
    "tw-flow execute <uuid>",
    "tw-flow focus back",
    "tw-flow focus clear",
    "tw-flow focus ind <plan-name>",
    "tw-flow focus ind plan <name>",
    "tw-flow focus ind task <uuid>",
    "tw-flow note <uuid>",
    "tw-flow outcome <uuid>",
    "tw-flow plan feature-x",
    "tw-flow ponder --force",
    "tw-flow session dump --force",
    "tw-flow session resume",
    "tw-flow status --force",
    "taskp",
    "TASKDATA",
    "PROJECT_ID",
    "JACAZUL_SESSION_ID",
    "JACAZUL_FOCUS_PLAN",
    "priority:M",
    "`due` date",
    "OUTCOME",
    "short UUIDs (8 chars)",
)
# Owned by the jacazul-engine hub or its references.
ENGINE_OWNED = (
    "| **`[GUIDE]`**",
    "## 🌐 Language Protocol",
    "**File behavior for dump (Error as Prompt):**",
)


class TaskwarriorSkillScopeTest(unittest.TestCase):
    """The slimmed skill keeps every command and drops engine copies."""

    def setUp(self):
        self.text = SKILL.read_text(encoding="utf-8")

    def test_keeps_every_owned_command_and_rule(self):
        for item in OWNED:
            self.assertIn(item, self.text, item)

    def test_points_at_the_engine_instead_of_copying_it(self):
        for item in ENGINE_OWNED:
            self.assertNotIn(item, self.text, item)
        self.assertIn("jacazul-engine", self.text)

    def test_stays_lean(self):
        self.assertLess(len(self.text.encode("utf-8")), 6_000)


if __name__ == "__main__":
    unittest.main()
