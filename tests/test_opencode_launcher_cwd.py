import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
LAUNCHER = PROJECT_ROOT / "scripts" / "jacazul-opencode"


class TestOpencodeLauncherCwd(unittest.TestCase):
    def setUp(self):
        self.test_dir = pathlib.Path(
            tempfile.mkdtemp(prefix="jacazul_opencode_cwd_")
        )
        self.home = self.test_dir / "home"
        self.fake_bin = self.test_dir / "bin"
        self.workdir = self.test_dir / "workspace"
        self.log = self.test_dir / "opencode-args.log"
        self.home.mkdir()
        self.fake_bin.mkdir()
        self.workdir.mkdir()
        fake_opencode = self.fake_bin / "opencode"
        fake_opencode.write_text(
            "#!/bin/bash\n"
            f'printf "cwd=%s\\n" "$PWD" >> "{self.log}"\n'
            f'printf "args=%s\\n" "$*" >> "{self.log}"\n',
            encoding="utf-8",
        )
        fake_opencode.chmod(0o755)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_launcher_preserves_cwd_outside_project_root(self):
        env = os.environ.copy()
        env.update(
            {
                "HOME": str(self.home),
                "JACAZUL_HOME": str(self.home / ".jacazul-ai"),
                "XDG_CONFIG_HOME": str(self.test_dir / "config"),
                "PATH": f"{self.fake_bin}:{env['PATH']}",
            }
        )
        for key in (
            "CLAUDE_CONFIG_DIR",
            "JACAZUL_ENV_INITIALIZED",
            "JACAZUL_SESSION_ID",
        ):
            env.pop(key, None)

        result = subprocess.run(
            [str(LAUNCHER), "--message", "hello"],
            cwd=self.workdir,
            env=env,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        output = self.log.read_text(encoding="utf-8")
        self.assertIn(f"cwd={self.workdir}\n", output)
        self.assertIn("args=--agent jacazul --message hello\n", output)
        self.assertNotIn(f"{PROJECT_ROOT} ", output)


if __name__ == "__main__":
    unittest.main()
