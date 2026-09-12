import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
BOOTSTRAP_OPENCODE = PROJECT_ROOT / "scripts" / "bootstrap" / "opencode"


class TestOpencodeConfigDir(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="jacazul_opencode_cfg_")
        self.home = os.path.join(self.test_dir, "home")
        self.jacazul_home = os.path.join(self.home, ".jacazul-ai")
        os.makedirs(self.home, exist_ok=True)
        os.makedirs(self.jacazul_home, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _source_bootstrap(self, extra_env=None):
        env = os.environ.copy()
        env.update({"HOME": self.home, "JACAZUL_HOME": self.jacazul_home})
        env.pop("XDG_CONFIG_HOME", None)
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            f'source "{BOOTSTRAP_OPENCODE}"',
            cwd=str(PROJECT_ROOT),
            env=env,
            shell=True,
            executable="/bin/bash",
            capture_output=True,
            text=True,
        )

    def test_bootstrap_defaults_under_anchored_xdg_config_home(self):
        result = self._source_bootstrap()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        anchored = os.path.join(self.jacazul_home, "agents", "opencode")
        self.assertTrue(os.path.isdir(os.path.join(anchored, "agents")))
        self.assertTrue(os.path.isdir(os.path.join(anchored, "skills")))
        self.assertFalse(os.path.exists(os.path.join(self.home, ".config")))

    def test_bootstrap_honors_explicit_xdg_config_home(self):
        custom = os.path.join(self.test_dir, "custom-config")

        result = self._source_bootstrap(extra_env={"XDG_CONFIG_HOME": custom})

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(
            os.path.isdir(os.path.join(custom, "opencode", "agents"))
        )
        self.assertFalse(
            os.path.exists(
                os.path.join(self.jacazul_home, "agents", "opencode")
            )
        )

    def test_bootstrap_migrates_legacy_global_directory(self):
        legacy = os.path.join(self.home, ".config", "opencode")
        os.makedirs(legacy, exist_ok=True)
        marker = os.path.join(legacy, "opencode.json")
        pathlib.Path(marker).write_text('{"legacy":true}\n', encoding="utf-8")

        result = self._source_bootstrap()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        anchored = os.path.join(self.jacazul_home, "agents", "opencode")
        self.assertTrue(
            os.path.isfile(os.path.join(anchored, "opencode.json"))
        )
        self.assertFalse(os.path.exists(legacy))


if __name__ == "__main__":
    unittest.main()
