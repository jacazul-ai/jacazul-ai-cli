import json
import os
import pathlib
import re
import shutil
import subprocess
import tempfile
import unittest


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
STATUSLINE = PROJECT_ROOT / "extensions" / "claude" / "jacazul-line.sh"
ANSI = re.compile(r"\x1b\[[0-9;]*m")


class TestClaudeJacazulLine(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="jacazul_line_")
        self.home = os.path.join(self.test_dir, "home")
        os.makedirs(self.home, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _run(self, payload):
        env = os.environ.copy()
        env.pop("CLAUDE_MODEL", None)
        env.pop("PROJECT_ID", None)
        env.pop("JACAZUL_SESSION_ID", None)
        env["HOME"] = self.home
        result = subprocess.run(
            [str(STATUSLINE)],
            input=json.dumps(payload),
            env=env,
            cwd=self.test_dir,
            capture_output=True,
            text=True,
        )
        return result, ANSI.sub("", result.stdout)

    def _write_transcript(self, name, model):
        path = os.path.join(self.test_dir, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"message": {"model": model}}) + "\n")
        return path

    def test_model_comes_from_the_payload(self):
        result, out = self._run({"model": {"display_name": "Opus"}})

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Opus", out)

    def test_model_falls_back_to_the_declared_transcript(self):
        transcript = self._write_transcript("real.jsonl", "claude-opus-5")

        result, out = self._run({"transcript_path": transcript})

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("claude-opus-5", out)

    def test_legacy_config_dir_is_never_guessed(self):
        """Regression: the fallback used to build ~/.claude/projects/...

        With the config dir anchored under JACAZUL_HOME, guessing that path
        reads the wrong tree. Plant a decoy there and assert it is ignored
        in favour of the payload's transcript_path.
        """
        slug = self.test_dir.replace("/", "-")
        legacy_dir = os.path.join(self.home, ".claude", "projects", slug)
        os.makedirs(legacy_dir, exist_ok=True)
        decoy = os.path.join(legacy_dir, "sess.jsonl")
        with open(decoy, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"message": {"model": "DECOY-MODEL"}}) + "\n")
        transcript = self._write_transcript("real.jsonl", "REAL-MODEL")

        env_extra = {"CLAUDE_CODE_SESSION_ID": "sess"}
        env = os.environ.copy()
        env.pop("CLAUDE_MODEL", None)
        env.pop("PROJECT_ID", None)
        env["HOME"] = self.home
        env.update(env_extra)
        result = subprocess.run(
            [str(STATUSLINE)],
            input=json.dumps({"transcript_path": transcript}),
            env=env,
            cwd=self.test_dir,
            capture_output=True,
            text=True,
        )
        out = ANSI.sub("", result.stdout)

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("REAL-MODEL", out)
        self.assertNotIn("DECOY-MODEL", out)

    def test_empty_payload_still_renders(self):
        result, out = self._run({})

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("COUNSELOR", out)
        self.assertGreaterEqual(len(out.strip().splitlines()), 3)

    def test_script_holds_no_hardcoded_legacy_config_path(self):
        body = STATUSLINE.read_text(encoding="utf-8")
        code = [
            line
            for line in body.splitlines()
            if not line.lstrip().startswith("#")
        ]
        self.assertNotIn(".claude/", "\n".join(code))


if __name__ == "__main__":
    unittest.main()
