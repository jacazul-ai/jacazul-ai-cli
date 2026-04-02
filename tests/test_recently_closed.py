import json
import subprocess
import unittest


class TestRecentlyClosed(unittest.TestCase):
    """Validate Recently Closed section in tw-flow ponder output."""

    SANDBOX_PLAN = "test-recently-closed-sandbox"

    def setUp(self):
        """Create a plan, complete all tasks, so it becomes zeroed."""
        subprocess.run(
            [
                "tw-flow",
                "plan",
                self.SANDBOX_PLAN,
                "EXECUTE|Recently closed test task|testing",
            ],
            capture_output=True,
        )
        result = subprocess.run(
            [
                "taskp",
                f'project:"{self.SANDBOX_PLAN}"',
                "status:pending",
                "export",
            ],
            capture_output=True,
            text=True,
        )
        tasks = json.loads(result.stdout or "[]")
        for t in tasks:
            subprocess.run(
                [
                    "tw-flow",
                    "outcome",
                    t["uuid"],
                    "Test outcome for recently closed validation.",
                ],
                capture_output=True,
            )
            subprocess.run(
                ["tw-flow", "done", t["uuid"]],
                capture_output=True,
            )

    def tearDown(self):
        """Delete completed sandbox tasks to keep the database clean."""
        result = subprocess.run(
            [
                "taskp",
                f'project:"{self.SANDBOX_PLAN}"',
                "status:completed",
                "export",
            ],
            capture_output=True,
            text=True,
        )
        tasks = json.loads(result.stdout or "[]")
        for t in tasks:
            subprocess.run(
                ["taskp", t["uuid"], "delete"],
                input="yes\n",
                capture_output=True,
                text=True,
            )

    def test_recently_closed_section_present(self):
        """Ponder must include a RECENTLY CLOSED section."""
        result = subprocess.run(
            ["tw-flow", "ponder", "--force"],
            capture_output=True,
            text=True,
        )
        self.assertIn("RECENTLY CLOSED", result.stdout)

    def test_recently_closed_shows_zeroed_plan(self):
        """Zeroed sandbox plan must appear in Recently Closed."""
        result = subprocess.run(
            ["tw-flow", "ponder", "--force"],
            capture_output=True,
            text=True,
        )
        self.assertIn(self.SANDBOX_PLAN, result.stdout)

    def test_recently_closed_shows_outcome(self):
        """Recently Closed entry must include the OUTCOME annotation."""
        result = subprocess.run(
            ["tw-flow", "ponder", "--force"],
            capture_output=True,
            text=True,
        )
        self.assertIn(
            "Test outcome for recently closed validation", result.stdout
        )

    def test_recently_closed_no_extra_requests(self):
        """Single ponder call must be sufficient to surface project history.

        This test validates the zero-extra-requests requirement: the
        Recently Closed section must be present in a single ponder call
        without any follow-up queries needed to understand past state.
        """
        result = subprocess.run(
            ["tw-flow", "ponder", "--force"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("RECENTLY CLOSED", result.stdout)
        self.assertIn(self.SANDBOX_PLAN, result.stdout)


if __name__ == "__main__":
    unittest.main()
