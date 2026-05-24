import pathlib
import unittest


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]


class TestUserLaunchers(unittest.TestCase):
    def test_jacazul_github_uses_project_wrapper(self):
        configure = (PROJECT_ROOT / "scripts" / "configure").read_text()

        self.assertIn(
            "jacazul-github:scripts/jacazul-github",
            configure,
        )
        self.assertIn("$HOME/.local/bin/jacazul-github", configure)
        self.assertIn("from jacazul.cli.github import main", configure)
        self.assertNotIn(
            "jacazul-github:$HOME/.jacazul-ai/.venv/bin/jacazul-github",
            configure,
        )

    def test_jacazul_github_wrapper_is_portable(self):
        launcher = PROJECT_ROOT / "scripts" / "jacazul-github"
        content = launcher.read_text()

        self.assertTrue(content.startswith("#!/usr/bin/env bash\n"))
        self.assertNotIn("/home/fpiraz", content)
        self.assertIn("$HOME/.jacazul-ai/.venv", content)
        self.assertIn("-m", content)
        self.assertIn("jacazul.cli.github", content)


if __name__ == "__main__":
    unittest.main()
