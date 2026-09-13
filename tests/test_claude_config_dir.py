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
        os.makedirs(self.home, exist_ok=True)
        os.makedirs(self.jacazul_home, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _source_bootstrap(self, extra_env=None, command_suffix=""):
        env = os.environ.copy()
        env.pop("CLAUDE_CONFIG_DIR", None)
        env.update({"HOME": self.home, "JACAZUL_HOME": self.jacazul_home})
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            f'source "{BOOTSTRAP_CLAUDE}" {command_suffix}'.strip(),
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
        self.assertFalse(os.path.exists(os.path.join(self.home, ".claude")))

    def test_bootstrap_defaults_under_jacazul_home(self):
        default_dir = os.path.join(self.jacazul_home, "agents", "claude")

        result = self._source_bootstrap()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(os.path.isdir(os.path.join(default_dir, "skills")))
        self.assertTrue(
            os.path.isfile(os.path.join(default_dir, "settings.json"))
        )

    def test_anchored_dir_starts_clean_and_links_project_skills(self):
        default_dir = os.path.join(self.jacazul_home, "agents", "claude")

        result = self._source_bootstrap()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        skills_dir = os.path.join(default_dir, "skills")
        linked = sorted(os.listdir(skills_dir))
        # jacazul-engine is a generated artifact and is not in the repo, so
        # anchor on a committed skill instead.
        self.assertIn("git-expert", linked)
        for name in linked:
            entry = os.path.join(skills_dir, name)
            self.assertTrue(os.path.islink(entry), msg=f"{name} is not a link")
            self.assertEqual(
                os.path.realpath(entry),
                str(PROJECT_ROOT / "skills" / name),
            )
        # A fresh anchored dir carries no credential or history.
        self.assertFalse(
            os.path.exists(os.path.join(default_dir, ".credentials.json"))
        )
        self.assertFalse(
            os.path.exists(os.path.join(default_dir, "history.jsonl"))
        )

    def test_legacy_tree_is_never_touched(self):
        legacy = self._make_legacy_tree()
        creds = os.path.join(legacy, ".credentials.json")
        before = os.stat(creds)

        result = self._source_bootstrap()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(os.path.isdir(legacy))
        self.assertTrue(os.path.isfile(creds))
        self.assertTrue(os.path.isfile(os.path.join(legacy, "history.jsonl")))
        after = os.stat(creds)
        self.assertEqual(before.st_mtime, after.st_mtime)
        self.assertEqual(
            stat.S_IMODE(after.st_mode), stat.S_IRUSR | stat.S_IWUSR
        )

    def test_legacy_dir_is_usable_as_an_explicit_rollback_target(self):
        legacy = self._make_legacy_tree()

        result = self._source_bootstrap(
            extra_env={"CLAUDE_CONFIG_DIR": legacy}
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(os.path.isdir(os.path.join(legacy, "skills")))
        self.assertTrue(
            os.path.isfile(os.path.join(legacy, ".credentials.json"))
        )

    def test_wrapper_flags_are_never_read_as_a_config_dir(self):
        """Regression for #65.

        The bootstrap is sourced by jacazul-claude, so any argument the
        wrapper received is still visible as $1. It must resolve the config
        dir from the environment only, never from a positional argument.
        """
        flags = "--resume --jacazul-session abc123 --dangerously-skip"
        default_dir = os.path.join(self.jacazul_home, "agents", "claude")

        result = self._source_bootstrap(command_suffix=flags)

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(os.path.isdir(os.path.join(default_dir, "skills")))
        for parent in (self.home, self.test_dir, str(PROJECT_ROOT)):
            stray = [n for n in os.listdir(parent) if n.startswith("--")]
            self.assertEqual(stray, [], msg=f"flag-named path in {parent}")

    def _write_settings(self, value):
        target = os.path.join(self.jacazul_home, "agents", "claude")
        os.makedirs(target, exist_ok=True)
        settings = os.path.join(target, "settings.json")
        with open(settings, "w", encoding="utf-8") as fh:
            json.dump({"statusLine": value}, fh)
        return target, settings

    def _read_statusline(self, settings):
        with open(settings, encoding="utf-8") as fh:
            return json.load(fh)["statusLine"]

    def test_statusline_is_written_as_a_command_object(self):
        """Claude Code rejects a bare string path for statusLine."""
        target = os.path.join(self.jacazul_home, "agents", "claude")

        result = self._source_bootstrap()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        value = self._read_statusline(os.path.join(target, "settings.json"))
        self.assertEqual(
            value,
            {
                "type": "command",
                "command": os.path.join(
                    target, "extensions", "jacazul-line.sh"
                ),
            },
        )

    def test_legacy_string_statusline_is_upgraded_to_an_object(self):
        stale = "/home/someone/.claude/extensions/jacazul-line.sh"
        target, settings = self._write_settings(stale)

        result = self._source_bootstrap()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(
            self._read_statusline(settings),
            {
                "type": "command",
                "command": os.path.join(
                    target, "extensions", "jacazul-line.sh"
                ),
            },
        )

    def test_stale_object_statusline_is_rehomed(self):
        stale = {
            "type": "command",
            "command": "/home/someone/.claude/extensions/jacazul-line.sh",
        }
        target, settings = self._write_settings(stale)

        result = self._source_bootstrap()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(
            self._read_statusline(settings)["command"],
            os.path.join(target, "extensions", "jacazul-line.sh"),
        )

    def test_user_owned_statusline_is_left_alone(self):
        mine = {"type": "command", "command": "/home/someone/bin/mine.sh"}
        _, settings = self._write_settings(mine)

        result = self._source_bootstrap()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(self._read_statusline(settings), mine)


if __name__ == "__main__":
    unittest.main()
