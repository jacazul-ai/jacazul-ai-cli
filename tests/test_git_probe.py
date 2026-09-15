import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from jacazul.gitexpert.probe import census, detect

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]

GIT_ENV = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_TERMINAL_PROMPT": "0",
}


def _env():
    env = os.environ.copy()
    env.update(GIT_ENV)
    return env


def git(cwd, *args, stdin=None):
    result = subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
        input=stdin,
        env=_env(),
    )
    return result.stdout.strip()


def make_repo(root, name="repo"):
    path = pathlib.Path(root, name)
    subprocess.run(
        ["git", "init", "-q", "-b", "main", str(path)],
        check=True,
        env=_env(),
    )
    _identity(path)
    return path


def _identity(path):
    git(path, "config", "user.name", "Probe Test")
    git(path, "config", "user.email", "probe@example.invalid")
    git(path, "config", "commit.gpgsign", "false")


def commit(repo, message, filename="file.txt"):
    path = pathlib.Path(repo, filename)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(message.splitlines()[0] + "\n")
    git(repo, "add", "--", filename)
    git(repo, "commit", "-q", "-F", "-", stdin=message)
    return git(repo, "rev-parse", "HEAD")


def linear_history(repo, count=10):
    for index in range(count):
        commit(repo, f"feat: step {index}")


class GitProbeCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="jacazul_gitprobe_")
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name).resolve()
        env = dict(GIT_ENV, GIT_CEILING_DIRECTORIES=str(self.root))
        patcher = mock.patch.dict(os.environ, env)
        patcher.start()
        self.addCleanup(patcher.stop)


class TestGitMode(GitProbeCase):
    def test_linear_history_scans_as_linear(self):
        repo = make_repo(self.root)
        linear_history(repo)

        report = detect(repo)

        self.assertEqual(report.mode, "linear")
        self.assertEqual(report.source, "scan")
        self.assertEqual(report.reference, "main")
        self.assertEqual(report.layout, "plain")

    def test_short_history_is_unknown(self):
        repo = make_repo(self.root)
        linear_history(repo, count=3)

        report = detect(repo)

        self.assertEqual(report.mode, "unknown")

    def test_merge_commits_on_reference_scan_as_merge(self):
        repo = make_repo(self.root)
        linear_history(repo)
        git(repo, "switch", "-q", "-c", "topic")
        commit(repo, "feat: topic work")
        git(repo, "switch", "-q", "main")
        git(repo, "merge", "-q", "--no-ff", "-m", "Merge topic", "topic")

        report = detect(repo)

        self.assertEqual(report.mode, "merge")
        self.assertEqual(report.source, "scan")

    def test_gitflow_config_means_merge(self):
        repo = make_repo(self.root)
        linear_history(repo)
        git(repo, "config", "gitflow.branch.master", "main")

        report = detect(repo)

        self.assertEqual(report.mode, "merge")
        self.assertTrue(any("gitflow" in e for e in report.evidence))

    def test_config_pin_beats_scan(self):
        repo = make_repo(self.root)
        linear_history(repo)
        git(repo, "config", "gitflow.branch.master", "main")
        git(repo, "config", "git-expert.integration", "linear")

        report = detect(repo)

        self.assertEqual(report.mode, "linear")
        self.assertEqual(report.source, "config")

    def test_project_pin_beats_config(self):
        repo = make_repo(self.root)
        linear_history(repo)
        pathlib.Path(repo, "AGENTS.md").write_text(
            "# Agents\n\n"
            "## Git Workflow\n\n"
            "- integration: merge\n"
            "- reference: `develop`\n\n"
            "## Other\n\n"
            "- integration: linear\n",
            encoding="utf-8",
        )
        git(repo, "config", "git-expert.integration", "linear")

        report = detect(repo)

        self.assertEqual(report.mode, "merge")
        self.assertEqual(report.source, "project")
        self.assertEqual(report.reference, "develop")
        self.assertEqual(report.reference_source, "project")

    def test_invalid_pin_value_is_ignored(self):
        repo = make_repo(self.root)
        linear_history(repo)
        git(repo, "config", "git-expert.integration", "yolo")

        report = detect(repo)

        self.assertEqual(report.source, "scan")
        self.assertTrue(any("yolo" in e for e in report.evidence))

    def test_linked_worktree_layout_warns_about_shared_stash(self):
        repo = make_repo(self.root)
        linear_history(repo)
        worktree = self.root / "topic"
        git(repo, "worktree", "add", "-q", "-b", "topic", str(worktree))

        from_main = detect(repo)
        from_topic = detect(worktree)

        self.assertEqual(from_main.layout, "worktrees")
        self.assertEqual(from_topic.layout, "worktrees")
        self.assertEqual(from_topic.branch, "topic")
        self.assertTrue(any("stash" in e for e in from_topic.evidence))

    def test_bare_layout_reports_missing_fetch_refspec(self):
        origin = make_repo(self.root, "origin")
        linear_history(origin, count=2)
        project = self.root / "project"
        project.mkdir()
        subprocess.run(
            ["git", "clone", "-q", "--bare", str(origin), "project/.bare"],
            cwd=self.root,
            check=True,
            env=_env(),
        )
        (project / ".git").write_text("gitdir: ./.bare\n", encoding="utf-8")
        git(project / ".bare", "worktree", "add", "-q", "../main", "main")

        report = detect(project / "main")

        self.assertEqual(report.layout, "bare")
        self.assertTrue(
            any("remote.origin.fetch" in e for e in report.evidence)
        )

    def test_reference_from_origin_head_and_upstream_counts(self):
        origin = make_repo(self.root, "origin")
        linear_history(origin, count=3)
        subprocess.run(
            ["git", "clone", "-q", str(origin), "clone"],
            cwd=self.root,
            check=True,
            env=_env(),
        )
        clone = self.root / "clone"
        _identity(clone)
        commit(clone, "feat: local only")

        report = detect(clone)

        self.assertEqual(report.reference, "main")
        self.assertEqual(report.reference_source, "origin/HEAD")
        self.assertEqual(report.upstream, "origin/main")
        self.assertEqual((report.ahead, report.behind), (1, 0))

    def test_convention_share_counts_recent_titles(self):
        repo = make_repo(self.root)
        commit(repo, "feat: one")
        commit(repo, "Update things")
        commit(repo, "fix(core): two")

        report = detect(repo)

        self.assertEqual((report.conventional, report.recent), (2, 3))

    def test_not_a_repository_returns_none(self):
        empty = self.root / "empty"
        empty.mkdir()

        self.assertIsNone(detect(empty))


class TestGitCensus(GitProbeCase):
    def setUp(self):
        super().setUp()
        self.repo = make_repo(self.root)
        self.base = commit(self.repo, "chore: base")

    def _row(self, rows, needle):
        matches = [r for r in rows if needle in r.label]
        self.assertTrue(matches, needle)
        return matches[0]

    def test_counts_message_and_history_families(self):
        long_line = "x" * 80
        messages = (
            "feat: this title is definitely longer than fifty characters",
            "Update stuff",
            "fix: title\nsecond line without a blank line",
            "docs: wrap\n\n"
            f"{long_line}\n"
            f"see https://example.com/{long_line}\n"
            f"    {long_line}\n",
            "fix: collapsed\\n\\nbody",
            "fix: footer\n\nBody.\n\nRefs: #12\n\nTrailing paragraph.\n",
            "fix: uuid footer\n\nBody.\n\n"
            "Refs: 9d0edacf-6df4-47d6-a5da-abef0fa5e834\n",
            "fix: short hex\n\nBody.\n\nRefs: 9d0edacf\n",
            f"fix: real hash\n\nBody.\n\nRefs: {self.base[:8]}\n",
            "fixup! chore: base",
            "feat: ai\n\nBody.\n\n"
            "Co-authored-by: Claude <noreply@anthropic.com>\n",
            "fix: signed\n\nBody.\n\n"
            "Signed-off-by: A <a@example.invalid>\nRefs: #7\n",
        )
        for message in messages:
            commit(self.repo, message)

        rows = census(self.repo, f"{self.base}..HEAD", mode="linear")

        self.assertEqual(self._row(rows, "AI attribution").kind, "security")
        self.assertEqual(self._row(rows, "AI attribution").count, 1)
        self.assertEqual(self._row(rows, "title over 50").count, 1)
        self.assertEqual(self._row(rows, "Conventional Commits").count, 1)
        self.assertEqual(self._row(rows, "blank line").count, 1)
        self.assertEqual(self._row(rows, "body line over 72").count, 1)
        self.assertEqual(self._row(rows, "literal").count, 1)
        self.assertEqual(self._row(rows, "footer not the last").count, 1)
        self.assertEqual(self._row(rows, "internal workflow ID").count, 2)
        self.assertEqual(self._row(rows, "leftover").kind, "history")
        self.assertEqual(self._row(rows, "leftover").count, 1)
        self.assertEqual(self._row(rows, "merge commit").count, 0)

    def test_merge_commit_counts_only_under_linear_mode(self):
        git(self.repo, "switch", "-q", "-c", "topic")
        commit(self.repo, "feat: topic")
        git(self.repo, "switch", "-q", "main")
        commit(self.repo, "feat: main moved", filename="other.txt")
        git(self.repo, "merge", "-q", "--no-ff", "-m", "Merge topic", "topic")
        rng = f"{self.base}..HEAD"

        linear = census(self.repo, rng, mode="linear")
        merge = census(self.repo, rng, mode="merge")

        self.assertEqual(self._row(linear, "merge commit").count, 1)
        self.assertEqual(self._row(merge, "merge commit").count, 0)
        self.assertEqual(self._row(linear, "Conventional Commits").count, 0)

    def test_clean_series_has_zero_hits(self):
        commit(self.repo, "feat(core): add the thing\n\nWhy it matters.\n")
        commit(
            self.repo,
            "fix: handle the edge\n\nExplain the edge.\n\nRefs: #42\n",
        )

        rows = census(self.repo, f"{self.base}..HEAD", mode="linear")

        self.assertEqual(sum(r.count for r in rows), 0)


class TestGitCli(GitProbeCase):
    def setUp(self):
        super().setUp()
        self.env = _env()
        self.env["PYTHONPATH"] = str(PROJECT_ROOT)
        self.env["GIT_CEILING_DIRECTORIES"] = str(self.root)

    def _run(self, module, *args):
        return subprocess.run(
            [sys.executable, "-m", module, *args],
            env=self.env,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def test_git_mode_prints_mode_and_layout(self):
        repo = make_repo(self.root)
        linear_history(repo)

        result = self._run("jacazul.cli.gitmode", str(repo))

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("GIT_MODE: linear", result.stdout)
        self.assertIn("layout: plain", result.stdout)

    def test_git_mode_outside_repository_exits_with_action(self):
        empty = self.root / "empty"
        empty.mkdir()

        result = self._run("jacazul.cli.gitmode", str(empty))

        self.assertEqual(result.returncode, 2)
        self.assertIn("ACTION", result.stderr)

    def test_git_census_requires_explicit_path(self):
        result = self._run("jacazul.cli.gitcensus")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("explicit path", result.stderr.lower())

    def test_git_census_defaults_to_reference_range_on_topic(self):
        repo = make_repo(self.root)
        linear_history(repo)
        git(repo, "switch", "-q", "-c", "topic")
        commit(repo, "Bad title here")

        result = self._run("jacazul.cli.gitcensus", str(repo))

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("main..HEAD", result.stdout)
        self.assertIn("Conventional Commits", result.stdout)

    def test_git_census_on_reference_without_upstream_asks_for_range(self):
        repo = make_repo(self.root)
        linear_history(repo)

        result = self._run("jacazul.cli.gitcensus", str(repo))

        self.assertEqual(result.returncode, 2)
        self.assertIn("--range", result.stderr)

    def test_git_census_json(self):
        repo = make_repo(self.root)
        base = commit(repo, "chore: base")
        commit(repo, "Update stuff")

        result = self._run(
            "jacazul.cli.gitcensus",
            "--json",
            "--range",
            f"{base}..HEAD",
            str(repo),
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["range"], f"{base}..HEAD")
        self.assertEqual(data["total"], 1)
        self.assertIn("rows", data)


if __name__ == "__main__":
    unittest.main()
