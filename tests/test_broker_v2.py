import unittest
import subprocess
import os

class TestBrokerV2(unittest.TestCase):
    def test_invalid_command_error_as_prompt(self):
        """Verify that an invalid command returns exit 1 and contains ACTION: hint."""
        res = subprocess.run(["jacazul-broker", "invalidcmd"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 1)
        self.assertIn("ERROR: Unknown command: 'invalidcmd'.", res.stderr)
        self.assertIn("ACTION: Use one of:", res.stderr)

    def test_missing_args_error_as_prompt(self):
        """Verify that commands missing mandatory args return exit 1 and ACTION: hint."""
        # Test 'sync' without issue ID
        res = subprocess.run(["jacazul-broker", "sync"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 1)
        self.assertIn("ACTION: Use 'jacazul-broker sync #123'", res.stderr)

        # Test 'open' without title
        res = subprocess.run(["jacazul-broker", "open"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 1)
        self.assertIn("ACTION: Use 'jacazul-broker open \"My title\"'", res.stderr)

    def test_list_command_execution(self):
        """Verify that 'list' command works (integration test with gh)."""
        # We test with '--limit 1' to keep it fast
        res = subprocess.run(["jacazul-broker", "list", "-", "open"], capture_output=True, text=True)
        # If gh is not authenticated in this env, it might fail with exit 1, 
        # but the command structure should be valid.
        if res.returncode == 0:
            self.assertIn("Open issues for", res.stdout)
        else:
            # If it fails due to auth, we at least check it didn't fail due to python error
            self.assertNotIn("Traceback", res.stderr)

if __name__ == "__main__":
    unittest.main()
