import os
from pathlib import Path
import subprocess
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class PersonaSignatureAuthorityTest(unittest.TestCase):
    """Verify prompt and persistent task signature contracts."""

    def test_engine_declares_separate_signatures(self):
        source = self._read("jacazul/hatch/templates/core/logic.md")
        self._assert_contract(source)
        self.assertIn("task annotation signature", source.lower())

    def test_claude_prompt_declares_separate_signatures(self):
        self._assert_contract(self._read("scripts/jacazul-claude"))

    def test_pi_prompt_declares_separate_signatures(self):
        self._assert_contract(self._read("scripts/jacazul-pi"))

    def test_user_docs_define_separate_signatures(self):
        source = self._read("docs/interaction-modes.md")
        self.assertIn("active persona's visual signature", source)
        self.assertIn("— <Active Persona> (<Current Model>; harness:", source)

    def test_launchers_publish_harness_identity(self):
        for launcher, harness in {
            "scripts/jacazul-pi": "pi",
            "scripts/jacazul-claude": "claude",
            "scripts/jacazul-gemini": "gemini",
            "scripts/jacazul-copilot": "copilot",
            "scripts/jacazul-opencode": "opencode",
        }.items():
            source = self._read(launcher)
            self.assertIn(
                f'JACAZUL_HARNESS="${{JACAZUL_HARNESS:-{harness}}}"',
                source,
            )

    def test_persona_bootstrap_composes_task_signature(self):
        with tempfile.TemporaryDirectory(prefix="persona-signature-") as home:
            env = os.environ.copy()
            env.update(
                {
                    "JACAZUL_HOME": home,
                    "PROJECT_ID": "persona-signature-test",
                    "JACAZUL_MODEL": "unspecified",
                    "PI_MODEL": "claude-opus-5",
                    "JACAZUL_HARNESS": "claude",
                    "JACAZUL_SESSION_ID": "123456789",
                }
            )
            result = subprocess.run(
                [
                    "bash",
                    "-c",
                    'source "$1"; printf "%s\\n" '
                    '"$JACAZUL_RESPONSE_SIGNATURE" '
                    '"$JACAZUL_TASK_SIGNATURE"',
                    "bash",
                    str(PROJECT_ROOT / "scripts/bootstrap/persona"),
                ],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )

        self.assertEqual(
            result.stdout.splitlines(),
            [
                "🐊 Jacazul",
                "— Jacazul (claude-opus-5; harness: claude; "
                "session: 12345678)",
            ],
        )

    @staticmethod
    def _read(relative_path: str) -> str:
        return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")

    def _assert_contract(self, source: str):
        normalized = source.lower()
        self.assertIn("jacazul_persona_signature", normalized)
        self.assertIn("jacazul_response_signature", normalized)
        self.assertIn("jacazul_task_signature", normalized)
        self.assertIn("active persona", normalized)
        self.assertIn("task annotation", normalized)


if __name__ == "__main__":
    unittest.main()
