#!/home/fpiraz/.jacazul-ai/.venv/bin/python
import re
import orjson
import os
from .base import JacazulTest


class FlowTest(JacazulTest):
    """Atomic tests for the 7-phase Taskwarrior workflow."""

    def setUp(self):
        super().setUp()
        self.run_cmd(
            f"{self.tw_flow} ini test_ini "
            "'Step 1|research|today' 'Step 2|implementation|tomorrow'"
        )
        out, _, _ = self.run_cmd(f"{self.taskp} project:test_ini export")
        tasks = orjson.loads(out or "[]")
        if not tasks:
            print(f"DEBUG: Setup failed. Output: {out}")
        self.u1 = tasks[0]["uuid"]
        self.u2 = tasks[1]["uuid"]

    def test_initiative_creation_emits_short_uuid(self):
        """Standardization: Initiative creation must output 8-char UUIDs."""
        out, _, _ = self.run_cmd(f"{self.tw_flow} ini new_ini 'Task|r|today'")
        self.assertTrue(
            re.search(r"Created task [0-9a-f]{8}:", out),
            "Output missing short UUID",
        )

    def test_initiatives_list_display(self):
        """Initiatives command must list projects with pending tasks."""
        out, _, _ = self.run_cmd(f"{self.tw_flow} inis")
        self.assertIn("test_ini [ACTIVE]", out)

    def test_initiatives_filtering_all_and_closed(self):
        """Integration: 'tw-flow inis' must support --all and --closed."""
        # 1. Setup: one active ini and one completed ini
        self.run_cmd(f"{self.tw_flow} ini ini_active 'Task 1|r|today'")
        self.run_cmd(f"{self.tw_flow} ini ini_closed 'Task 2|r|today'")

        out_exp, _, _ = self.run_cmd(f"{self.taskp} project:ini_closed export")
        uuid = orjson.loads(out_exp)[0]["uuid"]
        self.run_cmd(f"{self.tw_flow} outcome {uuid} 'Done'")
        self.run_cmd(f"{self.tw_flow} done {uuid}")

        # 2. Test default (only active)
        out, _, _ = self.run_cmd(f"{self.tw_flow} inis")
        self.assertIn("ini_active [ACTIVE]", out)
        self.assertNotIn("ini_closed", out)

        # 3. Test --closed only
        out_closed, _, _ = self.run_cmd(f"{self.tw_flow} inis --closed")
        self.assertIn("ini_closed [ZEROED]", out_closed)
        self.assertNotIn("ini_active", out_closed)

        # 4. Test --all
        out_all, _, _ = self.run_cmd(f"{self.tw_flow} inis --all")
        self.assertIn("ini_active [ACTIVE]", out_all)
        self.assertIn("ini_closed [ZEROED]", out_all)

    def test_status_split_view_content(self):
        """Status command must show PENDING and COMPLETED tasks."""
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
        self.assertIn("Step 2", out)

    def test_status_shows_ticket_in_line(self):
        """Status: Task lines must include direct or inherited tickets."""
        self.run_cmd(f"{self.tw_flow} ticket {self.u1} '#TKT-123'")
        out, _, _ = self.run_cmd(f"{self.tw_flow} status test_ini")
        self.assertIn("[#TKT-123] Step 1", out)
        # u2 inherits from u1
        self.assertIn("[#TKT-123] Step 2", out)

    def test_tw_flow_ponder_subcommand(self):
        """Integration: 'tw-flow ponder' must render the dashboard."""
        out, _, _ = self.run_cmd(f"{self.tw_flow} ponder")
        self.assertIn("[TASK LANDSCAPE]", out)
        self.assertIn("[TACTICAL READOUT]", out)

    def test_cool_down_protocol_and_hyphen_fix(self):
        """Standardization: 'tw-flow plan' must not add default due/priority and must support hyphens (Fix #37)."""
        # 1. Test hyphenated plan name (Fix #37)
        plan_name = "cool-down-test"
        out, _, _ = self.run_cmd(f"{self.tw_flow} plan {plan_name} 'DESIGN|Cool task|design'")
        self.assertIn(f"Creating plan: {plan_name}", out)
        self.assertIn("Created task", out)

        # 2. Verify Cool Down protocol (no default due, priority:M)
        out_exp, _, _ = self.run_cmd(f"{self.taskp} project:{plan_name} export")
        tasks = orjson.loads(out_exp)
        self.assertEqual(len(tasks), 1)
        task = tasks[0]
        self.assertNotIn("due", task, "Task should not have a default due date")
        self.assertEqual(task.get("priority"), "M", "Task should have priority:M by default")

        # 3. Verify tree and status also work with hyphenated names
        out_status, _, _ = self.run_cmd(f"{self.tw_flow} status {plan_name}")
        self.assertIn(f"Plan: {plan_name}", out_status)
        self.assertIn("Cool task", out_status)

        out_tree, _, _ = self.run_cmd(f"{self.tw_flow} tree {plan_name}")
        self.assertIn(f"Plan: {plan_name}", out_tree)
        self.assertIn("Cool task", out_tree)

    def test_tw_flow_commit_draft_generation(self):
        """Standardization: 'tw-flow commit' must generate a draft."""
        self.run_cmd(f"{self.tw_flow} ticket {self.u1} '#JAC-789'")
        self.run_cmd(f"{self.tw_flow} focus task {self.u1}")
        out, _, _ = self.run_cmd(f"{self.tw_flow} commit")
        self.assertIn("══ DRAFT CONVENTIONAL COMMIT ══", out)
        self.assertIn("Refs: #JAC-789", out)

        # Test fix flag
        out, _, _ = self.run_cmd(f"{self.tw_flow} commit --fix")
        self.assertIn("Fixes: #JAC-789", out)

    def test_next_task_readiness_logic(self):
        """Next command must correctly identify the first unblocked task."""
        out, _, _ = self.run_cmd(f"{self.tw_flow} next test_ini")
        self.assertIn("Step 1", out)

    def test_execute_marks_task_active(self):
        """Execution logic: Task must be marked ACTIVE in the database."""
        self.run_cmd(f"{self.tw_flow} execute {self.u1}")
        out, _, _ = self.run_cmd(f"{self.taskp} +ACTIVE export")
        tasks = orjson.loads(out or "[]")
        self.assertTrue(any(t.get("uuid") == self.u1 for t in tasks))

    def test_note_prefix_persistence(self):
        """Context: Structured notes must persist with correct prefixes."""
        self.run_cmd(f"{self.tw_flow} note {self.u1} decision 'Fixed'")
        out, _, _ = self.run_cmd(f"{self.taskp} {self.u1} export")
        annots = [
            a["description"]
            for a in orjson.loads(out or "[]")[0].get("annotations", [])
        ]
        self.assertIn("DECISION: Fixed", annots)

    def test_context_command_retrieval(self):
        """Context retrieval: Context command must display annotations."""
        self.run_cmd(f"{self.tw_flow} note {self.u1} research 'Deep'")
        out, _, _ = self.run_cmd(f"{self.tw_flow} context {self.u1}")
        self.assertIn("RESEARCH: Deep", out)

    def test_active_filter_output(self):
        """Filters: Active filter must only show tasks in ACTIVE state."""
        self.run_cmd(f"{self.tw_flow} execute {self.u1}")
        out, _, _ = self.run_cmd(f"{self.tw_flow} active")
        self.assertIn("Step 1", out)

    def test_initiative_prepends_mode_prefix(self):
        """Interaction modes: Initiative must correctly prepend [MODE]."""
        out, _, _ = self.run_cmd(
            f"{self.tw_flow} ini mtest 'SPIKE|Arch|r|today'"
        )
        self.assertIn("[SPIKE] Arch", out)

    def test_ponder_dashboard_mode_highlighting(self):
        """Ponder: Tactical dashboard must highlight interaction modes."""
        self.run_cmd(f"{self.tw_flow} ini mtest 'GUIDE|Docs|r|today'")
        out, _, _ = self.run_cmd(f"{self.ponder}")
        self.assertIn("GUIDE", out)

    def test_handoff_protocol_execution(self):
        """Handoff: Protocol must add note AND execute the next task."""
        self.run_cmd(f"{self.tw_flow} outcome {self.u1} 'Finished'")
        self.run_cmd(f"{self.tw_flow} done {self.u1}")
        self.run_cmd(f"{self.tw_flow} handoff {self.u2} 'Start S2'")
        out, _, _ = self.run_cmd(f"{self.taskp} {self.u2} export")
        task = orjson.loads(out or "[]")[0]
        self.assertTrue(
            any(
                "HANDOFF: Start S2" in a["description"]
                for a in task.get("annotations", [])
            )
        )
        self.assertTrue(task.get("start"), "Next task not auto-executed")

    def test_done_enforces_outcome_annotation(self):
        """Safety: Done command must fail if OUTCOME is missing."""
        out, err, code = self.run_cmd(f"{self.tw_flow} done {self.u1}")
        self.assertNotEqual(code, 0)
        self.assertIn("cannot be completed without an OUTCOME", out + err)

    def test_done_success_with_outcome(self):
        """Happy path: Done command succeeds when OUTCOME is present."""
        self.run_cmd(f"{self.tw_flow} outcome {self.u1} 'Verified'")
        _, _, code = self.run_cmd(f"{self.tw_flow} done {self.u1}")
        self.assertEqual(code, 0)

    def test_focus_heap_accumulation(self):
        """Anchor System: Focus stack must accumulate anchored tasks."""
        self.run_cmd(f"{self.tw_flow} focus ini test_ini")
        self.run_cmd(f"{self.tw_flow} ini other_ini 'Task|r|today'")
        self.run_cmd(f"{self.tw_flow} focus ini other_ini")

        focus_file = os.path.join(self.taskdata, "focus.json")
        with open(focus_file, "rb") as f:
            state = orjson.loads(f.read())
            self.assertGreaterEqual(len(state.get("task_track", [])), 2)

    def test_ponder_interest_filtering_logic(self):
        """Dashboard: Ponder must filter projects by interest."""
        self.run_cmd(f"{self.tw_flow} ini boring 'Hidden|r|today'")
        self.run_cmd(f"{self.tw_flow} focus interest add test_ini")

        out, _, _ = self.run_cmd(f"{self.ponder}")
        self.assertIn("test_ini", out)
        self.assertNotIn("boring", out)

        out_all, _, _ = self.run_cmd(f"{self.ponder} --all")
        self.assertIn("boring", out_all)

    def test_recursive_context_inheritance(self):
        """Context: Status must recursively collect annotations."""
        # Create 3-level hierarchy: A -> B -> C
        self.run_cmd(
            f"{self.tw_flow} ini rtest"
            " 'Step A|research|today'"
            " 'Step B|implementation|today'"
            " 'Step C|testing|today'"
        )
        out_exp, _, _ = self.run_cmd(f"{self.taskp} project:rtest export")
        tasks = orjson.loads(out_exp)
        ua = tasks[0]["uuid"]
        ub = tasks[1]["uuid"]
        uc = tasks[2]["uuid"]

        # Annotate A (Grandparent) and B (Parent)
        self.run_cmd(f"{self.tw_flow} note {ua} decision 'Root'")
        self.run_cmd(f"{self.tw_flow} note {ub} outcome 'Intermediate'")

        # Focus on C (Child) and check status
        self.run_cmd(f"{self.tw_flow} focus task {uc}")
        out, _, _ = self.run_cmd(f"{self.tw_flow} status rtest")

        # Verify inherited context
        self.assertIn("══ INHERITED CONTEXT ══", out)
        self.assertIn("DECISION: Root", out)
        self.assertIn("OUTCOME: Intermediate", out)

    def test_ticket_command_uda_persistence(self):
        """UDA Integration: Ticket command must persist externalid."""
        self.run_cmd(f"{self.tw_flow} ticket {self.u1} '#JAC-123'")
        out, _, _ = self.run_cmd(f"{self.taskp} {self.u1} export")
        task = orjson.loads(out or "[]")[0]
        self.assertEqual(task.get("externalid"), "#JAC-123")

    def test_prompt_marketing_alert_display(self):
        """Awareness: Status must display an alert when ticket is found."""
        self.run_cmd(f"{self.tw_flow} ticket {self.u1} '#TKT-789'")
        self.run_cmd(f"{self.tw_flow} focus task {self.u1}")
        out, _, _ = self.run_cmd(f"{self.tw_flow} status test_ini")
        # Strip ANSI escape codes
        clean_out = re.sub(r"\x1b\[[0-9;]*[mK]", "", out)
        self.assertIn("ALERT: External ticket detected (#TKT-789)", clean_out)

    def test_smart_focus_anchoring(self):
        """Smart Focus: 'tw-flow focus <ini>' must anchor without 'ini'."""
        # Create a new test initiative
        self.run_cmd(f"{self.tw_flow} ini smart_ini 'Goal|r|today'")

        # 1. Test smart focus (without 'ini' keyword)
        out, _, _ = self.run_cmd(f"{self.tw_flow} focus smart_ini")
        self.assertIn("Smart-focused anchored to: smart_ini", out)

        # 2. Verify anchoring in focus.json
        focus_file = os.path.join(self.taskdata, "focus.json")
        with open(focus_file, "rb") as f:
            state = orjson.loads(f.read())
            self.assertEqual(state.get("focused_plan"), "smart_ini")

        # 3. Test invalid focus target returns error
        out_err, err, code = self.run_cmd(
            f"{self.tw_flow} focus non_existent_ini"
        )
        self.assertNotEqual(code, 0)
        self.assertIn("Unknown focus subcommand", out_err + err)

    def test_independent_focus_creates_session_file(self):
        """Independent Focus: focus ind task must create session file."""
        session_id = "testsession"
        session_env = {"JACAZUL_SESSION_ID": session_id}
        out, _, code = self.run_cmd(
            f"{self.tw_flow} focus ind task {self.u1}", env=session_env
        )
        self.assertEqual(code, 0)
        session_file = os.path.join(self.taskdata, f"focus-{session_id}.json")
        self.assertTrue(os.path.exists(session_file))
        with open(session_file, "rb") as f:
            data = orjson.loads(f.read())
        self.assertEqual(data.get("focused_plan"), "test_ini")
        self.assertIn(self.u1[:8], data.get("focused_task_uuid", ""))

    def test_independent_focus_plan(self):
        """Independent Focus: ind plan anchors to plan in session file."""
        session_id = "testsession"
        session_env = {"JACAZUL_SESSION_ID": session_id}
        out, _, code = self.run_cmd(
            f"{self.tw_flow} focus ind plan test_ini", env=session_env
        )
        self.assertEqual(code, 0)
        self.assertIn("Independent focus anchored to plan: test_ini", out)
        session_file = os.path.join(self.taskdata, f"focus-{session_id}.json")
        self.assertTrue(os.path.exists(session_file))
        with open(session_file, "rb") as f:
            data = orjson.loads(f.read())
        self.assertEqual(data.get("focused_plan"), "test_ini")

    def test_independent_focus_back(self):
        """Independent Focus: focus back deletes session file."""
        session_id = "testsession"
        session_env = {"JACAZUL_SESSION_ID": session_id}
        # First create session
        self.run_cmd(f"{self.tw_flow} focus ind plan test_ini", env=session_env)
        session_file = os.path.join(self.taskdata, f"focus-{session_id}.json")
        self.assertTrue(os.path.exists(session_file))
        # Then exit
        out, _, code = self.run_cmd(f"{self.tw_flow} focus back", env=session_env)
        self.assertEqual(code, 0)
        self.assertIn("Switched back to global focus", out)
        self.assertFalse(os.path.exists(session_file))

    def test_focus_back_falls_back_to_global_focus(self):
        """Independent Focus: after focus back, SESSION_ID set but file deleted falls back to global."""
        session_id = "testsession2"
        session_env = {"JACAZUL_SESSION_ID": session_id}
        # Set a plan in global focus first
        self.run_cmd(f"{self.tw_flow} focus plan test_ini")
        # Create independent session and focus on different plan
        self.run_cmd(f"{self.tw_flow} focus ind plan test_ini", env=session_env)
        # Exit independent session (deletes session file)
        self.run_cmd(f"{self.tw_flow} focus back", env=session_env)
        # With SESSION_ID still set but file deleted, focus must read global focus.json
        out, _, code = self.run_cmd(f"{self.tw_flow} focus", env=session_env)
        self.assertEqual(code, 0)
        self.assertIn("test_ini", out)

    def test_vaccinated_done_enforces_python_quality(self):
        """Quality Gate: 'tw-flow done' must block if Python files fail."""
        # 1. Create a task and add outcome
        self.run_cmd(
            f"{self.tw_flow} ini quality_test 'Check Quality|r|today'"
        )
        out_exp, _, _ = self.run_cmd(
            f"{self.taskp} project:quality_test export"
        )
        uuid = orjson.loads(out_exp)[0]["uuid"]
        self.run_cmd(f"{self.tw_flow} outcome {uuid} 'Testing blocking'")

        # 2. Introduce a syntax error in a .py file
        dirty_file = os.path.join(self.project_root, "dirty_test.py")
        with open(dirty_file, "w") as f:
            f.write("def broken_syntax(:\n    pass\n")

        # 2.1 Force git to see the file
        self.run_cmd(f"git add {dirty_file}")

        try:
            # 3. Attempt 'done' - should be blocked
            out, err, code = self.run_cmd(
                f"JACAZUL_TESTING=false {self.tw_flow} done {uuid}"
            )
            self.assertNotEqual(code, 0, "Blocked")
            self.assertIn("Python validation failed", out + err)

            # 4. Verify task status is still pending
            out_check, _, _ = self.run_cmd(f"{self.taskp} {uuid} export")
            self.assertEqual(orjson.loads(out_check)[0]["status"], "pending")
        finally:
            self.run_cmd(f"git restore --staged {dirty_file}")
            if os.path.exists(dirty_file):
                os.remove(dirty_file)

    def test_initiative_rename_synchronization(self):
        """Standardization: 'tw-flow rename' must sync TW and Focus."""
        # 1. Setup an initiative, interest it, and focus it
        self.run_cmd(f"{self.tw_flow} ini old_ini 'Task|r|today'")
        self.run_cmd(f"{self.tw_flow} focus interest add old_ini")
        self.run_cmd(f"{self.tw_flow} focus old_ini")

        # 2. Rename it
        self.run_cmd(f"{self.tw_flow} rename old_ini new_ini")

        # 3. Verify Taskwarrior update
        out_tasks, _, _ = self.run_cmd(f"{self.taskp} project:new_ini export")
        self.assertEqual(len(orjson.loads(out_tasks)), 1)

        # 4. Verify Focus update
        focus_file = os.path.join(self.taskdata, "focus.json")
        with open(focus_file, "rb") as f:
            state = orjson.loads(f.read())
            self.assertEqual(state.get("focused_plan"), "new_ini")

    def test_ponder_session_context_display(self):
        """Ponder: Must display Interests and Task Track from focus.json."""
        # 1. Create and execute tasks
        self.run_cmd(f"{self.tw_flow} ini ini_a 'Task A|r|today'")
        self.run_cmd(f"{self.tw_flow} ini ini_b 'Task B|r|today'")
        out_a, _, _ = self.run_cmd(f"{self.taskp} project:ini_a export")
        out_b, _, _ = self.run_cmd(f"{self.taskp} project:ini_b export")
        u_a = orjson.loads(out_a)[0]["uuid"]
        u_b = orjson.loads(out_b)[0]["uuid"]

        self.run_cmd(f"{self.tw_flow} execute {u_a}")
        self.run_cmd(f"{self.tw_flow} execute {u_b}")
        self.run_cmd(f"{self.tw_flow} focus interest add ini_a")
        self.run_cmd(f"{self.tw_flow} focus interest add ini_b")
        self.run_cmd(f"{self.tw_flow} focus ini ini_b")

        # 2. Run ponder and check display
        out, _, _ = self.run_cmd(f"{self.ponder}")

        self.assertIn("[SESSION CONTEXT]", out)
        self.assertIn("ini_a, ini_b", out)
        self.assertIn("Track:", out)
        self.assertIn("Focus: ini_b", out)
        self.assertIn("[PULSE SUMMARY]", out)

    def test_hierarchical_ticket_inheritance(self):
        """Awareness: Child tasks must inherit tickets from ancestors."""
        # u2 depends on u1. Set ticket on u1 only.
        self.run_cmd(f"{self.tw_flow} ticket {self.u1} '#PARENT-123'")
        self.run_cmd(f"{self.tw_flow} focus task {self.u2}")
        out, _, _ = self.run_cmd(f"{self.tw_flow} status test_ini")

        clean_out = re.sub(r"\x1b\[[0-9;]*[mK]", "", out)
        self.assertIn(
            "ALERT: Inherited ticket detected (#PARENT-123)", clean_out
        )

    def test_semantic_notes_inheritance(self):
        """Context: Question and Hypothesis notes must be inherited."""
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

        # Verify completion
        out, _, _ = self.run_cmd(f"{self.taskp} {self.u1} export")
        self.assertEqual(orjson.loads(out)[0]["status"], "completed")

        # Reopen
        self.run_cmd(f"{self.tw_flow} reopen {self.u1}")
        out, _, _ = self.run_cmd(f"{self.taskp} {self.u1} export")
        self.assertEqual(orjson.loads(out)[0]["status"], "pending")

    def test_amend_metadata_any_task(self):
        """Metadata: Amend must update description/ticket."""
        self.run_cmd(f"{self.tw_flow} outcome {self.u1} 'Done'")
        self.run_cmd(f"{self.tw_flow} done {self.u1}")

        # Amend
        self.run_cmd(
            f"{self.tw_flow} amend {self.u1} description='Fix' ticket='#F1'"
        )

        out, _, _ = self.run_cmd(f"{self.taskp} {self.u1} export")
        task = orjson.loads(out)[0]
        self.assertEqual(task["description"], "Fix")
        self.assertEqual(task["externalid"], "#F1")

    def test_notes_lists_annotations(self):
        """Notes: tw-flow notes must list annotations with timestamps."""
        self.run_cmd(f"{self.tw_flow} note {self.u1} decision 'Test decision'")
        out, _, code = self.run_cmd(f"{self.tw_flow} notes {self.u1}")
        self.assertEqual(code, 0)
        self.assertIn("DECISION: Test decision", out)

    def test_note_delete_removes_annotation(self):
        """Notes: tw-flow note delete must remove specific annotation."""
        self.run_cmd(f"{self.tw_flow} note {self.u1} decision 'To be deleted'")
        # Get timestamp
        out, _, _ = self.run_cmd(f"{self.taskp} {self.u1[:8]} export")
        task = orjson.loads(out)[0]
        timestamp = task["annotations"][-1]["entry"]
        # Delete
        _, _, code = self.run_cmd(
            f"{self.tw_flow} note {self.u1} delete {timestamp}"
        )
        self.assertEqual(code, 0)
        # Verify gone
        out2, _, _ = self.run_cmd(f"{self.tw_flow} notes {self.u1}")
        self.assertNotIn("To be deleted", out2)

    def test_completed_task_modification_blocks(self):
        """Safety: execute on completed task fails; note is allowed."""
        self.run_cmd(f"{self.tw_flow} outcome {self.u1} 'Done'")
        self.run_cmd(f"{self.tw_flow} done {self.u1}")

        # note on completed task is allowed (annotations are always valid)
        _, _, code = self.run_cmd(
            f"{self.tw_flow} note {self.u1} note 'Post-completion note'"
        )
        self.assertEqual(code, 0)

        # execute on completed task must still fail
        _, err, code = self.run_cmd(f"{self.tw_flow} execute {self.u1}")
        self.assertNotEqual(code, 0)
        self.assertIn("ACTION: To fix metadata", err)

    def test_note_and_delete_on_completed_task(self):
        """Notes: add and delete annotations on completed tasks must work."""
        self.run_cmd(f"{self.tw_flow} outcome {self.u1} 'Done'")
        self.run_cmd(f"{self.tw_flow} done {self.u1}")

        # Add note to completed task
        _, _, code = self.run_cmd(
            f"{self.tw_flow} note {self.u1} note 'Post-completion note'"
        )
        self.assertEqual(code, 0)

        # Get timestamp of the annotation just added
        out, _, _ = self.run_cmd(f"taskp export status:completed {self.u1}")
        task = orjson.loads(out)[0]
        timestamp = task["annotations"][-1]["entry"]

        # Delete annotation from completed task
        _, _, code = self.run_cmd(
            f"{self.tw_flow} note {self.u1} delete {timestamp}"
        )
        self.assertEqual(code, 0)

        # Verify gone
        out2, _, _ = self.run_cmd(f"{self.tw_flow} notes {self.u1}")
        self.assertNotIn("Post-completion note", out2)

    def test_note_invalid_type_instructional_error(self):
        """Error as Prompt: Invalid note type must provide feedback."""
        _, err, code = self.run_cmd(
            f"{self.tw_flow} note {self.u1} invalid 'Msg'"
        )
        self.assertNotEqual(code, 0)
        self.assertIn("ACTION: Use one of the allowed semantic types", err)
