import pathlib
import tempfile
import unittest

from jacazul.pyexpert.archaeology import resolve_mode, scan


def _write(root, relpath, content=""):
    path = pathlib.Path(root, relpath)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


class TestArchaeologyScan(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="jacazul_pymode_")

    def test_python2_remnants_classify_as_legacy(self):
        _write(self.root, "setup.py", "from setuptools import setup\n")
        _write(
            self.root,
            "app/__init__.py",
            "from __future__ import print_function\n"
            "import six\n"
            "print 'hello'\n",
        )

        report = scan(self.root)

        self.assertEqual(report.mode, "legacy")
        self.assertTrue(any("six" in item for item in report.evidence))

    def test_modern_packaging_and_typing_classify_as_greenfield(self):
        _write(
            self.root,
            "pyproject.toml",
            '[project]\nname = "x"\nrequires-python = ">=3.13"\n'
            "[tool.ruff]\nline-length = 79\n",
        )
        _write(
            self.root,
            "src/x/__init__.py",
            "from pathlib import Path\n\n\n"
            "def load(path: Path) -> str:\n"
            '    return path.read_text(encoding="utf-8")\n',
        )
        _write(self.root, "tests/conftest.py", "")

        report = scan(self.root)

        self.assertEqual(report.mode, "greenfield")

    def test_mixed_markers_classify_as_migration(self):
        _write(
            self.root,
            "pyproject.toml",
            '[project]\nname = "x"\nrequires-python = ">=3.11"\n',
        )
        _write(
            self.root,
            "x/core.py",
            "import os\n\n\n"
            "def load(path):\n"
            "    return open(os.path.join(path, 'a')).read()\n",
        )

        report = scan(self.root)

        self.assertEqual(report.mode, "migration")

    def test_empty_tree_is_greenfield_with_warning(self):
        report = scan(self.root)

        self.assertEqual(report.mode, "greenfield")
        self.assertTrue(any("no evidence" in item for item in report.evidence))

    def test_old_interpreter_floor_is_legacy(self):
        _write(
            self.root,
            "setup.py",
            "from setuptools import setup\n"
            "setup(name='x', python_requires='>=2.7')\n",
        )
        _write(self.root, "x/__init__.py", "def f():\n    return 1\n")

        report = scan(self.root)

        self.assertEqual(report.mode, "legacy")


class TestModeResolution(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="jacazul_pymode_")

    def test_environment_override_wins(self):
        env = {"JACAZUL_PY_MODE": "legacy"}

        mode, source = resolve_mode(self.root, env=env)

        self.assertEqual((mode, source), ("legacy", "env"))

    def test_pyproject_override_beats_scan(self):
        _write(
            self.root,
            "pyproject.toml",
            '[tool.jacazul]\npy_mode = "migration"\n',
        )

        mode, source = resolve_mode(self.root, env={})

        self.assertEqual((mode, source), ("migration", "pyproject"))

    def test_invalid_override_falls_back_to_scan(self):
        env = {"JACAZUL_PY_MODE": "banana"}

        mode, source = resolve_mode(self.root, env=env)

        self.assertEqual(source, "scan")
        self.assertIn(mode, {"legacy", "greenfield", "migration"})


if __name__ == "__main__":
    unittest.main()
