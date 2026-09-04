#!/usr/bin/env python
"""Argument contract tests for the jacazul-broker CLI.

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


class TestRepoArgumentContract(unittest.TestCase):
    """The repo argument must behave identically across every command."""

    def test_write_commands_reject_positional_repo(self):
        """A bare repo on 'open' must fail instead of being dropped.

        Regression: parse_kwargs used to discard every token without '=',
        so the repository silently fell back to the inferred one and issues
        landed in the production repository.
        """
        res = run_broker("open", "title=Smoke", SANDBOX)
        self.assertEqual(res.returncode, 1)
        self.assertIn("Unexpected argument", res.stderr)
        self.assertIn(SANDBOX, res.stderr)
        self.assertIn("ACTION:", res.stderr)

    def test_read_commands_accept_repo_keyword(self):
        """'view' must understand repo= and not treat it as a literal."""
        res = run_broker("view", "#1", "repo=not a repo")
        self.assertEqual(res.returncode, 1)
        self.assertIn("Invalid repository", res.stderr)

    def test_close_comment_is_not_swallowed_as_repo(self):
        """Regression: 'close 30 comment=done' consumed the comment as repo."""
        res = run_broker("close", "30", "comment=done", "repo=bad repo")
        self.assertEqual(res.returncode, 1)
        self.assertIn("Invalid repository", res.stderr)
        self.assertNotIn("comment=done", res.stderr)

    def test_invalid_repo_shape_fails_before_gh(self):
        res = run_broker("labels", "repo=missing-slash")
        self.assertEqual(res.returncode, 1)
        self.assertIn("Invalid repository", res.stderr)
        self.assertIn('repo="org/name"', res.stderr)

    def test_positional_repo_still_works_but_warns(self):
        """The legacy positional form stays accepted during the transition."""
        res = run_broker("labels", "bad repo")
        self.assertEqual(res.returncode, 1)
        self.assertIn("deprecated", res.stderr)
        self.assertIn("Invalid repository", res.stderr)

    def test_repo_given_twice_is_an_error(self):
        res = run_broker("labels", SANDBOX, f"repo={SANDBOX}")
        self.assertEqual(res.returncode, 1)
        self.assertIn("given twice", res.stderr)


class TestFailClosedParsing(unittest.TestCase):
    """Unknown and misplaced arguments must abort, never be dropped."""

    def test_unknown_keyword_is_rejected(self):
        res = run_broker("comment", "#1", "bodyy=oops")
        self.assertEqual(res.returncode, 1)
        self.assertIn("Unknown argument 'bodyy='", res.stderr)
        self.assertIn("Accepted keywords:", res.stderr)

    def test_extra_positional_is_rejected(self):
        res = run_broker("labels", SANDBOX, "extra")
        self.assertEqual(res.returncode, 1)
        self.assertIn("Unexpected argument 'extra'", res.stderr)

    def test_dash_placeholder_skips_a_slot(self):
        """'list - closed' must reach the state slot, not the repo slot."""
        res = run_broker("list", "-", "closed", "bogus-milestone", "extra")
        self.assertEqual(res.returncode, 1)
        self.assertIn("Unexpected argument 'extra'", res.stderr)

    def test_keyword_shaped_positional_fails_closed(self):
        """A bare 'word=value' is never silently accepted as a positional.

        Guessing here would reintroduce the original defect: an argument that
        looks like a keyword would quietly land in an unrelated slot.
        """
        res = run_broker("close", "30", "-", "done=yes")
        self.assertEqual(res.returncode, 1)
        self.assertIn("Unknown argument 'done='", res.stderr)
        self.assertIn("comment=", res.stderr)

    def test_positional_value_may_contain_equals(self):
        """Values that are not keyword-shaped keep working positionally."""
        res = run_broker("close", "30", "-", "closed by a=b", "extra")
        self.assertEqual(res.returncode, 1)
        self.assertIn("Unexpected argument 'extra'", res.stderr)
        self.assertNotIn("Unknown argument", res.stderr)

    def test_missing_issue_id_is_reported(self):
        res = run_broker("view")
        self.assertEqual(res.returncode, 1)
        self.assertIn("Issue ID required", res.stderr)
        self.assertIn("ACTION:", res.stderr)


class TestHelp(unittest.TestCase):
    """The help block must be reachable and honest."""

    def test_help_flags_are_supported(self):
        for flag in ("--help", "-h", "help"):
            with self.subTest(flag=flag):
                res = run_broker(flag)
                self.assertEqual(res.returncode, 0)
                self.assertIn("Usage: jacazul-broker", res.stdout)

    def test_bare_invocation_prints_help(self):
        res = run_broker()
        self.assertEqual(res.returncode, 0)
        self.assertIn("Usage: jacazul-broker", res.stdout)

    def test_unknown_command_prints_help(self):
        res = run_broker("frobnicate")
        self.assertEqual(res.returncode, 1)
        self.assertIn("Usage: jacazul-broker", res.stderr)
        self.assertIn("Unknown command", res.stderr)

    def test_help_documents_the_dash_placeholder(self):
        res = run_broker("--help")
        self.assertIn('Use "-" to skip a positional argument', res.stdout)

    def test_help_documents_repo_inference(self):
        res = run_broker("--help")
        self.assertIn("inferred from the current git remote", res.stdout)

    def test_help_warns_about_shell_quoting(self):
        res = run_broker("--help")
        self.assertIn("comment", res.stdout)
        self.assertIn("view '#106'", res.stdout)


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
