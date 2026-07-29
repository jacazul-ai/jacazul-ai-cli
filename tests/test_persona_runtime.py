import json
import os
import pathlib
import shutil
import stat
import subprocess
import tempfile
import unittest


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
COPILOT_LAUNCHER = PROJECT_ROOT / "scripts" / "jacazul-copilot"
CLAUDE_LAUNCHER = PROJECT_ROOT / "scripts" / "jacazul-claude"
PI_LAUNCHER = PROJECT_ROOT / "scripts" / "jacazul-pi"
OPENCODE_LAUNCHER = PROJECT_ROOT / "scripts" / "jacazul-opencode"


class TestPersonaRuntime(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="jacazul_persona_runtime_")
        self.home = pathlib.Path(self.test_dir) / "home"
        self.bin_dir = pathlib.Path(self.test_dir) / "bin"
        self.project_id = "jacazul-ai_jacazul-ai-cli"
        self.task_dir = self.home / ".jacazul-ai" / ".task" / self.project_id
        self.home.mkdir(parents=True)
        self.bin_dir.mkdir(parents=True)
        self.task_dir.mkdir(parents=True)

        for binary in ("copilot", "claude"):
            fake_binary = self.bin_dir / binary
            fake_binary.write_text(
                "#!/usr/bin/env bash\n"
                'if [ -n "$CAPTURE_FILE" ]; then\n'
                '  printf \'%s\\n\' "$@" > "$CAPTURE_FILE"\n'
                "fi\n"
                "exit 0\n",
                encoding="utf-8",
            )
            fake_binary.chmod(stat.S_IRWXU)

        fake_pi = self.bin_dir / "pi"
        fake_pi.write_text(
            "#!/usr/bin/env bash\n"
            'if [[ "$1" == "update" ]]; then\n'
            "  echo 'pi already up to date'\n"
            "  exit 0\n"
            "fi\n"
            'if [ -n "$CAPTURE_FILE" ]; then\n'
            '  printf \'%s\\n\' "$@" > "$CAPTURE_FILE"\n'
            "fi\n"
            "exit 0\n",
            encoding="utf-8",
        )
        fake_pi.chmod(stat.S_IRWXU)

        fake_opencode = self.bin_dir / "opencode"
        fake_opencode.write_text(
            "#!/usr/bin/env bash\n"
            'if [[ "$1" == "upgrade" ]]; then\n'
            "  exit 0\n"
            "fi\n"
            'if [ -n "$CAPTURE_FILE" ]; then\n'
            '  printf \'%s\\n\' "$@" > "$CAPTURE_FILE"\n'
            "fi\n"
            "exit 0\n",
            encoding="utf-8",
        )
        fake_opencode.chmod(stat.S_IRWXU)

        self.generated_agent = PROJECT_ROOT / "agents" / "arnalbam-opencode.md"
        self.created_agent = not self.generated_agent.exists()
        if self.created_agent:
            self.generated_agent.write_text(
                "# Test generated Arnalbam agent\n",
                encoding="utf-8",
            )

        (self.task_dir / "persona.json").write_text(
            json.dumps({"anchored_persona": "arnalbam"}),
            encoding="utf-8",
        )

    def tearDown(self):
        if self.created_agent:
            self.generated_agent.unlink(missing_ok=True)
        shutil.rmtree(self.test_dir)

    def _run_launcher(self, launcher, dry=True):
        env = os.environ.copy()
        capture_file = self.home / "captured-args"
        env.update(
            {
                "HOME": str(self.home),
                "JACAZUL_HOME": str(self.home / ".jacazul-ai"),
                "PROJECT_ID": self.project_id,
                "JACAZUL_ENV_INITIALIZED": "true",
                "PATH": f"{self.bin_dir}:{env.get('PATH', '')}",
                "CAPTURE_FILE": str(capture_file),
            }
        )
        if dry:
            env["DRY"] = "true"
        else:
            env.pop("DRY", None)

        result = subprocess.run(
            [str(launcher)],
            cwd=PROJECT_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        captured = (
            capture_file.read_text(encoding="utf-8")
            if capture_file.exists()
            else ""
        )
        return result, captured

    def test_copilot_uses_project_anchored_persona(self):
        result, _ = self._run_launcher(COPILOT_LAUNCHER)

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("--agent arnalbam", result.stdout)
        self.assertNotIn("--agent jacazul", result.stdout)

    def test_claude_injects_project_anchored_persona(self):
        result, captured = self._run_launcher(CLAUDE_LAUNCHER, dry=False)

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Arnalbam ({💪} Arnalbam)", captured)
        self.assertNotIn("Jacazul (Jacaré Azul)", captured)

    def test_pi_injects_project_anchored_persona(self):
        result, captured = self._run_launcher(PI_LAUNCHER, dry=False)

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Arnalbam ({💪} Arnalbam)", captured)
        self.assertNotIn("Jacazul (Jacaré Azul)", captured)

    def test_opencode_uses_project_anchored_agent(self):
        result, captured = self._run_launcher(OPENCODE_LAUNCHER, dry=False)

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(captured.splitlines()[:2], ["--agent", "arnalbam"])


if __name__ == "__main__":
    unittest.main()
