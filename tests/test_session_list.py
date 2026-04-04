import json
import os
import shutil
import subprocess
import tempfile
import time
import unittest


class TestSessionList(unittest.TestCase):
    """Validate tw-flow session list with mtime-based heartbeat."""

    def setUp(self):
        self.taskdata = tempfile.mkdtemp(prefix="jacazul-test-session-")
        self.env = os.environ.copy()
        self.env["TASKDATA"] = self.taskdata
        self.env["PROJECT_ID"] = "test-session-list"

    def tearDown(self):
        shutil.rmtree(self.taskdata, ignore_errors=True)

    def _write_focus(self, session_id, plan, task_uuid):
        path = os.path.join(self.taskdata, f"focus-{session_id}.json")
        with open(path, "w") as f:
            json.dump(
                {
                    "focused_plan": plan,
                    "focused_task_uuid": task_uuid,
                    "task_track": [],
                    "plans_of_interest": [],
                },
                f,
            )
        return path

    def _set_age(self, path, seconds_ago):
        t = time.time() - seconds_ago
        os.utime(path, (t, t))

    def _tw_flow(self, args):
        return subprocess.run(
            ["tw-flow"] + args,
            capture_output=True,
            text=True,
            env=self.env,
        )

    def test_session_list_shows_session_ids(self):
        """session list must display all focus-*.json session IDs."""
        self._write_focus("aabbccdd", "roadmap-engine", "28714fce")
        self._write_focus("11223344", "session-resume", "33a89cb0")
        result = self._tw_flow(["session", "list"])
        self.assertIn("aabbccdd", result.stdout)
        self.assertIn("11223344", result.stdout)

    def test_session_list_shows_plan_and_task(self):
        """session list must show focused plan and task UUID."""
        self._write_focus("aabbccdd", "roadmap-engine", "28714fce")
        result = self._tw_flow(["session", "list"])
        self.assertIn("roadmap-engine", result.stdout)
        self.assertIn("28714fce", result.stdout)

    def test_active_status_within_two_hours(self):
        """Sessions modified less than 2h ago must show as active."""
        path = self._write_focus("aabbccdd", "some-plan", "aaaabbbb")
        self._set_age(path, 3600)  # 1h ago
        result = self._tw_flow(["session", "list"])
        self.assertIn("active", result.stdout)

    def test_idle_status_between_two_and_eight_hours(self):
        """Sessions modified 2-8h ago must show as idle."""
        path = self._write_focus("aabbccdd", "some-plan", "aaaabbbb")
        self._set_age(path, 14400)  # 4h ago
        result = self._tw_flow(["session", "list"])
        self.assertIn("idle", result.stdout)

    def test_orphan_status_older_than_eight_hours(self):
        """Sessions modified more than 8h ago must show as orphan."""
        path = self._write_focus("aabbccdd", "some-plan", "aaaabbbb")
        self._set_age(path, 36000)  # 10h ago
        result = self._tw_flow(["session", "list"])
        self.assertIn("orphan", result.stdout)

    def test_current_session_marked_with_asterisk(self):
        """Current JACAZUL_SESSION_ID must be marked with * in output."""
        self._write_focus("currentsession", "active-plan", "ccccdddd")
        self._write_focus("othersession", "other-plan", "eeeeffff")
        env = self.env.copy()
        env["JACAZUL_SESSION_ID"] = "currentsession"
        result = subprocess.run(
            ["tw-flow", "session", "list"],
            capture_output=True,
            text=True,
            env=env,
        )
        lines = [l for l in result.stdout.splitlines() if "currentsession" in l]
        self.assertTrue(any("*" in l for l in lines))

    def test_other_session_not_marked(self):
        """Sessions other than current must NOT have * marker."""
        self._write_focus("currentsession", "active-plan", "ccccdddd")
        self._write_focus("othersession", "other-plan", "eeeeffff")
        env = self.env.copy()
        env["JACAZUL_SESSION_ID"] = "currentsession"
        result = subprocess.run(
            ["tw-flow", "session", "list"],
            capture_output=True,
            text=True,
            env=env,
        )
        lines = [l for l in result.stdout.splitlines() if "othersession" in l]
        self.assertTrue(all("*" not in l for l in lines))

    def test_heartbeat_updates_mtime(self):
        """Any tw-flow command must touch the active session file."""
        env = self.env.copy()
        env["JACAZUL_SESSION_ID"] = "heartbeattest"
        path = os.path.join(self.taskdata, "focus-heartbeattest.json")
        with open(path, "w") as f:
            json.dump(
                {
                    "focused_plan": "some-plan",
                    "focused_task_uuid": "aaaabbbb",
                    "task_track": [],
                    "plans_of_interest": [],
                },
                f,
            )
        # Age it to 1h ago
        self._set_age(path, 3600)
        mtime_before = os.path.getmtime(path)

        # Run any tw-flow command
        subprocess.run(
            ["tw-flow", "session", "list"],
            capture_output=True,
            env=env,
        )

        mtime_after = os.path.getmtime(path)
        self.assertGreater(mtime_after, mtime_before)

    def test_empty_session_dir_shows_no_sessions(self):
        """session list with no focus files must not error out."""
        result = self._tw_flow(["session", "list"])
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
