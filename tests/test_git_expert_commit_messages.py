from pathlib import Path
import subprocess
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = PROJECT_ROOT / "skills" / "git-expert" / "SKILL.md"


class GitExpertCommitMessageTest(unittest.TestCase):
    """Verify the commit-message transport guardrail and its mechanism."""

    def test_skill_requires_file_based_messages_for_bodies(self):
        skill = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("A commit that includes a body MUST", skill)
        self.assertIn("git commit -F <file>", skill)
        self.assertIn("title-only commit", skill)
        self.assertIn("literal `\\n`", skill)
        self.assertIn("git log -1 --format=%b | cat -A", skill)

    def test_git_preserves_literal_escape_and_file_messages_preserve_lines(
        self,
    ):
        with tempfile.TemporaryDirectory(prefix="git-message-test-") as path:
            repo = Path(path)
            self._git(repo, "init", "-q")
            self._git(repo, "config", "user.name", "Commit Message Test")
            self._git(
                repo,
                "config",
                "user.email",
                "commit-message-test@example.invalid",
            )
            self._git(repo, "config", "commit.gpgsign", "false")

            (repo / "file").write_text("one", encoding="utf-8")
            self._git(repo, "add", "file")
            self._git(repo, "commit", "-q", "-m", r"fix: literal\n\nBody")
            literal_body = self._git(repo, "log", "-1", "--format=%B")
            self.assertIn(r"\n", literal_body)

            (repo / "file").write_text("two", encoding="utf-8")
            self._git(repo, "add", "file")
            message_file = repo / "message.txt"
            message_file.write_text(
                "fix: safe message\n\nBody line\n", encoding="utf-8"
            )
            self._git(repo, "commit", "-q", "-F", str(message_file))
            safe_body = self._git(repo, "log", "-1", "--format=%B")
            self.assertNotIn(r"\n", safe_body)
            self.assertIn("Body line\n", safe_body)

    @staticmethod
    def _git(repo: Path, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout


if __name__ == "__main__":
    unittest.main()
