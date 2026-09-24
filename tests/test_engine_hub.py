import os
import re
import unittest
from pathlib import Path

from jacazul.hatch.engine import ENGINE_PERSONAS, hatch_prompt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = PROJECT_ROOT / "jacazul" / "hatch" / "templates"
ENGINE_DIR = PROJECT_ROOT / "skills" / "jacazul-engine"
LAUNCHERS = (
    "scripts/jacazul-claude",
    "scripts/jacazul-pi",
    "scripts/jacazul-gemini",
    "scripts/jacazul-gemini-sandboxed",
)
# Signatures and voice slang belong to a persona's own spec or the roster.
PERSONA_VOICE = re.compile(
    r"🐊 Jacazul|\{🔷\}|\{💪\}|\{🦉\}|tá ligado|\bquiridu\b|\bbarão\b"
)
VOICE_OWNERS = {"roster.md"}


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
            if reference.startswith("references/personas/"):
                continue
            self.assertIn(f"`{reference}`", self.hub, reference)
        self.assertIn("`references/personas/<id>.md`", self.hub)

    def test_every_persona_has_a_voice_reference(self):
        for persona in ENGINE_PERSONAS:
            self.assertIn(f"references/personas/{persona}.md", self.references)

    def test_hub_carries_no_voice_specification(self):
        self.assertNotIn("Persona Specifications", self.hub)
        for persona in ENGINE_PERSONAS:
            spec = TEMPLATES / "persona" / f"persona_{persona}.md"
            voice = spec.read_text(encoding="utf-8")
            self.assertNotIn(voice.strip().splitlines()[0], self.hub)

    def test_hub_is_thinner_than_its_references(self):
        total = sum(
            (ENGINE_DIR / reference).stat().st_size
            for reference in self.references
        )
        self.assertLess(len(self.hub.encode("utf-8")), 36_000)
        self.assertLess(len(self.hub.encode("utf-8")), total * 1.5)

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

    def test_shared_templates_carry_no_persona_voice(self):
        for path in TEMPLATES.rglob("*.md"):
            if path.name.startswith("persona_") or path.name in VOICE_OWNERS:
                continue
            text = path.read_text(encoding="utf-8")
            self.assertEqual(
                PERSONA_VOICE.findall(text), [], path.relative_to(TEMPLATES)
            )

    def test_launchers_inject_only_the_active_persona(self):
        bootstrap = (PROJECT_ROOT / "scripts/bootstrap/persona").read_text(
            encoding="utf-8"
        )
        self.assertIn("JACAZUL_PERSONA_SPEC_FILE", bootstrap)
        for launcher in LAUNCHERS:
            source = (PROJECT_ROOT / launcher).read_text(encoding="utf-8")
            self.assertIn("JACAZUL_PERSONA_SPEC_FILE", source, launcher)


if __name__ == "__main__":
    unittest.main()
