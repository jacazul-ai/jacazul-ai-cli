import unittest
import json
from .base import JacazulTest


class TestBacklogFeature(JacazulTest):
    """Validate backlog plan state and --with-backlog flag behavior."""

    SANDBOX_PLAN = "test-backlog-sandbox"

    def setUp(self):
        """Create a temporary plan for testing."""
        super().setUp()
        self.run_cmd(
            f"{self.tw_flow} plan {self.SANDBOX_PLAN} 'EXECUTE|Backlog test task|testing'"
        )

    def tearDown(self):
        """Discard all tasks in the sandbox plan."""
        out, _, _ = self.run_cmd(
            f"{self.taskp} project:{self.SANDBOX_PLAN} status:pending export"
        )
        try:
            tasks = json.loads(out)
            for t in tasks:
                self.run_cmd(f"{self.tw_flow} discard {t['uuid']}")
        except Exception:
            pass
        super().tearDown()

    def test_backlog_hides_plan_from_plans(self):
        """Plan in backlog must not appear in tw-flow plans default view."""
        self.run_cmd(f"{self.tw_flow} backlog {self.SANDBOX_PLAN}")
        out, _, _ = self.run_cmd(f"{self.tw_flow} plans --force")
        self.assertNotIn(self.SANDBOX_PLAN, out)

    def test_with_backlog_shows_plan(self):
        """--with-backlog must reveal backlog plans with 💤 marker."""
        self.run_cmd(f"{self.tw_flow} backlog {self.SANDBOX_PLAN}")
        out, _, _ = self.run_cmd(f"{self.tw_flow} plans --with-backlog --force")
        self.assertIn(self.SANDBOX_PLAN, out)
        self.assertIn("💤", out)
        self.assertIn("BACKLOG", out)

    def test_activate_restores_plan_to_active(self):
        """activate must remove backlog state and restore plan to active."""
        self.run_cmd(f"{self.tw_flow} backlog {self.SANDBOX_PLAN}")
        self.run_cmd(f"{self.tw_flow} activate {self.SANDBOX_PLAN}")
        out, _, _ = self.run_cmd(f"{self.tw_flow} plans --force")
        self.assertIn(self.SANDBOX_PLAN, out)
        self.assertNotIn("💤", out)

    def test_backlog_command_success_message(self):
        """tw-flow backlog must emit success confirmation."""
        out, _, _ = self.run_cmd(f"{self.tw_flow} backlog {self.SANDBOX_PLAN}")
        self.assertIn("moved to backlog", out)
        self.assertIn("💤", out)

    def test_activate_command_success_message(self):
        """tw-flow activate must emit success confirmation."""
        self.run_cmd(f"{self.tw_flow} backlog {self.SANDBOX_PLAN}")
        out, _, _ = self.run_cmd(f"{self.tw_flow} activate {self.SANDBOX_PLAN}")
        self.assertIn("activated", out)


if __name__ == "__main__":
    unittest.main()
