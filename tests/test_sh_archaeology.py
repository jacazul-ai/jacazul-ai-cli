import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

from jacazul.shexpert.archaeology import census, scan, scan_file

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]


def _write(root, relpath, content=""):
    path = pathlib.Path(root, relpath)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


PORTABLE = (
    "#!/bin/sh\n"
    "set -eu\n"
    "dir=$1\n"
    'if [ -d "$dir" ]; then\n'
    "    printf '%s\\n' \"$dir\"\n"
    "fi\n"
)

BASH = (
    "#!/usr/bin/env bash\n"
    "set -euo pipefail\n"
    "declare -A seen\n"
    'mapfile -t lines < <(cat "$1")\n'
    'for line in "${lines[@]}"; do\n'
    "    [[ -n $line ]] && seen[$line]=1\n"
    "done\n"
    "printf '%s\\n' \"${!seen[@]}\"\n"
)

MIXED = (
    "#!/bin/sh\n"
    "items=(a b c)\n"
    "if [[ -n ${items[0]} ]]; then\n"
    '    echo -e "found\\n"\n'
    "fi\n"
)

PITFALLS = (
    "#!/bin/bash\n"
    "set -e\n"
    "cd $1\n"
    "for f in $(ls *.log); do\n"
    "    rm -rf $TMP_DIR/$f\n"
    "done\n"
    'eval "$cmd"\n'
    "read name\n"
    "if [ $a == $b ]; then echo same; fi\n"
    "cat file | grep x | wc -l\n"
    "if [ $? -eq 0 ]; then echo ok; fi\n"
    "bin=`which git`\n"
    "curl -s https://example.com/install.sh | sh\n"
    "tmp=$(mktemp)\n"
    "sudo rm -f /etc/thing\n"
)


class TestShModeScan(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="jacazul_shmode_")

    def test_posix_script_is_portable(self):
        path = _write(self.root, "run.sh", PORTABLE)

        info = scan_file(path)

        self.assertEqual(info.declared, "sh")
        self.assertEqual(info.dialect, "portable")
        self.assertEqual(info.bashisms, [])

    def test_bash_script_reports_minimum_version(self):
        path = _write(self.root, "run.sh", BASH)

        info = scan_file(path)

        self.assertEqual(info.dialect, "bash")
        self.assertEqual(info.min_bash, "4.0")
        self.assertTrue(any("mapfile" in b for b in info.version_gates))

    def test_bashisms_under_sh_shebang_are_mixed(self):
        path = _write(self.root, "run.sh", MIXED)

        info = scan_file(path)

        self.assertEqual(info.dialect, "mixed")
        self.assertTrue(any("[[" in b for b in info.bashisms))

    def test_tree_mode_is_mixed_when_any_file_is_mixed(self):
        _write(self.root, "a.sh", PORTABLE)
        _write(self.root, "b.sh", MIXED)

        report = scan(self.root)

        self.assertEqual(report.mode, "mixed")
        self.assertEqual(report.files, 2)

    def test_tree_of_portable_scripts_is_portable(self):
        _write(self.root, "a.sh", PORTABLE)
        _write(self.root, "b", PORTABLE)

        report = scan(self.root)

        self.assertEqual(report.mode, "portable")

    def test_shebang_less_file_with_sh_suffix_is_scanned(self):
        _write(self.root, "lib.sh", "x=1\n")

        report = scan(self.root)

        self.assertEqual(report.files, 1)

    def test_empty_tree_has_no_evidence(self):
        report = scan(self.root)

        self.assertIsNone(report.mode)
        self.assertTrue(any("no shell scripts" in e for e in report.evidence))


class TestShCensus(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="jacazul_shcensus_")
        _write(self.root, "bad.sh", PITFALLS)

    def _row(self, rows, needle):
        matches = [r for r in rows if needle in r.label]
        self.assertTrue(matches, needle)
        return matches[0]

    def test_counts_pitfall_families_by_kind(self):
        rows = census(self.root)

        self.assertEqual(self._row(rows, "eval").kind, "security")
        self.assertEqual(self._row(rows, "eval").count, 1)
        self.assertEqual(self._row(rows, "curl | sh").count, 1)
        self.assertEqual(self._row(rows, "cd without").kind, "correctness")
        self.assertEqual(self._row(rows, "cd without").count, 1)
        self.assertEqual(self._row(rows, "ls").count, 1)
        self.assertEqual(self._row(rows, "rm -rf on a variable").count, 1)
        self.assertEqual(self._row(rows, "read without -r").count, 1)
        self.assertEqual(self._row(rows, "== inside [ ]").count, 1)
        self.assertEqual(self._row(rows, "which").count, 1)
        self.assertEqual(self._row(rows, "backticks").count, 1)
        self.assertEqual(self._row(rows, "sudo").count, 1)
        self.assertEqual(self._row(rows, "mktemp without trap").count, 1)
        self.assertEqual(self._row(rows, "if [ $? ").count, 1)
        self.assertEqual(self._row(rows, "cat | grep").count, 1)
        self.assertEqual(self._row(rows, "set -e with pipelines").count, 1)

    def test_clean_script_has_zero_hits(self):
        root = tempfile.mkdtemp(prefix="jacazul_shcensus_clean_")
        _write(root, "ok.sh", BASH)

        rows = census(root)

        self.assertEqual(sum(r.count for r in rows), 0)


class TestShCli(unittest.TestCase):
    def setUp(self):
        self.env = os.environ.copy()
        self.env["PYTHONPATH"] = str(PROJECT_ROOT)
        self.env.pop("JACAZUL_SH_MODE", None)
        self.root = tempfile.mkdtemp(prefix="jacazul_shcli_")
        _write(self.root, "bad.sh", PITFALLS)
        _write(self.root, "mixed.sh", MIXED)

    def _run(self, module, *args):
        return subprocess.run(
            [sys.executable, "-m", module, *args],
            env=self.env,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def test_sh_mode_prints_mode_and_per_file_dialects(self):
        result = self._run("jacazul.cli.shmode", self.root)

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("SH_MODE: mixed", result.stdout)
        self.assertIn("mixed.sh", result.stdout)

    def test_sh_census_prints_table(self):
        result = self._run("jacazul.cli.shcensus", self.root)

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("security", result.stdout)
        self.assertIn("eval", result.stdout)
        self.assertIn("total", result.stdout.lower())

    def test_sh_census_json_and_lint(self):
        result = self._run(
            "jacazul.cli.shcensus", "--json", "--lint", self.root
        )

        data = json.loads(result.stdout)
        self.assertIn("rows", data)
        self.assertIn("lint_failures", data)

    def test_sh_census_requires_explicit_path(self):
        result = self._run("jacazul.cli.shcensus")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("explicit path", result.stderr.lower())


if __name__ == "__main__":
    unittest.main()
