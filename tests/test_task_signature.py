import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import orjson

from .base import JacazulTest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PERSONA_BOOTSTRAP = PROJECT_ROOT / "scripts/bootstrap/persona"


class PersonaTaskSignatureTest(unittest.TestCase):
    """Verify prompt and persistent task signatures stay separate."""

    def test_bootstrap_separates_signatures_and_uses_runtime_context(self):
        with tempfile.TemporaryDirectory(prefix="task-signature-") as home:
            env = os.environ.copy()
            env.update(
                {
                    "JACAZUL_HOME": home,
                    "PROJECT_ID": "task-signature-test",
                    "JACAZUL_MODEL": "unspecified",
                    "PI_MODEL": "gpt-5.6-luna",
                    "JACAZUL_HARNESS": "pi",
                    "JACAZUL_SESSION_ID": "123456789",
                }
            )
            result = subprocess.run(
                [
                    "bash",
                    "-c",
                    'source "$1"; printf "%s\\n%s\\n%s\\n" '
                    '"$JACAZUL_PERSONA_SIGNATURE" '
                    '"$JACAZUL_RESPONSE_SIGNATURE" '
                    '"$JACAZUL_TASK_SIGNATURE"',
                    "bash",
                    str(PERSONA_BOOTSTRAP),
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
                "🐊 Jacazul",
                "— Jacazul (gpt-5.6-luna; harness: pi; session: 12345678)",
            ],
        )


class TaskAnnotationSignatureTest(JacazulTest):
    """Verify tw-flow signs persistent agent communication."""

    def setUp(self):
        super().setUp()
        self.env.update(
            {
                "JACAZUL_TASK_SIGNATURE": (
                    "— Arnalbam (gpt-5.6-luna; harness: pi; "
                    "session: abcdef12)"
                )
            }
        )
        self.run_cmd(f"{self.tw_flow} ini signature_test 'Task|research'")
        out, _, _ = self.run_cmd(
            f"{self.taskp} project:signature_test export"
        )
        self.task_uuid = orjson.loads(out)[0]["uuid"]

    def test_note_outcome_and_handoff_append_task_signature(self):
        signature = self.env["JACAZUL_TASK_SIGNATURE"]
        self.run_cmd(
            f"{self.tw_flow} note {self.task_uuid} decision 'Decision'"
        )
        self.run_cmd(f"{self.tw_flow} outcome {self.task_uuid} 'Outcome'")
        self.run_cmd(
            f"{self.tw_flow} handoff {self.task_uuid} 'Next action'"
        )

        out, _, _ = self.run_cmd(f"{self.taskp} {self.task_uuid} export")
        annotations = orjson.loads(out)[0]["annotations"]
        self.assertGreaterEqual(len(annotations), 3)
        for annotation in annotations[-3:]:
            self.assertTrue(annotation["description"].endswith(signature))

    def test_discard_audit_appends_task_signature(self):
        signature = self.env["JACAZUL_TASK_SIGNATURE"]
        self.run_cmd(f"{self.tw_flow} discard {self.task_uuid}")

        out, _, _ = self.run_cmd(f"{self.taskp} {self.task_uuid} export")
        annotation = orjson.loads(out)[0]["annotations"][-1]
        self.assertTrue(annotation["description"].endswith(signature))


if __name__ == "__main__":
    unittest.main()
