import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

from jacazul.phpexpert.archaeology import census, resolve_mode, scan

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]


def _write(root, relpath, content=""):
    path = pathlib.Path(root, relpath)
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, dict):
        content = json.dumps(content)
    path.write_text(content, encoding="utf-8")
    return path


LEGACY = (
    "<?php\n"
    "class db {\n"
    "    var $link;\n"
    "    function db() {\n"
    "        $this->link = mysql_connect('h', 'u', 'p');\n"
    "    }\n"
    "}\n"
    "while (list($k, $v) = each($rows)) { echo $k; }\n"
    "if (ereg('^a', $s)) { $t = split(',', $s); }\n"
    "$f = create_function('$a', 'return $a;');\n"
    "echo strftime('%Y');\n"
    'echo "${name}";\n'
)

MODERN = (
    "<?php\n"
    "declare(strict_types=1);\n\n"
    "namespace App;\n\n"
    "use App\\Repo;\n\n"
    "enum Status: string { case Open = 'open'; }\n\n"
    "final class Service {\n"
    "    public function __construct(private readonly Repo $repo) {}\n"
    "    public function run(?int $id): string {\n"
    "        return match ($id) { null => 'none', default => 'some' };\n"
    "    }\n"
    "}\n"
)


class TestPhpModeScan(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="jacazul_phpmode_")

    def test_removed_constructs_classify_as_legacy(self):
        _write(self.root, "db.php", LEGACY)

        report = scan(self.root)

        self.assertEqual(report.mode, "legacy")
        self.assertTrue(any("mysql_" in e for e in report.evidence))

    def test_modern_tree_with_php8_floor_is_greenfield(self):
        _write(
            self.root,
            "composer.json",
            {
                "require": {"php": ">=8.2"},
                "autoload": {"psr-4": {"App\\": "src/"}},
            },
        )
        _write(self.root, "src/Service.php", MODERN)

        report = scan(self.root)

        self.assertEqual(report.mode, "greenfield")
        self.assertEqual(report.floor, "8.2")

    def test_mixed_markers_are_migration(self):
        _write(self.root, "composer.json", {"require": {"php": ">=5.6"}})
        _write(self.root, "legacy/db.php", LEGACY)
        _write(self.root, "src/Service.php", MODERN)

        report = scan(self.root)

        self.assertEqual(report.mode, "migration")

    def test_modern_syntax_above_declared_floor_is_flagged(self):
        _write(self.root, "composer.json", {"require": {"php": ">=5.6"}})
        _write(
            self.root,
            "a.php",
            "<?php\n$x = $a ?? 'b';\n$f = fn($v) => $v;\n",
        )

        report = scan(self.root)

        self.assertTrue(report.above_floor)
        self.assertTrue(
            any("above declared floor" in e for e in report.evidence)
        )

    def test_wordpress_is_evidence_only(self):
        _write(self.root, "wp-config.php", "<?php\ndefine('DB_NAME', 'x');\n")
        _write(
            self.root,
            "wp-content/plugins/p/p.php",
            "<?php\nadd_action('init', 'f');\n",
        )

        report = scan(self.root)

        self.assertTrue(any("WordPress" in e for e in report.evidence))

    def test_empty_tree_is_greenfield_with_warning(self):
        report = scan(self.root)

        self.assertEqual(report.mode, "greenfield")
        self.assertTrue(any("no evidence" in e for e in report.evidence))

    def test_env_override_wins(self):
        mode, source = resolve_mode(
            self.root, env={"JACAZUL_PHP_MODE": "legacy"}
        )

        self.assertEqual((mode, source), ("legacy", "env"))

    def test_composer_extra_override(self):
        _write(
            self.root,
            "composer.json",
            {"extra": {"jacazul": {"mode": "migration"}}},
        )

        mode, source = resolve_mode(self.root, env={})

        self.assertEqual((mode, source), ("migration", "composer.json"))


class TestPhpCensus(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="jacazul_phpcensus_")
        _write(self.root, "db.php", LEGACY)

    def test_counts_are_grouped_by_breaking_version(self):
        rows = census(self.root)

        by_version = {
            (r.breaks, r.kind): r
            for r in rows
            if r.label == "mysql_* extension"
        }
        self.assertIn(("7.0", "removed"), by_version)
        self.assertEqual(by_version[("7.0", "removed")].count, 1)
        each = [r for r in rows if r.label.startswith("each()")][0]
        self.assertEqual(
            (each.breaks, each.kind, each.count), ("8.0", "removed", 1)
        )
        php4 = [r for r in rows if "PHP 4 constructor" in r.label][0]
        self.assertEqual(php4.count, 1)

    def test_floor_filter_reports_only_constructs_above_it(self):
        _write(
            self.root,
            "new.php",
            "<?php\n$x = $a ?? 1;\n$m = match ($x) { default => 1 };\n",
        )

        rows = census(self.root, floor="5.6")

        labels = {r.label for r in rows if r.count}
        self.assertTrue(any("??" in label for label in labels))
        self.assertTrue(any("match" in label for label in labels))
        self.assertFalse(any("mysql_" in label for label in labels))


class TestPhpCli(unittest.TestCase):
    def setUp(self):
        self.env = os.environ.copy()
        self.env["PYTHONPATH"] = str(PROJECT_ROOT)
        self.env.pop("JACAZUL_PHP_MODE", None)
        self.root = tempfile.mkdtemp(prefix="jacazul_phpcli_")
        _write(self.root, "db.php", LEGACY)

    def _run(self, module, *args):
        return subprocess.run(
            [sys.executable, "-m", module, *args],
            env=self.env,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def test_php_mode_prints_mode(self):
        result = self._run("jacazul.cli.phpmode", self.root)

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("PHP_MODE: legacy", result.stdout)

    def test_php_census_prints_table_and_totals(self):
        result = self._run("jacazul.cli.phpcensus", self.root)

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("7.0", result.stdout)
        self.assertIn("mysql_", result.stdout)
        self.assertIn("total", result.stdout.lower())

    def test_php_census_json(self):
        result = self._run("jacazul.cli.phpcensus", "--json", self.root)

        data = json.loads(result.stdout)
        self.assertTrue(
            any(r["label"].startswith("each()") for r in data["rows"])
        )

    def test_php_census_requires_explicit_path(self):
        result = self._run("jacazul.cli.phpcensus")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("explicit path", result.stderr.lower())


if __name__ == "__main__":
    unittest.main()
