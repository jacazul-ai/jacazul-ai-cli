import os
import pathlib
import shutil
import stat
import subprocess
import tempfile
import unittest


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
BOOTSTRAP_PI = PROJECT_ROOT / "scripts" / "bootstrap" / "pi"
JACAZUL_PI = PROJECT_ROOT / "scripts" / "jacazul-pi"


class TestPiAgentDirectory(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="jacazul_pi_agent_dir_")
        self.home = os.path.join(self.test_dir, "home")
        self.jacazul_home = os.path.join(self.home, ".jacazul-ai")
        self.bin_dir = os.path.join(self.test_dir, "bin")
        os.makedirs(self.home, exist_ok=True)
        os.makedirs(self.jacazul_home, exist_ok=True)
        os.makedirs(self.bin_dir, exist_ok=True)
        self._write_fake_pi()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _write_fake_pi(self):
        fake_pi = os.path.join(self.bin_dir, "pi")
        with open(fake_pi, "w", encoding="utf-8") as fh:
            fh.write("#!/usr/bin/env bash\n")
            fh.write('if [[ "$1" == "update" ]]; then\n')
            fh.write("  echo 'pi already up to date'\n")
            fh.write("  exit 0\n")
            fh.write("fi\n")
            fh.write("printf '%s\n' \"$@\"\n")
        os.chmod(fake_pi, stat.S_IRWXU)

    def _run_bash(self, command, extra_env=None, cwd=None):
        env = os.environ.copy()
        env.pop("PI_CODING_AGENT_DIR", None)
        env.update(
            {
                "HOME": self.home,
                "JACAZUL_HOME": self.jacazul_home,
                "PATH": f"{self.bin_dir}:{env.get('PATH', '')}",
                "PROJECT_ID": "jacazul-ai_jacazul-ai-cli",
                "TASKDATA": os.path.join(
                    self.jacazul_home,
                    ".task",
                    "jacazul-ai_jacazul-ai-cli",
                ),
            }
        )
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            command,
            cwd=cwd or str(PROJECT_ROOT),
            env=env,
            shell=True,
            executable="/bin/bash",
            capture_output=True,
            text=True,
        )

    def test_bootstrap_uses_explicit_pi_coding_agent_dir(self):
        custom_dir = os.path.join(self.test_dir, "custom-pi-agent")

        result = self._run_bash(
            f'source "{BOOTSTRAP_PI}"',
            extra_env={"PI_CODING_AGENT_DIR": custom_dir},
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(os.path.isdir(os.path.join(custom_dir, "skills")))
        self.assertTrue(os.path.isdir(os.path.join(custom_dir, "extensions")))
        self.assertFalse(
            os.path.exists(os.path.join(self.home, ".pi", "agent", "skills"))
        )

    def test_launcher_defaults_pi_state_under_jacazul_home(self):
        default_dir = os.path.join(self.jacazul_home, "agents", "pi")

        result = self._run_bash(
            f'DRY=true "{JACAZUL_PI}"',
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(os.path.isdir(os.path.join(default_dir, "skills")))
        self.assertTrue(os.path.isdir(os.path.join(default_dir, "extensions")))
        self.assertFalse(
            os.path.exists(os.path.join(self.home, ".pi", "agent"))
        )

    def test_launcher_migrates_existing_home_pi_agent_dir_once(self):
        legacy_dir = os.path.join(self.home, ".pi", "agent")
        os.makedirs(os.path.join(legacy_dir, "extensions"), exist_ok=True)
        os.makedirs(os.path.join(legacy_dir, "skills"), exist_ok=True)
        settings_file = os.path.join(legacy_dir, "settings.json")
        legacy_extension = os.path.join(legacy_dir, "extensions", "custom.ts")
        with open(settings_file, "w", encoding="utf-8") as fh:
            fh.write('{"theme":"legacy"}\n')
        with open(legacy_extension, "w", encoding="utf-8") as fh:
            fh.write("export default {}\n")

        result = self._run_bash(f'DRY=true "{JACAZUL_PI}"')

        target_dir = os.path.join(self.jacazul_home, "agents", "pi")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertFalse(os.path.exists(settings_file))
        self.assertTrue(
            os.path.isfile(os.path.join(target_dir, "settings.json"))
        )
        self.assertTrue(
            os.path.isfile(os.path.join(target_dir, "extensions", "custom.ts"))
        )

    def test_launcher_passthrough_commands_skip_onboard_prompt(self):
        result = self._run_bash(
            f'DRY=true "{JACAZUL_PI}" install npm:pi-web-access',
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn(
            "🐊 Arguments for pi: install npm:pi-web-access",
            result.stdout,
        )
        self.assertNotIn("--append-system-prompt", result.stdout)

    def test_launcher_prints_resume_banner_for_independent_session(self):
        session_id = "019f16d1-97b1-7c15-bced-dde88107026d"
        focus_dir = os.path.join(
            self.jacazul_home,
            ".task",
            "jacazul-ai_jacazul-ai-cli",
        )
        os.makedirs(focus_dir, exist_ok=True)
        focus_file = os.path.join(focus_dir, f"focus-{session_id}.json")
        with open(focus_file, "w", encoding="utf-8") as fh:
            fh.write("{}\n")

        result = self._run_bash(
            f'"{JACAZUL_PI}" --jacazul-session {session_id} --help',
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn(
            f"🐊 Resume: jacazul-pi --jacazul-session {session_id}",
            result.stdout,
        )


if __name__ == "__main__":
    unittest.main()
