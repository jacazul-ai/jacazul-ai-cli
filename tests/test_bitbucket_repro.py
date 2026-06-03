import unittest
import json
from .base import JacazulTest


class TestBitbucketDetection(JacazulTest):
    def setUp(self):
        super().setUp()
        self.project = "test-bitbucket-detection"
        # Create a dummy task
        self.run_cmd(
            f"{self.tw_flow} plan {self.project} 'Test task'"
        )
        out, _, _ = self.run_cmd(
            f"{self.taskp} project:{self.project} export"
        )
        tasks = json.loads(out)
        self.uuid = tasks[0]["uuid"]

    def test_bitbucket_pattern_detected_now(self):
        """
        Verify that a Bitbucket-style ticket (PROJ-123) NOW triggers
        the validation protocol and calls the Bitbucket mock.
        """
        out, _, _ = self.run_cmd(
            f"{self.tw_flow} ticket {self.uuid} BTBKR-123"
        )
        # Check for the Protocol alert
        self.assertIn(
            "The Protocol: Validating ticket BTBKR-123...", out
        )
        # Check for Bitbucket mock output
        self.assertIn(
            "🐊 [Bitbucket/Jira] Mock Syncing ticket BTBKR-123...", out
        )
        self.assertIn("linked to ticket: BTBKR-123", out)

    def test_github_still_works(self):
        """
        Verify that GitHub-style ticket (#123) still triggers the Protocol.
        """
        out, _, _ = self.run_cmd(
            f"{self.tw_flow} ticket {self.uuid} #456"
        )
        self.assertIn("The Protocol: Validating ticket #456...", out)
        self.assertIn("Syncing issue #456", out)


if __name__ == "__main__":
    unittest.main()
