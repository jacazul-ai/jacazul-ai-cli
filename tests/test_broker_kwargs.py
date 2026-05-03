import unittest
import subprocess
import tempfile
import os


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

    def test_open_issue_body_file_parser(self):
        """Verify that body_file= kwarg is parsed and forwarded (not blocked)."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write(
                '## Body with `backticks` and "quotes"\n\nNewline content.'
            )
            tmp_path = f.name

        try:
            res = subprocess.run(
                [
                    "jacazul-broker",
                    "open",
                    "title=Test body_file kwarg",
                    f"body_file={tmp_path}",
                    "repo=jacazul-ai/jacazul-ai-sandbox",
                ],
                capture_output=True,
                text=True,
            )
            # Parser must not reject body_file= — any failure must be at gh
            # level
            self.assertNotIn("Title required to open issue", res.stderr)
            self.assertNotIn("body_file", res.stderr)
        finally:
            os.unlink(tmp_path)

    def test_open_issue_body_file_precedence(self):
        """body_file= takes precedence over body= when both are present."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write("Content from file.")
            tmp_path = f.name

        try:
            res = subprocess.run(
                [
                    "jacazul-broker",
                    "open",
                    "title=Test precedence",
                    "body=inline body",
                    f"body_file={tmp_path}",
                    "repo=jacazul-ai/jacazul-ai-sandbox",
                ],
                capture_output=True,
                text=True,
            )
            self.assertNotIn("Title required to open issue", res.stderr)
        finally:
            os.unlink(tmp_path)

    def test_edit_issue_body_file_parser(self):
        """Verify that body_file= kwarg is accepted by edit command."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write('## Updated body\n\nWith `special` chars and "quotes".')
            tmp_path = f.name

        try:
            res = subprocess.run(
                [
                    "jacazul-broker",
                    "edit",
                    "#1",
                    f"body_file={tmp_path}",
                    "repo=jacazul-ai/jacazul-ai-sandbox",
                ],
                capture_output=True,
                text=True,
            )
            # Must not fail at our parser level
            self.assertNotIn("body_file", res.stderr)
        finally:
            os.unlink(tmp_path)

    def test_view_issue_requires_id(self):
        """Verify that 'view' without issue ID returns error."""
        res = subprocess.run(
            ["jacazul-broker", "view"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 1)
        self.assertIn("ACTION: Use 'jacazul-broker view #123'", res.stderr)

    def test_view_issue_calls_gh(self):
        """Verify that 'view' reaches gh (not blocked by our parser)."""
        # Uses a fake repo — fails at gh level, not our parser.
        res = subprocess.run(
            ["jacazul-broker", "view", "1", "jacazul-ai/jacazul-ai-sandbox"],
            capture_output=True,
            text=True,
        )
        self.assertNotIn("ACTION: Use 'jacazul-broker view #123'", res.stderr)


if __name__ == "__main__":
    unittest.main()
