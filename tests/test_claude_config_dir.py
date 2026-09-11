import json
import os
import pathlib
import shutil
import stat
import subprocess
import tempfile
import unittest


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
BOOTSTRAP_CLAUDE = PROJECT_ROOT / "scripts" / "bootstrap" / "claude"


class TestClaudeConfigDir(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="jacazul_claude_cfg_")
        self.home = os.path.join(self.test_dir, "home")
        self.jacazul_home = os.path.join(self.home, ".jacazul-ai")
        self.bin_dir = os.path.join(self.test_dir, "bin")
        os.makedirs(self.home, exist_ok=True)
        os.makedirs(self.jacazul_home, exist_ok=True)
        os.makedirs(self.bin_dir, exist_ok=True)
        self._write_fake_pgrep(session_running=False)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _write_fake_pgrep(self, session_running):
        """Shadow pgrep so the live-session guard is deterministic.

        The real pgrep would see the developer's own Claude sessions and
        make the migration branch untestable on a working machine.
        """
        fake = os.path.join(self.bin_dir, "pgrep")
        exit_code = 0 if session_running else 1
        with open(fake, "w", encoding="utf-8") as fh:
            fh.write("#!/usr/bin/env bash\n")
            fh.write(f"exit {exit_code}\n")
        os.chmod(fake, stat.S_IRWXU)

    def _source_bootstrap(self, extra_env=None):
        env = os.environ.copy()
        env.pop("CLAUDE_CONFIG_DIR", None)
        env.update(
            {
                "HOME": self.home,
                "JACAZUL_HOME": self.jacazul_home,
                "PATH": f"{self.bin_dir}:{env.get('PATH', '')}",
            }
        )
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            f'source "{BOOTSTRAP_CLAUDE}"',
            cwd=str(PROJECT_ROOT),
            env=env,
            shell=True,
            executable="/bin/bash",
            capture_output=True,
            text=True,
        )

    def _make_legacy_tree(self):
        legacy = os.path.join(self.home, ".claude")
        os.makedirs(legacy, exist_ok=True)
        creds = os.path.join(legacy, ".credentials.json")
        with open(creds, "w", encoding="utf-8") as fh:
            fh.write('{"token":"legacy-secret"}\n')
        os.chmod(creds, stat.S_IRUSR | stat.S_IWUSR)
        with open(
            os.path.join(legacy, "history.jsonl"), "w", encoding="utf-8"
        ) as fh:
            fh.write('{"turn":1}\n')
        return legacy

    def test_bootstrap_honors_explicit_claude_config_dir(self):
        custom_dir = os.path.join(self.test_dir, "custom-claude")

        result = self._source_bootstrap(
            extra_env={"CLAUDE_CONFIG_DIR": custom_dir}
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(os.path.isdir(os.path.join(custom_dir, "skills")))
        self.assertTrue(os.path.isdir(os.path.join(custom_dir, "extensions")))
        self.assertFalse(os.path.exists(os.path.join(self.home, ".claude")))

    def test_bootstrap_defaults_under_jacazul_home(self):
        default_dir = os.path.join(self.jacazul_home, "agents", "claude")

        result = self._source_bootstrap()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(os.path.isdir(os.path.join(default_dir, "skills")))
        self.assertTrue(os.path.isdir(os.path.join(default_dir, "extensions")))
        self.assertFalse(os.path.exists(os.path.join(self.home, ".claude")))

    def test_bootstrap_migrates_legacy_tree_once(self):
        legacy = self._make_legacy_tree()
        target = os.path.join(self.jacazul_home, "agents", "claude")

        result = self._source_bootstrap()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertFalse(os.path.exists(legacy))
        moved_creds = os.path.join(target, ".credentials.json")
        self.assertTrue(os.path.isfile(moved_creds))
        self.assertTrue(os.path.isfile(os.path.join(target, "history.jsonl")))
        mode = stat.S_IMODE(os.stat(moved_creds).st_mode)
        self.assertEqual(mode, stat.S_IRUSR | stat.S_IWUSR)

    def test_migration_never_merges_into_existing_target(self):
        legacy = self._make_legacy_tree()
        target = os.path.join(self.jacazul_home, "agents", "claude")
        os.makedirs(target, exist_ok=True)

        result = self._source_bootstrap()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(os.path.isdir(legacy))
        self.assertFalse(
            os.path.exists(os.path.join(target, ".credentials.json"))
        )

    def test_migration_aborts_while_a_claude_session_runs(self):
        self._write_fake_pgrep(session_running=True)
        legacy = self._make_legacy_tree()
        target = os.path.join(self.jacazul_home, "agents", "claude")

        result = self._source_bootstrap()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(
            os.path.isfile(os.path.join(legacy, ".credentials.json"))
        )
        self.assertFalse(
            os.path.exists(os.path.join(target, ".credentials.json"))
        )
        self.assertIn("another Claude session is running", result.stderr)

    def test_statusline_is_rehomed_instead_of_frozen(self):
        target = os.path.join(self.jacazul_home, "agents", "claude")
        os.makedirs(target, exist_ok=True)
        settings = os.path.join(target, "settings.json")
        stale = "/home/someone/.claude/extensions/jacazul-line.sh"
        with open(settings, "w", encoding="utf-8") as fh:
            json.dump({"statusLine": stale}, fh)

        result = self._source_bootstrap()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        with open(settings, encoding="utf-8") as fh:
            value = json.load(fh)["statusLine"]
        self.assertEqual(
            value, os.path.join(target, "extensions", "jacazul-line.sh")
        )

    def test_user_owned_statusline_is_left_alone(self):
        target = os.path.join(self.jacazul_home, "agents", "claude")
        os.makedirs(target, exist_ok=True)
        settings = os.path.join(target, "settings.json")
        mine = "/home/someone/bin/my-own-line.sh"
        with open(settings, "w", encoding="utf-8") as fh:
            json.dump({"statusLine": mine}, fh)

        result = self._source_bootstrap()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        with open(settings, encoding="utf-8") as fh:
            self.assertEqual(json.load(fh)["statusLine"], mine)


if __name__ == "__main__":
    unittest.main()
