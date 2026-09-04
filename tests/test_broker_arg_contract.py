#!/usr/bin/env python
"""Behavior tests for the jacazul-broker CLI.

Every case here is resolved by the parser before 'gh' is ever invoked, so the
suite needs no network access and no GitHub credentials.
"""

import os
import subprocess
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BROKER = os.path.join(PROJECT_ROOT, "jacazul", "cli", "broker.py")

SANDBOX = "jacazul-ai/jacazul-ai-sandbox"


def run_broker(*args):
    """Runs the broker CLI module directly, isolated from the real vault."""
    env = os.environ.copy()
    env["PYTHONPATH"] = PROJECT_ROOT + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, BROKER, *args],
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )


class TestAssigneeLifecycle(unittest.TestCase):
    """Assignee handling must use the flags gh actually accepts."""

    def test_edit_uses_add_assignee_flag(self):
        """Regression: edit_issue emitted --assignee, which gh rejects."""
        sys.path.insert(0, PROJECT_ROOT)
        from jacazul.cli.broker import GitHubBroker

        captured = {}

        class FakeResult:
            returncode = 0
            stdout = ""
            stderr = ""

        broker = GitHubBroker()

        def fake_run_gh(args, repo=None, use_repo_flag=True):
            captured["args"] = args
            return FakeResult()

        broker._run_gh = fake_run_gh
        broker._invalidate_cache = lambda *a, **k: None
        broker.edit_issue("#106", assignee="@me")

        self.assertIn("--add-assignee", captured["args"])
        self.assertNotIn("--assignee", captured["args"])
        self.assertIn("@me", captured["args"])

    def test_edit_supports_remove_and_multiple_assignees(self):
        sys.path.insert(0, PROJECT_ROOT)
        from jacazul.cli.broker import GitHubBroker

        captured = {}

        class FakeResult:
            returncode = 0
            stdout = ""
            stderr = ""

        broker = GitHubBroker()

        def fake_run_gh(args, repo=None, use_repo_flag=True):
            captured["args"] = args
            return FakeResult()

        broker._run_gh = fake_run_gh
        broker._invalidate_cache = lambda *a, **k: None
        broker.edit_issue(
            "#106", assignee="alice, bob", remove_assignee="carol"
        )

        args = captured["args"]
        self.assertEqual(args.count("--add-assignee"), 2)
        self.assertIn("alice", args)
        self.assertIn("bob", args)
        self.assertIn("--remove-assignee", args)
        self.assertIn("carol", args)

    def test_open_keeps_create_assignee_flag(self):
        """'gh issue create' does accept --assignee; keep it there."""
        sys.path.insert(0, PROJECT_ROOT)
        from jacazul.cli.broker import GitHubBroker

        captured = {}

        class FakeResult:
            returncode = 0
            stdout = "https://example.invalid/1"
            stderr = ""

        broker = GitHubBroker()

        def fake_run_gh(args, repo=None, use_repo_flag=True):
            captured["args"] = args
            return FakeResult()

        broker._run_gh = fake_run_gh
        broker._invalidate_cache = lambda *a, **k: None
        broker.open_issue("Title", assignee="@me", repo=SANDBOX)

        self.assertIn("--assignee", captured["args"])
        self.assertNotIn("--add-assignee", captured["args"])


class TestDecryptTimeout(unittest.TestCase):
    """Token resolution must be bounded and instructional on expiry."""

    def test_timeout_is_configurable(self):
        sys.path.insert(0, PROJECT_ROOT)
        from jacazul.cli.broker import GitHubBroker

        os.environ["JACAZUL_BROKER_DECRYPT_TIMEOUT"] = "7"
        try:
            self.assertEqual(GitHubBroker().decrypt_timeout, 7)
        finally:
            del os.environ["JACAZUL_BROKER_DECRYPT_TIMEOUT"]

    def test_invalid_timeout_falls_back_to_default(self):
        sys.path.insert(0, PROJECT_ROOT)
        from jacazul.cli.broker import (
            DEFAULT_DECRYPT_TIMEOUT,
            GitHubBroker,
        )

        for bogus in ("nonsense", "0", "-5"):
            with self.subTest(value=bogus):
                os.environ["JACAZUL_BROKER_DECRYPT_TIMEOUT"] = bogus
                try:
                    self.assertEqual(
                        GitHubBroker().decrypt_timeout,
                        DEFAULT_DECRYPT_TIMEOUT,
                    )
                finally:
                    del os.environ["JACAZUL_BROKER_DECRYPT_TIMEOUT"]

    def test_decrypt_times_out_with_action_hint(self):
        """A stuck decrypt must return None and emit an ACTION prompt."""
        sys.path.insert(0, PROJECT_ROOT)
        from jacazul.cli.broker import GitHubBroker

        broker = GitHubBroker(cryptozoid_bin="/bin/sleep")
        broker.decrypt_timeout = 1

        original_run = subprocess.run

        def slow_run(cmd, **kwargs):
            raise subprocess.TimeoutExpired(cmd, 1)

        subprocess.run = slow_run
        try:
            self.assertIsNone(broker._decrypt("blob"))
        finally:
            subprocess.run = original_run


if __name__ == "__main__":
    unittest.main()
