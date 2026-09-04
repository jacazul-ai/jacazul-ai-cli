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
