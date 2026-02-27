import re
import orjson
import os
from .base import JakaTest

class FlowTest(JakaTest):
    """Atomic tests for the 7-phase Taskwarrior workflow."""

    def setUp(self):
        super().setUp()
        self.run_cmd(f"{self.tw_flow} ini test_ini 'Step 1|research|today' 'Step 2|implementation|tomorrow'")
        out, _, _ = self.run_cmd(f"{self.taskp} project:test_ini export")
        tasks = orjson.loads(out)
        self.u1 = tasks[0]["uuid"]
        self.u2 = tasks[1]["uuid"]

    def test_initiative_creation_emits_short_uuid(self):
        """Standardization: Initiative creation must output 8-char short UUIDs."""
        out, _, _ = self.run_cmd(f"{self.tw_flow} ini new_ini 'Task|r|today'")
        self.assertTrue(re.search(r'Created task [0-9a-f]{8}:', out), "Output missing short UUID")

    def test_initiatives_list_display(self):
        """Initiatives command must list projects with pending tasks."""
        out, _, _ = self.run_cmd(f"{self.tw_flow} inis")
        self.assertIn("test_ini", out)

    def test_status_split_view_content(self):
        """Status command must show PENDING tasks and split-view layout."""
        out, _, _ = self.run_cmd(f"{self.tw_flow} status test_ini")
        self.assertIn("PENDING:", out)
        self.assertIn("Initiative: test_ini", out)

    def test_next_task_readiness_logic(self):
        """Next command must correctly identify the first unblocked task."""
        out, _, _ = self.run_cmd(f"{self.tw_flow} next test_ini")
        self.assertIn("Step 1", out)

    def test_execute_marks_task_active(self):
        """Execution logic: Task must be marked ACTIVE in the database."""
        self.run_cmd(f"{self.tw_flow} execute {self.u1}")
        out, _, _ = self.run_cmd(f"{self.taskp} +ACTIVE export")
        tasks = orjson.loads(out or "[]")
        self.assertTrue(any(t.get('uuid') == self.u1 for t in tasks))

    def test_note_prefix_persistence(self):
        """Context: Structured notes must persist with correct uppercase prefixes."""
        self.run_cmd(f"{self.tw_flow} note {self.u1} decision 'Standardized'")
        out, _, _ = self.run_cmd(f"{self.taskp} {self.u1} export")
        annots = [a["description"] for a in orjson.loads(out or "[]")[0].get("annotations", [])]
        self.assertIn("DECISION: Standardized", annots)

    def test_context_command_retrieval(self):
        """Context retrieval: Context command must display task annotations."""
        self.run_cmd(f"{self.tw_flow} note {self.u1} research 'Investigation'")
        out, _, _ = self.run_cmd(f"{self.tw_flow} context {self.u1}")
        self.assertIn("RESEARCH: Investigation", out)

    def test_active_filter_output(self):
        """Filters: Active filter must only show tasks in ACTIVE state."""
        self.run_cmd(f"{self.tw_flow} execute {self.u1}")
        out, _, _ = self.run_cmd(f"{self.tw_flow} active")
        self.assertIn("Step 1", out)

    def test_initiative_prepends_mode_prefix(self):
        """Interaction modes: Initiative must correctly prepend [MODE] to descriptions."""
        out, _, _ = self.run_cmd(f"{self.tw_flow} ini mode_test 'PLAN|Architecture|r|today'")
        self.assertIn("[PLAN] Architecture", out)

    def test_ponder_dashboard_mode_highlighting(self):
        """Ponder: Tactical dashboard must highlight interaction modes."""
        self.run_cmd(f"{self.tw_flow} ini mode_test 'GUIDE|Instructions|r|today'")
        out, _, _ = self.run_cmd(f"{self.ponder} test_project")
        self.assertIn("GUIDE", out)

    def test_handoff_protocol_execution(self):
        """Handoff: Protocol must add note AND automatically execute the next task."""
        self.run_cmd(f"{self.tw_flow} outcome {self.u1} 'Finished'")
        self.run_cmd(f"{self.tw_flow} done {self.u1}")
        self.run_cmd(f"{self.tw_flow} handoff {self.u2} 'Start Step 2'")
        out, _, _ = self.run_cmd(f"{self.taskp} {self.u2} export")
        task = orjson.loads(out or "[]")[0]
        self.assertTrue(any("HANDOFF: Start Step 2" in a["description"] for a in task.get("annotations", [])))
        self.assertTrue(task.get("start"), "Next task not auto-executed during handoff")

    def test_done_enforces_outcome_annotation(self):
        """Safety: Done command must fail if OUTCOME annotation is missing."""
        out, err, code = self.run_cmd(f"{self.tw_flow} done {self.u1}")
        self.assertNotEqual(code, 0)
        self.assertIn("cannot be completed without an OUTCOME", out + err)

    def test_done_success_with_outcome(self):
        """Happy path: Done command succeeds when OUTCOME is present."""
        self.run_cmd(f"{self.tw_flow} outcome {self.u1} 'Verified'")
        _, _, code = self.run_cmd(f"{self.tw_flow} done {self.u1}")
        self.assertEqual(code, 0)

    def test_focus_heap_accumulation(self):
        """Anchor System: Focus stack must accumulate multiple anchored tasks."""
        self.run_cmd(f"{self.tw_flow} focus ini test_ini")
        self.run_cmd(f"{self.tw_flow} ini other_ini 'Task|r|today'")
        self.run_cmd(f"{self.tw_flow} focus ini other_ini")
        
        focus_file = os.path.join(self.taskdata, "focus.json")
        with open(focus_file, "rb") as f:
            state = orjson.loads(f.read())
            self.assertGreaterEqual(len(state.get("task_track", [])), 2)

    def test_ponder_interest_filtering_logic(self):
        """Dashboard: Ponder must filter projects by interest and support --all bypass."""
        self.run_cmd(f"{self.tw_flow} ini boring 'Hidden Task|r|today'")
        self.run_cmd(f"{self.tw_flow} focus interest add test_ini")
        
        out, _, _ = self.run_cmd(f"{self.ponder} test_project")
        self.assertIn("test_ini", out)
        self.assertNotIn("boring", out)
        
        out_all, _, _ = self.run_cmd(f"{self.ponder} --all test_project")
        self.assertIn("boring", out_all)
