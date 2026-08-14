import os
import shutil
import subprocess
import sys
import tempfile
import unittest


class TestSessionResume(unittest.TestCase):
    """Validate visible session-note acknowledgement behavior."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="jacazul-test-resume-")
        self.taskdata = os.path.join(self.test_dir, "taskdata")
        os.makedirs(self.taskdata)
        self.env = os.environ.copy()
        self.env.update(
            {
                "TASKDATA": self.taskdata,
                "PROJECT_ID": "test-session-resume",
                "JACAZUL_SESSION_ID": "323b7cd3",
                "PYTHONPATH": os.path.abspath("."),
            }
        )
        self.flow = os.path.abspath("jacazul/cli/flow.py")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _run(self, *args):
        return subprocess.run(
            [sys.executable, self.flow, *args],
            capture_output=True,
            text=True,
            env=self.env,
        )

    def _write_note(self, content):
        path = os.path.join(
            self.taskdata,
            f"session-note-{self.env['JACAZUL_SESSION_ID']}.md",
        )
        with open(path, "w") as note:
            note.write(content)

    def test_acknowledged_note_is_reported(self):
        """resume must explain that an existing note was acknowledged."""
        self._write_note("# Session Handoff Note\n\ninjected: 2026-04-02T00:00:00+00:00\n")

        result = self._run("session", "resume")

        self.assertEqual(result.returncode, 0)
        self.assertIn("already acknowledged", result.stdout.lower())
        self.assertIn("session-note-323b7cd3.md", result.stdout)

    def test_dump_explains_acknowledged_note(self):
        """dump must explain why an acknowledged note cannot be replaced."""
        self._write_note("# Session Handoff Note\n\ninjected: 2026-04-02T00:00:00+00:00\n")

        result = self._run("session", "dump")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("already acknowledged", result.stderr.lower())
        self.assertIn("injected:", result.stderr)

    def test_absent_note_remains_silent(self):
        """resume must remain silent when no note exists."""
        result = self._run("session", "resume")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
