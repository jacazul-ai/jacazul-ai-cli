#!/home/fpiraz/.jacazul-ai/.venv/bin/python
import re
import orjson
import os
from .base import JacazulTest

class FlowTest(JacazulTest):
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
        """Status command must show PENDING and COMPLETED tasks by default."""
        self.run_cmd(f"{self.tw_flow} outcome {self.u1} 'Done'")
        self.run_cmd(f"{self.tw_flow} done {self.u1}")
        
        out, _, _ = self.run_cmd(f"{self.tw_flow} status test_ini")
        self.assertIn("PENDING:", out)
        self.assertIn("COMPLETED:", out)
        self.assertIn("Step 1", out)
        self.assertIn("Step 2", out)

    def test_status_pending_flag_filters_completed(self):
        """Status: --pending flag must hide completed tasks."""
        self.run_cmd(f"{self.tw_flow} outcome {self.u1} 'Done'")
        self.run_cmd(f"{self.tw_flow} done {self.u1}")
        
        out, _, _ = self.run_cmd(f"{self.tw_flow} status test_ini --pending")
        self.assertIn("PENDING:", out)
        self.assertNotIn("COMPLETED:", out)
        self.assertNotIn("Step 1", out)
        self.assertIn("Step 2", out)

    def test_status_shows_ticket_in_line(self):
        """Status: Task lines must include direct or inherited tickets."""
        self.run_cmd(f"{self.tw_flow} ticket {self.u1} '#TKT-123'")
        out, _, _ = self.run_cmd(f"{self.tw_flow} status test_ini")
        self.assertIn("[#TKT-123] Step 1", out)
        # u2 inherits from u1
        self.assertIn("[#TKT-123] Step 2", out)

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

    def test_recursive_context_inheritance(self):
        """Context: Status must recursively collect ancestor annotations (A -> B -> C)."""
        # Create 3-level hierarchy: A -> B -> C
        self.run_cmd(f"{self.tw_flow} ini recursion_test 'Step A|r|today' 'Step B|i|today' 'Step C|t|today'")
        out_exp, _, _ = self.run_cmd(f"{self.taskp} project:recursion_test export")
        tasks = orjson.loads(out_exp)
        ua = tasks[0]["uuid"]
        ub = tasks[1]["uuid"]
        uc = tasks[2]["uuid"]

        # Annotate A (Grandparent) and B (Parent)
        self.run_cmd(f"{self.tw_flow} note {ua} decision 'Root logic'")
        self.run_cmd(f"{self.tw_flow} note {ub} outcome 'Intermediate valid'")

        # Focus on C (Child) and check status
        self.run_cmd(f"{self.tw_flow} focus task {uc}")
        out, _, _ = self.run_cmd(f"{self.tw_flow} status recursion_test")

        # Verify inherited context from both ancestors
        self.assertIn("══ INHERITED CONTEXT ══", out)
        self.assertIn("DECISION: Root logic", out)
        self.assertIn("OUTCOME: Intermediate valid", out)
        # Verify they are associated with the correct task UUIDs (short)
        self.assertIn(f"Task ({ua[:8]})", out)
        self.assertIn(f"Task ({ub[:8]})", out)

    def test_ticket_command_uda_persistence(self):
        """UDA Integration: Ticket command must persist the externalid attribute."""
        self.run_cmd(f"{self.tw_flow} ticket {self.u1} '#JAC-123'")
        out, _, _ = self.run_cmd(f"{self.taskp} {self.u1} export")
        task = orjson.loads(out or "[]")[0]
        self.assertEqual(task.get("externalid"), "#JAC-123")

    def test_prompt_marketing_alert_display(self):
        """Workflow Awareness: Status must display an alert when a ticket is detected."""
        self.run_cmd(f"{self.tw_flow} ticket {self.u1} '#TKT-789'")
        self.run_cmd(f"{self.tw_flow} focus task {self.u1}")
        out, _, _ = self.run_cmd(f"{self.tw_flow} status test_ini")
        
        # Strip ANSI escape codes and normalize whitespace for robust matching
        clean_out = re.sub(r'\x1b\[[0-9;]*[mK]', '', out)
        self.assertIn("ALERT: External ticket detected (#TKT-789)", clean_out)
        self.assertIn("Git-expert will use this for automated commit referencing", clean_out)

    def test_hierarchical_ticket_inheritance(self):
        """Workflow Awareness: Child tasks must inherit tickets from ancestors if not directly set."""
        # u2 depends on u1. Set ticket on u1 only.
        self.run_cmd(f"{self.tw_flow} ticket {self.u1} '#PARENT-123'")
        self.run_cmd(f"{self.tw_flow} focus task {self.u2}")
        out, _, _ = self.run_cmd(f"{self.tw_flow} status test_ini")

        clean_out = re.sub(r'\x1b\[[0-9;]*[mK]', '', out)
        self.assertIn("ALERT: Inherited ticket detected (#PARENT-123)", clean_out)

    def test_semantic_notes_inheritance(self):
        """Context: Question and Hypothesis notes must be recorded and inherited."""
        self.run_cmd(f"{self.tw_flow} note {self.u1} question 'Why X?'")
        self.run_cmd(f"{self.tw_flow} note {self.u1} hypothesis 'Maybe Y'")
        
        self.run_cmd(f"{self.tw_flow} focus task {self.u2}")
        out, _, _ = self.run_cmd(f"{self.tw_flow} status test_ini")
        
        self.assertIn("QUESTION: Why X?", out)
        self.assertIn("HYPOTHESIS: Maybe Y", out)

    def test_reopen_completed_task(self):
        """Workflow: Reopen must move a completed task back to pending."""
        self.run_cmd(f"{self.tw_flow} outcome {self.u1} 'Done'")
        self.run_cmd(f"{self.tw_flow} done {self.u1}")
        
        # Verify it's completed
        out, _, _ = self.run_cmd(f"{self.taskp} {self.u1} export")
        self.assertEqual(orjson.loads(out)[0]["status"], "completed")
        
        # Reopen
        self.run_cmd(f"{self.tw_flow} reopen {self.u1}")
        out, _, _ = self.run_cmd(f"{self.taskp} {self.u1} export")
        self.assertEqual(orjson.loads(out)[0]["status"], "pending")

    def test_amend_metadata_any_task(self):
        """Metadata: Amend must update description/ticket without status errors."""
        self.run_cmd(f"{self.tw_flow} outcome {self.u1} 'Done'")
        self.run_cmd(f"{self.tw_flow} done {self.u1}")
        
        # Amend description and ticket
        self.run_cmd(f"{self.tw_flow} amend {self.u1} description='Fixed Desc' ticket='#FIX-123'")
        
        out, _, _ = self.run_cmd(f"{self.taskp} {self.u1} export")
        task = orjson.loads(out)[0]
        self.assertEqual(task["description"], "Fixed Desc")
        self.assertEqual(task["externalid"], "#FIX-123")

    def test_completed_task_modification_blocks_with_instruction(self):
        """Safety: Modifying completed task with standard commands must fail with ACTION prompt."""
        self.run_cmd(f"{self.tw_flow} outcome {self.u1} 'Done'")
        self.run_cmd(f"{self.tw_flow} done {self.u1}")
        
        # Try note on completed task
        _, err, code = self.run_cmd(f"{self.tw_flow} note {self.u1} note 'Illegal'")
        self.assertNotEqual(code, 0)
        self.assertIn("ACTION: To fix metadata", err)
        self.assertIn("ACTION: To perform more work", err)

    def test_note_invalid_type_instructional_error(self):
        """Error as Prompt: Invalid note type must provide instructional feedback."""
        _, err, code = self.run_cmd(f"{self.tw_flow} note {self.u1} invalid 'Message'")
        self.assertNotEqual(code, 0)
        self.assertIn("ACTION: Use one of the allowed semantic types", err)
        self.assertIn("QUESTION", err)
        self.assertIn("HYPOTHESIS", err)
