import os
import re
from .base import JakaTest

class SecurityTest(JakaTest):
    """Atomic tests for vaccination, obfuscation, and environment safety."""

    def test_task_description_quote_handling(self):
        """Edge Case: Ensure descriptions handle single and double quotes correctly."""
        desc = "Task with 'single' and \"double\" quotes"
        escaped_desc = desc.replace('"', '\\"')
        out, _, code = self.run_cmd(f'{self.taskp} add "{escaped_desc}"')
        self.assertEqual(code, 0)
        out, _, _ = self.run_cmd(f"{self.taskp} list")
        self.assertIn("double", out)

    def test_ponder_excludes_archive_projects(self):
        """Standardization: Ponder must not show projects ending in _archive."""
        self.run_cmd(f"{self.taskp} add project:p:_archive 'Archived Task'")
        out, _, _ = self.run_cmd(f"{self.ponder} p")
        self.assertNotIn("Archived Task", out)

    def test_taskp_blocks_direct_done_command(self):
        """Vaccination: taskp MUST block the direct 'done' command to enforce tw-flow."""
        self.run_cmd(f"{self.taskp} add 'Sec task'")
        out, err, code = self.run_cmd(f"{self.taskp} 1 done")
        self.assertNotEqual(code, 0)
        self.assertIn("ERROR: Direct 'done' command via taskp is restricted", out + err)

    def test_taskp_blocks_manual_discard_tag(self):
        """Vaccination: taskp MUST block manual addition of +DISCARDED tag."""
        self.run_cmd(f"{self.taskp} add 'Sec task'")
        out, err, code = self.run_cmd(f"{self.taskp} 1 modify +DISCARDED")
        self.assertNotEqual(code, 0)
        self.assertIn("ERROR: Manual '+DISCARDED' tag via taskp is restricted", out + err)

    def test_discard_creates_automatic_outcome_audit(self):
        """Auditing: tw-flow discard must automatically document the task closure."""
        out, _, _ = self.run_cmd(f"{self.tw_flow} ini disc 'Discard me|r|today'")
        uuid = re.search(r'Created task ([0-9a-f]{8}):', out).group(1)
        self.run_cmd(f"{self.tw_flow} discard {uuid}")
        out, _, _ = self.run_cmd(f"{self.tw_flow} context {uuid}")
        normalized_out = " ".join(out.split())
        self.assertIn("OUTCOME: Task discarded and moved to archive", normalized_out)

    def test_raw_task_binary_restricted_via_wrapper(self):
        """Obfuscation: The 'task' wrapper must prevent raw binary usage."""
        scripts_dir = os.path.join(self.project_root, "scripts")
        self.env["PATH"] = f"{scripts_dir}:{self.env['PATH']}"
        out, err, code = self.run_cmd("task")
        self.assertNotEqual(code, 0)
        self.assertIn("ERROR: Direct usage of 'task' is restricted", out + err)
