import json
import os
import shutil
import subprocess
import tempfile
import unittest


class TestRoadmapInitGuard(unittest.TestCase):
    """Validate tw-flow roadmap init blocks when ledger already exists.

    Regression test for the ghost-task accumulation bug: init was only
    checking status:pending, so a roadmap that had all phases completed
    would pass the guard and create duplicate ledger entries.
    """

    TEST_PROJECT_ID = "test-roadmap-init-guard"

    def setUp(self):
        self.roadmap_plan = f"{self.TEST_PROJECT_ID}-roadmap"
        self.taskdata = tempfile.mkdtemp(prefix="jacazul-test-roadmap-")
        self.env = os.environ.copy()
        self.env["PROJECT_ID"] = self.TEST_PROJECT_ID
        self.env["TASKDATA"] = self.taskdata

    def tearDown(self):
        shutil.rmtree(self.taskdata, ignore_errors=True)

    def _taskp(self, args, **kwargs):
        return subprocess.run(
            ["taskp"] + args,
            capture_output=True,
            text=True,
            env=self.env,
            **kwargs,
        )

    def _tw_flow(self, args, **kwargs):
        return subprocess.run(
            ["tw-flow"] + args,
            capture_output=True,
            text=True,
            env=self.env,
            **kwargs,
        )

    def _seed_pending_roadmap_task(self):
        """Add a pending sentinel task directly to the roadmap plan."""
        self._taskp(
            ["add", f"project:{self.roadmap_plan}", "sentinel phase"]
        )

    def _seed_completed_roadmap_task(self):
        """Add a task to the roadmap plan and immediately complete it."""
        self._seed_pending_roadmap_task()
        result = self._taskp(
            [f'project:"{self.roadmap_plan}"', "status:pending", "export"]
        )
        tasks = json.loads(result.stdout or "[]")
        for t in tasks:
            self._tw_flow(
                ["outcome", t["uuid"], "Seeded for guard regression test."]
            )
            self._tw_flow(["done", t["uuid"]])

    def test_init_blocked_when_pending_exists(self):
        """init must block if roadmap plan already has pending tasks."""
        self._seed_pending_roadmap_task()
        result = self._tw_flow(["roadmap", "init"])
        self.assertNotEqual(result.returncode, 0)
        output = result.stdout + result.stderr
        self.assertIn("already", output)

    def test_init_blocked_when_only_completed_exists(self):
        """init must block if roadmap plan has only completed tasks.

        Regression: before the fix, init only checked status:pending.
        A ledger with all phases completed (zero pending) would pass the
        guard and accumulate ghost tasks on every subsequent init call.
        """
        self._seed_completed_roadmap_task()

        # Confirm the roadmap has zero pending tasks (guard trigger condition)
        result = self._taskp(
            [f'project:"{self.roadmap_plan}"', "status:pending", "export"]
        )
        self.assertEqual(json.loads(result.stdout or "[]"), [])

        result = self._tw_flow(["roadmap", "init"])
        self.assertNotEqual(result.returncode, 0)
        output = result.stdout + result.stderr
        self.assertIn("already", output)

    def test_init_succeeds_on_empty_db(self):
        """init must succeed when no roadmap plan exists at all."""
        result = self._tw_flow(["roadmap", "init"])
        # Empty DB has no inis to classify — init should not error out
        output = result.stdout + result.stderr
        self.assertNotIn("already", output)


if __name__ == "__main__":
    unittest.main()
