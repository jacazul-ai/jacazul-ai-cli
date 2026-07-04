import pathlib
import unittest


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]


class TestConfigureBootstrap(unittest.TestCase):
    def test_init_venv_matches_configure_venv_path(self):
        configure = (PROJECT_ROOT / "scripts" / "configure").read_text()
        init_venv = (PROJECT_ROOT / "scripts" / "init-venv.sh").read_text()

        self.assertIn('VENV_ROOT="$HOME/.jacazul-ai/.venv"', configure)
        self.assertIn('VENV_BIN="$VENV_ROOT/bin"', configure)
        self.assertIn('VENV_PATH="$HOME/.jacazul-ai/.venv"', init_venv)
        self.assertNotIn('VENV_PATH="/project/sandbox/venv"', init_venv)

    def test_configure_removes_only_broken_jacazul_venv(self):
        configure = (PROJECT_ROOT / "scripts" / "configure").read_text()

        self.assertIn('rm -rf "$VENV_ROOT"', configure)
        self.assertIn('"$VENV_ROOT" = "$HOME/.jacazul-ai/.venv"', configure)
        self.assertIn("Removing broken Python virtual environment", configure)

    def test_configure_only_runs_chcon_when_selinux_is_active(self):
        configure = (PROJECT_ROOT / "scripts" / "configure").read_text()

        self.assertIn("SELINUX_STATUS=", configure)
        self.assertIn('"$SELINUX_STATUS" = "Enforcing"', configure)
        self.assertIn('"$SELINUX_STATUS" = "Permissive"', configure)
        self.assertIn("Skipping SELinux configuration", configure)


if __name__ == "__main__":
    unittest.main()
