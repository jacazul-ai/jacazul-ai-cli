import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import orjson

from jacazul.cli.flow import FlowManager
from jacazul.taskwarrior.core import FocusManager, FocusState
from tests.base import JacazulTest


class FakeTaskWrapper:
    def __init__(self, statuses):
        self.statuses = statuses

    def export(self, filters):
        uuid = filters[0]
        status = self.statuses.get(uuid)
        return [{"uuid": uuid, "status": status}] if status else []


class FocusAdvanceTest(unittest.TestCase):
    """Verify that completion cannot cross plan boundaries."""

    def test_advance_ignores_pending_task_from_another_plan(self):
        with tempfile.TemporaryDirectory(prefix="focus-test-") as path:
            with patch.dict(os.environ, {"TASKDATA": path}, clear=False):
                manager = FocusManager()
                manager.save(
                    FocusState(
                        focused_plan="plan-a",
                        focused_task_uuid="task-a",
                        task_track=[
                            {"uuid": "task-a", "plan": "plan-a"},
                            {"uuid": "task-b", "plan": "plan-b"},
                        ],
                        plans_of_interest=[],
                    )
                )

                result = manager.advance(
                    "task-a",
                    FakeTaskWrapper(
                        {"task-a": "completed", "task-b": "pending"}
                    ),
                )

                self.assertIsNone(result)
                state = manager.load()
                self.assertIsNone(state.focused_task_uuid)
                self.assertIsNone(state.focused_plan)

    def test_advance_selects_pending_task_from_same_plan(self):
        with tempfile.TemporaryDirectory(prefix="focus-test-") as path:
            with patch.dict(os.environ, {"TASKDATA": path}, clear=False):
                manager = FocusManager()
                manager.save(
                    FocusState(
                        focused_plan="plan-a",
                        focused_task_uuid="task-a",
                        task_track=[
                            {"uuid": "task-a", "plan": "plan-a"},
                            {"uuid": "task-b", "plan": "plan-a"},
                            {"uuid": "task-c", "plan": "plan-b"},
                        ],
                        plans_of_interest=[],
                    )
                )

                result = manager.advance(
                    "task-a",
                    FakeTaskWrapper(
                        {
                            "task-a": "completed",
                            "task-b": "pending",
                            "task-c": "pending",
                        }
                    ),
                )

                self.assertEqual(result["uuid"], "task-b")
                state = manager.load()
                self.assertEqual(state.focused_task_uuid, "task-b")
                self.assertEqual(state.focused_plan, "plan-a")


class ExecuteProtocolContractTest(unittest.TestCase):
    """Verify that the source protocol defines proactive EXECUTE behavior."""

    def test_execute_authority_is_unambiguous(self):
        source = (
            Path(__file__).resolve().parents[1]
            / "jacazul"
            / "hatch"
            / "templates"
            / "protocols"
            / "environment_modes.md"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "active, anchored task with `[EXECUTE]` or `[REFINE]`",
            source,
        )
        self.assertIn(
            "Commits and pushes keep their separate gates.",
            source,
        )

    def test_workflow_loop_requires_docs_and_reanchors(self):
        source = (
            Path(__file__).resolve().parents[1]
            / "jacazul"
            / "hatch"
            / "templates"
            / "core"
            / "workflow_loop.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Documentation Gate", source)
        self.assertIn("re-anchor", source)
        self.assertIn("same plan", source)


class CommitFooterTypeTest(unittest.TestCase):
    """Verify deterministic Refs versus Fixes selection."""

    def test_pending_ticket_tasks_require_refs(self):
        manager = object.__new__(FlowManager)
        manager.tw = Mock()
        manager.tw.export.return_value = [
            {"uuid": "task-a", "externalid": "#98", "status": "pending"},
            {"uuid": "task-b", "externalid": "#97", "status": "pending"},
        ]

        self.assertEqual(manager.commit_footer_type("#98"), "Refs")

    def test_no_pending_ticket_tasks_use_fixes(self):
        manager = object.__new__(FlowManager)
        manager.tw = Mock()
        manager.tw.export.return_value = [
            {"uuid": "task-a", "externalid": "#98", "status": "completed"},
            {"uuid": "task-b", "externalid": "#97", "status": "pending"},
        ]

        self.assertEqual(manager.commit_footer_type("#98"), "Fixes")


class CacheInvalidationTest(JacazulTest):
    """Verify that task mutations invalidate filtered status output."""

    def test_amend_invalidates_plan_status_cache(self):
        self.run_cmd(
            f"{self.tw_flow} plan cache-control "
            "'Original task|implementation'"
        )
        exported, _, _ = self.run_cmd(
            f"{self.taskp} project:cache-control export"
        )
        uuid = orjson.loads(exported)[0]["uuid"]

        first_status, _, _ = self.run_cmd(
            f"{self.tw_flow} status cache-control"
        )
        self.assertIn("Original task", first_status)

        self.run_cmd(
            f'{self.tw_flow} amend {uuid} description="Updated task"'
        )
        second_status, _, _ = self.run_cmd(
            f"{self.tw_flow} status cache-control"
        )

        self.assertNotIn("[cached]", second_status)
        self.assertIn("Updated task", second_status)


if __name__ == "__main__":
    unittest.main()
