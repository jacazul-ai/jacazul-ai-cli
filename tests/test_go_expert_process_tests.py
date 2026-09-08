import pathlib
import unittest


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
PLAYBOOK = PROJECT_ROOT / "skills" / "go-expert" / "PLAYBOOK.md"
CODE_REVIEW = PROJECT_ROOT / "skills" / "go-expert" / "CODE-REVIEW.md"
DOCS = PROJECT_ROOT / "docs" / "go-expert.md"


class TestGoExpertProcessTests(unittest.TestCase):
    def test_playbook_documents_env_guarded_helper_processes(self):
        content = PLAYBOOK.read_text(encoding="utf-8")

        for marker in (
            "GO_WANT_HELPER_PROCESS",
            "GO_WANT_EPOCH_HELPER",
            "os.Executable()",
            "-test.run",
            "TZ",
        ):
            self.assertIn(marker, content)

    def test_review_and_user_docs_cover_the_contract(self):
        review = CODE_REVIEW.read_text(encoding="utf-8")
        docs = DOCS.read_text(encoding="utf-8")

        self.assertIn("os.Executable()", review)
        self.assertIn("init", review)
        self.assertIn("date", docs.lower())
        self.assertIn("environment", docs.lower())


if __name__ == "__main__":
    unittest.main()
