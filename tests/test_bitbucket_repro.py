import unittest
import subprocess
import os
import json


class TestBitbucketDetection(unittest.TestCase):
    def setUp(self):
        self.project = "test-bitbucket-detection"
        os.environ["PROJECT_ID"] = self.project
        # Create a dummy task
        subprocess.run(
            ["tw-flow", "plan", self.project, "Test task"], capture_output=True
        )
        res = subprocess.run(
            ["taskp", "project:" + self.project, "export"],
            capture_output=True,
            text=True,
        )
        tasks = json.loads(res.stdout)
        self.uuid = tasks[0]["uuid"]

    def test_bitbucket_pattern_detected_now(self):
        """
        Verify that a Bitbucket-style ticket (PROJ-123) NOW triggers
        the validation protocol and calls the Bitbucket mock.
        """
        res = subprocess.run(
            ["tw-flow", "ticket", self.uuid, "BTBKR-123"],
            capture_output=True,
            text=True,
        )
        # Check for the Protocol alert
        self.assertIn(
            "The Protocol: Validating ticket BTBKR-123...", res.stdout
        )
        # Check for Bitbucket mock output
        self.assertIn(
            "🐊 [Bitbucket/Jira] Mock Syncing ticket BTBKR-123...", res.stdout
        )
        self.assertIn("linked to ticket: BTBKR-123", res.stdout)

    def test_github_still_works(self):
        """
        Verify that GitHub-style ticket (#123) still triggers the Protocol.
        """
        res = subprocess.run(
            ["tw-flow", "ticket", self.uuid, "#456"],
            capture_output=True,
            text=True,
        )
        self.assertIn("The Protocol: Validating ticket #456...", res.stdout)
        self.assertIn("Syncing issue #456", res.stdout)


if __name__ == "__main__":
    unittest.main()
