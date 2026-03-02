#!/home/fpiraz/.jacazul-ai/.venv/bin/python
from .base import JacazulTest

class CoreTest(JacazulTest):
    """Atomic tests for core environment and isolation."""

    def test_tools_executable(self):
        """Ensure taskp, tw-flow, and ponder are executable binaries."""
        for tool in [self.taskp, self.tw_flow, self.ponder]:
            self.assertTrue(os.access(tool, os.X_OK), f"Tool {tool} is not executable")

    def test_tw_flow_help_usage(self):
        """Ensure tw-flow help returns valid usage documentation."""
        out, _, code = self.run_cmd(f"{self.tw_flow} help")
        self.assertEqual(code, 0)
        self.assertIn("tw-flow USAGE:", out)

    def test_taskdata_isolation(self):
        """Verify strict TASKDATA isolation: project Alpha cannot see project Beta."""
        # Setup Project Alpha
        self.env["PROJECT_ID"] = "alpha"
        self.env["TASKDATA"] = os.path.join(self.test_dir, "alpha_data")
        self.run_cmd(f"{self.taskp} add 'Alpha Task'")
        
        # Setup Project Beta
        self.env["PROJECT_ID"] = "beta"
        self.env["TASKDATA"] = os.path.join(self.test_dir, "beta_data")
        self.run_cmd(f"{self.taskp} add 'Beta Task'")
        
        # Cross-check Alpha
        self.env["PROJECT_ID"] = "alpha"
        self.env["TASKDATA"] = os.path.join(self.test_dir, "alpha_data")
        out, _, _ = self.run_cmd(f"{self.taskp} list")
        self.assertIn("Alpha Task", out)
        self.assertNotIn("Beta Task", out, "Isolation breach: foreign task leaked!")
