import subprocess
import unittest


class TestBacklogFeature(unittest.TestCase):
    """Validate backlog plan state and --with-backlog flag behavior."""

    SANDBOX_PLAN = "test-backlog-sandbox"

    def setUp(self):
        """Create a temporary plan for testing."""
        subprocess.run(
            [
                "tw-flow",
                "plan",
                self.SANDBOX_PLAN,
                "EXECUTE|Backlog test task|testing",
            ],
            capture_output=True,
        )

    def tearDown(self):
        """Discard all tasks in the sandbox plan."""
        result = subprocess.run(
            ["taskp", f'project:"{self.SANDBOX_PLAN}"',
             "status:pending", "export"],
            capture_output=True,
            text=True,
        )
        import json

        try:
            tasks = json.loads(result.stdout)
            for t in tasks:
                subprocess.run(
                    ["tw-flow", "discard", t["uuid"]],
                    capture_output=True,
                )
        except Exception:
            pass

    def test_backlog_hides_plan_from_plans(self):
        """Plan in backlog must not appear in tw-flow plans default view."""
        subprocess.run(
            ["tw-flow", "backlog", self.SANDBOX_PLAN],
            capture_output=True,
        )
        result = subprocess.run(
            ["tw-flow", "plans", "--force"],
            capture_output=True,
            text=True,
        )
        self.assertNotIn(self.SANDBOX_PLAN, result.stdout)

    def test_with_backlog_shows_plan(self):
        """--with-backlog must reveal backlog plans with 💤 marker."""
        subprocess.run(
            ["tw-flow", "backlog", self.SANDBOX_PLAN],
            capture_output=True,
        )
        result = subprocess.run(
            ["tw-flow", "plans", "--with-backlog", "--force"],
            capture_output=True,
            text=True,
        )
        self.assertIn(self.SANDBOX_PLAN, result.stdout)
        self.assertIn("💤", result.stdout)
        self.assertIn("BACKLOG", result.stdout)

    def test_activate_restores_plan_to_active(self):
        """activate must remove backlog state and restore plan to active."""
        subprocess.run(
            ["tw-flow", "backlog", self.SANDBOX_PLAN],
            capture_output=True,
        )
        subprocess.run(
            ["tw-flow", "activate", self.SANDBOX_PLAN],
            capture_output=True,
        )
        result = subprocess.run(
            ["tw-flow", "plans", "--force"],
            capture_output=True,
            text=True,
        )
        self.assertIn(self.SANDBOX_PLAN, result.stdout)
        self.assertNotIn("💤", result.stdout)

    def test_backlog_command_success_message(self):
        """tw-flow backlog must emit success confirmation."""
        result = subprocess.run(
            ["tw-flow", "backlog", self.SANDBOX_PLAN],
            capture_output=True,
            text=True,
        )
        self.assertIn("moved to backlog", result.stdout)
        self.assertIn("💤", result.stdout)

    def test_activate_command_success_message(self):
        """tw-flow activate must emit success confirmation."""
        subprocess.run(
            ["tw-flow", "backlog", self.SANDBOX_PLAN],
            capture_output=True,
        )
        result = subprocess.run(
            ["tw-flow", "activate", self.SANDBOX_PLAN],
            capture_output=True,
            text=True,
        )
        self.assertIn("activated", result.stdout)


if __name__ == "__main__":
    unittest.main()
