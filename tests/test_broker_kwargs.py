import unittest
import subprocess


class TestBrokerKwargs(unittest.TestCase):
    def test_open_issue_kwarg_validation(self):
        """Verify that 'open' requires 'title=' kwarg."""
        res = subprocess.run(
            ["jacazul-broker", "open", "JustATitle"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 1)
        self.assertIn(
            "ACTION: Use 'jacazul-broker open title=\"My title\"'", res.stderr
        )

    def test_open_issue_dry_run_ish(self):
        """Verify that 'open' with title= works (using sandbox repo)."""
        # Note: This will actually try to create an issue if GH_TOKEN is set.
        # Use a fake repo so it fails at gh level but passes our parser.
        res = subprocess.run(
            [
                "jacazul-broker",
                "open",
                "title=Test Issue",
                "repo=jacazul-ai/jacazul-ai-sandbox",
                "body=Test Body",
            ],
            capture_output=True,
            text=True,
        )

        # If not authenticated, gh fails — check that our parser worked.
        # If it failed at gh, stderr will contain gh error.
        # If it failed at our parser, it would hit the 'Title required' error.
        self.assertNotIn("Title required to open issue", res.stderr)


    def test_view_issue_requires_id(self):
        """Verify that 'view' without issue ID returns error."""
        res = subprocess.run(
            ["jacazul-broker", "view"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 1)
        self.assertIn(
            "ACTION: Use 'jacazul-broker view #123'", res.stderr
        )

    def test_view_issue_calls_gh(self):
        """Verify that 'view' reaches gh (not blocked by our parser)."""
        # Uses a fake repo — fails at gh level, not our parser.
        res = subprocess.run(
            ["jacazul-broker", "view", "1",
             "jacazul-ai/jacazul-ai-sandbox"],
            capture_output=True,
            text=True,
        )
        self.assertNotIn(
            "ACTION: Use 'jacazul-broker view #123'", res.stderr
        )

if __name__ == "__main__":
    unittest.main()
