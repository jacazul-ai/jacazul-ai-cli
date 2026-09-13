import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

from jacazul.jsexpert.archaeology import resolve_mode, scan
from jacazul.jsexpert.formatting import (
    ignore_formatting,
    resolve_indent,
)

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]


def _write(root, relpath, content=""):
    path = pathlib.Path(root, relpath)
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, dict):
        content = json.dumps(content)
    path.write_text(content, encoding="utf-8")
    return path


class TestJsArchaeologyScan(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="jacazul_jsmode_")

    def test_jquery_grunt_commonjs_tree_is_legacy(self):
        _write(
            self.root,
            "package.json",
            {
                "name": "old",
                "dependencies": {"jquery": "1.12.4"},
                "devDependencies": {"grunt": "0.4.5", "karma": "1.0.0"},
            },
        )
        _write(self.root, "bower.json", "{}")
        _write(
            self.root,
            "src/app.js",
            "var $ = require('jquery');\n"
            "module.exports = function () { return $('#x'); };\n",
        )

        report = scan(self.root)

        self.assertEqual(report.mode, "legacy")
        self.assertTrue(any("bower" in item for item in report.evidence))

    def test_esm_typescript_vite_tree_is_greenfield(self):
        _write(
            self.root,
            "package.json",
            {
                "name": "new",
                "type": "module",
                "packageManager": "pnpm@9.0.0",
                "engines": {"node": ">=20"},
                "devDependencies": {
                    "typescript": "5.9.0",
                    "vite": "6.0.0",
                    "vitest": "2.0.0",
                },
            },
        )
        _write(self.root, "pnpm-lock.yaml", "lockfileVersion: '9.0'\n")
        _write(
            self.root,
            "tsconfig.json",
            {"compilerOptions": {"strict": True, "target": "ES2022"}},
        )
        _write(
            self.root,
            "src/main.ts",
            "import { start } from './start';\n"
            "export const run = () => start();\n",
        )

        report = scan(self.root)

        self.assertEqual(report.mode, "greenfield")

    def test_modern_toolchain_over_legacy_code_is_migration(self):
        _write(
            self.root,
            "package.json",
            {
                "name": "mixed",
                "type": "module",
                "dependencies": {"jquery": "3.7.0"},
                "devDependencies": {"vite": "6.0.0", "typescript": "5.9.0"},
            },
        )
        _write(self.root, "tsconfig.json", {"compilerOptions": {}})
        _write(
            self.root,
            "src/legacy.js",
            "var x = require('./y');\nmodule.exports = x;\n",
        )
        _write(self.root, "src/new.ts", "export const a = 1;\n")

        report = scan(self.root)

        self.assertEqual(report.mode, "migration")

    def test_empty_tree_is_greenfield_with_warning(self):
        report = scan(self.root)

        self.assertEqual(report.mode, "greenfield")
        self.assertTrue(any("no evidence" in item for item in report.evidence))

    def test_env_override_wins(self):
        mode, source = resolve_mode(
            self.root, env={"JACAZUL_JS_TS_MODE": "legacy"}
        )

        self.assertEqual((mode, source), ("legacy", "env"))

    def test_package_json_override_beats_scan(self):
        _write(
            self.root,
            "package.json",
            {"name": "x", "jacazul": {"mode": "migration"}},
        )

        mode, source = resolve_mode(self.root, env={})

        self.assertEqual((mode, source), ("migration", "package.json"))


class TestIndentResolution(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="jacazul_jsfmt_")

    def test_house_default_is_four_spaces(self):
        self.assertEqual(
            resolve_indent(self.root, flag=None, env={}),
            ("space", 4, "default"),
        )

    def test_prettierrc_declares_two_spaces(self):
        _write(self.root, ".prettierrc", {"tabWidth": 2})

        self.assertEqual(
            resolve_indent(self.root, flag=None, env={}),
            ("space", 2, ".prettierrc"),
        )

    def test_editorconfig_declares_tabs(self):
        _write(
            self.root,
            ".editorconfig",
            "root = true\n\n[*.{js,ts}]\nindent_style = tab\n",
        )

        self.assertEqual(
            resolve_indent(self.root, flag=None, env={}),
            ("tab", 4, ".editorconfig"),
        )

    def test_package_json_prettier_key_is_read(self):
        _write(
            self.root,
            "package.json",
            {"name": "x", "prettier": {"tabWidth": 2, "useTabs": False}},
        )

        self.assertEqual(
            resolve_indent(self.root, flag=None, env={}),
            ("space", 2, "package.json"),
        )

    def test_flag_and_env_win(self):
        _write(self.root, ".prettierrc", {"tabWidth": 2})

        self.assertEqual(
            resolve_indent(self.root, flag=8, env={})[:2], ("space", 8)
        )
        self.assertEqual(
            resolve_indent(
                self.root, flag=None, env={"JACAZUL_JS_TS_INDENT": "3"}
            ),
            ("space", 3, "env"),
        )


class TestIgnoreFormattingGuard(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="jacazul_jsfmt_")

    def test_env_guard(self):
        env = {"JACAZUL_JS_TS_IGNORE_FORMATTING": "1"}

        self.assertTrue(ignore_formatting("greenfield", self.root, env=env))

    def test_legacy_without_formatter_config(self):
        self.assertTrue(ignore_formatting("legacy", self.root, env={}))

    def test_legacy_with_prettier_config_formats(self):
        _write(self.root, ".prettierrc", {"tabWidth": 2})

        self.assertFalse(ignore_formatting("legacy", self.root, env={}))


class TestJsCheckPlan(unittest.TestCase):
    """js-check --dry-run prints the command plan; no Node required."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="jacazul_jscheck_")
        self.env = os.environ.copy()
        self.env["PYTHONPATH"] = str(PROJECT_ROOT)
        for key in ("JACAZUL_JS_TS_MODE", "JACAZUL_JS_TS_IGNORE_FORMATTING"):
            self.env.pop(key, None)

    def _run(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "jacazul.cli.jscheck", *args],
            env=self.env,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def test_no_path_is_an_error_as_prompt(self):
        result = self._run()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("explicit path", result.stderr.lower())

    def test_plan_uses_pnpm_and_tsc_when_declared(self):
        _write(
            self.root,
            "package.json",
            {
                "name": "x",
                "type": "module",
                "devDependencies": {
                    "typescript": "5.9.0",
                    "prettier": "3.0.0",
                },
            },
        )
        _write(self.root, "pnpm-lock.yaml", "lockfileVersion: '9.0'\n")
        _write(
            self.root, "tsconfig.json", {"compilerOptions": {"strict": True}}
        )
        _write(self.root, ".prettierrc", {"tabWidth": 2})
        _write(self.root, "src/a.ts", "export const a = 1;\n")

        result = self._run("--dry-run", self.root)

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("pnpm exec tsc --noEmit", result.stdout)
        self.assertIn("pnpm exec prettier --write", result.stdout)

    def test_check_mode_never_plans_writes(self):
        _write(
            self.root,
            "package.json",
            {"name": "x", "devDependencies": {"prettier": "3.0.0"}},
        )
        _write(self.root, ".prettierrc", {"tabWidth": 2})

        result = self._run("--dry-run", "--check", self.root)

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("prettier --check", result.stdout)
        self.assertNotIn("--write", result.stdout)
        self.assertNotIn("--fix", result.stdout)

    def test_legacy_tree_without_formatter_is_check_only(self):
        _write(
            self.root,
            "package.json",
            {"name": "old", "dependencies": {"jquery": "1.12.4"}},
        )
        _write(self.root, "bower.json", "{}")
        _write(self.root, "src/app.js", "var a = require('b');\n")

        result = self._run("--dry-run", self.root)

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("check-only", result.stdout.lower())
        self.assertNotIn("--write", result.stdout)


class TestJsModeCli(unittest.TestCase):
    def test_prints_mode_and_evidence(self):
        root = tempfile.mkdtemp(prefix="jacazul_jsmode_cli_")
        _write(root, "bower.json", "{}")
        _write(root, "src/a.js", "var $ = require('jquery');\n")
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PROJECT_ROOT)
        env.pop("JACAZUL_JS_TS_MODE", None)

        result = subprocess.run(
            [sys.executable, "-m", "jacazul.cli.jsmode", root],
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("JS_TS_MODE: legacy", result.stdout)


if __name__ == "__main__":
    unittest.main()
