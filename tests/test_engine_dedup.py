import os
import re
import unittest
from pathlib import Path

from jacazul.hatch.engine import hatch_prompt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = PROJECT_ROOT / "jacazul" / "hatch" / "templates"
PERSONA_VOICE = re.compile(
    r"🐊|\{🔷\}|\{💪\}|\{🦉\}|\bJacazul\b|\bCodana\b|\bCodama\b"
    r"|\bArnalbam\b|\bAtena\b|tá ligado|\bpai\b|\bbarão\b|\bquiridu\b"
)


class EngineDedupTest(unittest.TestCase):
    """Each engine section renders once and shared text carries no voice."""

    def test_engine_renders_one_response_format(self):
        rendered = self._hatch_engine()

        self.assertEqual(
            rendered.count("## Response Format (Terminal-First"), 1
        )
        self.assertIn("**RULE 8:**", rendered)
        self.assertIn("### 3b. Ponder Table", rendered)

    def test_language_protocol_is_persona_neutral(self):
        text = (TEMPLATES / "protocols" / "language_protocol.md").read_text(
            encoding="utf-8"
        )

        self.assertEqual(PERSONA_VOICE.findall(text), [])

    @staticmethod
    def _hatch_engine() -> str:
        previous = os.environ.get("PROJECT_ID")
        os.environ["PROJECT_ID"] = "engine-dedup-test"
        try:
            hatch_prompt("gemini", persona_override="jacazul")
        finally:
            if previous is None:
                os.environ.pop("PROJECT_ID", None)
            else:
                os.environ["PROJECT_ID"] = previous
        skill = PROJECT_ROOT / "skills" / "jacazul-engine" / "SKILL.md"
        return skill.read_text(encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
