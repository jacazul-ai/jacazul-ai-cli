import os
import unittest
from pathlib import Path

from jacazul.hatch.engine import hatch_prompt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = PROJECT_ROOT / "skills" / "jacazul-engine"


class EngineHubTest(unittest.TestCase):
    """The engine renders a thin hub plus one level of references."""

    @classmethod
    def setUpClass(cls):
        previous = os.environ.get("PROJECT_ID")
        os.environ["PROJECT_ID"] = "engine-hub-test"
        stale = ENGINE_DIR / "references" / "stale-topic.md"
        stale.parent.mkdir(parents=True, exist_ok=True)
        stale.write_text("stale\n", encoding="utf-8")
        try:
            hatch_prompt("gemini", persona_override="arnalbam")
        finally:
            if previous is None:
                os.environ.pop("PROJECT_ID", None)
            else:
                os.environ["PROJECT_ID"] = previous
        cls.hub = (ENGINE_DIR / "SKILL.md").read_text(encoding="utf-8")
        cls.references = sorted(
            path.relative_to(ENGINE_DIR).as_posix()
            for path in (ENGINE_DIR / "references").rglob("*.md")
        )

    def test_hub_routes_every_reference(self):
        self.assertTrue(self.references)
        for reference in self.references:
            self.assertIn(f"`{reference}`", self.hub, reference)

    def test_references_stay_one_level_deep(self):
        for reference in self.references:
            text = (ENGINE_DIR / reference).read_text(encoding="utf-8")
            self.assertNotRegex(text, r"`references/[^`]+\.md`", reference)

    def test_orphan_references_are_removed(self):
        self.assertNotIn("references/stale-topic.md", self.references)
        self.assertTrue((ENGINE_DIR / "evals").is_dir())

    def test_triggered_protocols_left_the_hub(self):
        self.assertNotIn("## HANDOFF VISIBILITY CONTRACT", self.hub)
        self.assertNotIn("### GUIDE Precision Protocol", self.hub)
        self.assertNotIn("# Jacazul Trigger Glossary", self.hub)
        self.assertNotIn("## 🚀 CLI Quick Reference", self.hub)


if __name__ == "__main__":
    unittest.main()
